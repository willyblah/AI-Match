#!/usr/bin/env python3
"""Kling Motion Control 3.0 gateway CLI. Reads INTEGRATIONS_API_KEY."""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

CREATE = "https://app-dvtmyuucfs3l-api-n9QVBZkleO2L-gateway.appmiaoda.com/motion-control/kling-3.0"
TASKS = "https://app-dvtmyuucfs3l-api-Aa2P8o0BV1RL-gateway.appmiaoda.com/tasks"

class ApiError(RuntimeError): pass

def emit(value): print(json.dumps(value, ensure_ascii=False, indent=2))
def key():
    value = os.environ.get("INTEGRATIONS_API_KEY", "").strip()
    if not value: raise ApiError("缺少环境变量 INTEGRATIONS_API_KEY")
    return value.removeprefix("Bearer ").strip()

def request(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "X-Gateway-Authorization": f"Bearer {key()}", "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", "replace")
            payload = json.loads(raw)
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try: payload = json.loads(raw)
        except json.JSONDecodeError: payload = {"message": raw[:500]}
        raise ApiError(f"HTTP {exc.code}: {payload.get('message', '请求失败')}") from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"网络请求失败: {exc.reason}") from exc
    if status < 200 or status >= 300 or payload.get("code") != 0:
        raise ApiError(f"API {payload.get('code', status)}: {payload.get('message', '请求失败')}")
    return payload

def create(args):
    if len(args.prompt or "") > 2500: raise ApiError("prompt 不能超过 2500 字符")
    if args.element_id and args.character_orientation != "video":
        raise ApiError("引用主体时 character_orientation 必须为 video")
    contents = []
    if args.prompt: contents.append({"type":"prompt", "text":args.prompt})
    contents += [{"type":"image", "url":args.image_url}, {"type":"video", "url":args.video_url}]
    if args.element_id:
        contents.append({"type":"element", "element_id":args.element_id, "id":args.element_index})
    options = {"watermark_info":{"enabled":args.watermark}}
    if args.callback_url: options["callback_url"] = args.callback_url
    if args.external_task_id: options["external_task_id"] = args.external_task_id
    payload = request("POST", CREATE, {"contents":contents,"settings":{
        "character_orientation":args.character_orientation,"audio":args.audio,"resolution":args.resolution
    },"options":options})
    data = payload.get("data") or {}
    emit({"task_id":str(data.get("id", "")),"external_task_id":data.get("external_id"),
          "status":data.get("status"),"request_id":payload.get("request_id")})

def query_payload(task_ids=None, external_ids=None):
    if bool(task_ids) == bool(external_ids): raise ApiError("task_ids 与 external_task_ids 必须二选一")
    params = {"task_ids":task_ids} if task_ids else {"external_task_ids":external_ids}
    return request("GET", TASKS + "?" + urllib.parse.urlencode(params))

def query(args): emit(query_payload(args.task_ids, args.external_task_ids))

def download(url, destination):
    path=Path(destination).expanduser().resolve(); path.parent.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as src, path.open("wb") as dst:
        while chunk:=src.read(1024*1024): dst.write(chunk)
    return str(path)

def wait(args):
    deadline=time.time()+args.timeout
    while time.time()<deadline:
        payload=query_payload(args.task_id, None)
        tasks=payload.get("data") if isinstance(payload.get("data"),list) else []
        task=next((x for x in tasks if str(x.get("id"))==str(args.task_id)),None)
        if not task: raise ApiError("查询响应中未找到目标任务")
        status=task.get("status")
        if status=="failed": raise ApiError(task.get("message") or "任务失败")
        if status=="succeeded":
            videos=[x for x in task.get("outputs",[]) if x.get("type")=="video" and x.get("url")]
            result={"task_id":str(task.get("id")),"status":status,"videos":videos}
            if args.download:
                if not videos: raise ApiError("任务成功但没有视频输出")
                result["downloaded_to"]=download(videos[0]["url"],args.download)
            emit(result); return
        time.sleep(args.interval)
    raise ApiError(f"任务等待超过 {args.timeout} 秒")

def parser():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest="command",required=True)
    c=sub.add_parser("create"); c.add_argument("--image-url",required=True); c.add_argument("--video-url",required=True)
    c.add_argument("--prompt"); c.add_argument("--character-orientation",choices=["image","video"],required=True)
    c.add_argument("--audio",choices=["original","off"],default="original"); c.add_argument("--resolution",choices=["720p","1080p"],default="720p")
    c.add_argument("--element-id"); c.add_argument("--element-index",default="element_1"); c.add_argument("--callback-url")
    c.add_argument("--external-task-id"); c.add_argument("--watermark",action="store_true"); c.set_defaults(func=create)
    q=sub.add_parser("query"); g=q.add_mutually_exclusive_group(required=True); g.add_argument("--task-ids"); g.add_argument("--external-task-ids"); q.set_defaults(func=query)
    w=sub.add_parser("wait"); w.add_argument("--task-id",required=True); w.add_argument("--interval",type=float,default=7); w.add_argument("--timeout",type=int,default=600); w.add_argument("--download"); w.set_defaults(func=wait)
    return p

def main():
    try: args=parser().parse_args(); args.func(args)
    except ApiError as exc: emit({"error":str(exc)}); return 2
    return 0
if __name__=="__main__": sys.exit(main())
