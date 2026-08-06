# 应用内完整生成闭环（必须实现）

本文件是秒哒生成应用时的强制实现合同。动作控制是异步媒体生成能力，**创建接口返回任务 ID 不代表用户任务完成**。应用不得在只拿到 `task_id` 后显示“生成成功”；必须继续查询，直到取得视频 URL，完成预览与下载能力。

## 强制完成定义

一次“生成”操作只有满足以下全部条件才算成功：

1. 创建接口返回 `data.id`；
2. 应用自动按该 ID 轮询查询接口；
3. 查询状态达到 `succeeded`；
4. 从精确匹配的任务中读取 `outputs[type=video].url`；
5. 页面渲染可播放的 `<video controls>` 预览；
6. 页面提供“下载视频”按钮；
7. 应用保存任务与输出 URL，刷新页面后仍可恢复结果；
8. 推荐在服务端将30天临时URL转存至 Supabase Storage，并优先预览、下载持久化URL。

仅展示“生成成功 + 任务ID”属于未完成实现。

## Edge Function：查询、精确匹配并转存

```typescript
// supabase/functions/kling-motion-control-query/index.ts
import { serve } from "https://deno.land/std/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const QUERY_ENDPOINT =
  "https://app-dvtmyuucfs3l-api-Aa2P8o0BV1RL-gateway.appmiaoda.com/tasks";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

async function transferVideo(taskId: string, output: {
  id?: string; url: string; duration?: string; watermark_url?: string;
}) {
  const response = await fetch(output.url);
  if (!response.ok || !response.body) {
    throw new Error(`视频下载失败：${response.status}`);
  }
  const contentType = response.headers.get("content-type") || "video/mp4";
  if (!contentType.startsWith("video/") && contentType !== "application/octet-stream") {
    throw new Error(`视频类型异常：${contentType}`);
  }
  const outputId = output.id || crypto.randomUUID();
  const path = `kling-motion-control/${taskId}/${outputId}.mp4`;
  const { error } = await supabase.storage.from("generated-media").upload(
    path,
    response.body,
    { contentType, upsert: true, cacheControl: "31536000" },
  );
  if (error) throw error;
  return supabase.storage.from("generated-media").getPublicUrl(path).data.publicUrl;
}

serve(async (req) => {
  if (req.method !== "POST") {
    return Response.json({ error: "Method Not Allowed" }, { status: 405 });
  }
  try {
    const body = await req.json();
    const taskId = String(body.task_id || "").trim();
    const externalTaskId = String(body.external_task_id || "").trim();
    if (Boolean(taskId) === Boolean(externalTaskId)) {
      return Response.json(
        { error: "task_id 与 external_task_id 必须二选一" },
        { status: 400 },
      );
    }

    const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
    if (!apiKey) return Response.json({ error: "视频服务配置缺失" }, { status: 500 });
    const auth = apiKey.startsWith("Bearer ") ? apiKey : `Bearer ${apiKey}`;
    const query = taskId
      ? `task_ids=${encodeURIComponent(taskId)}`
      : `external_task_ids=${encodeURIComponent(externalTaskId)}`;

    const upstream = await fetch(`${QUERY_ENDPOINT}?${query}`, {
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": auth,
      },
    });
    const json = await upstream.json().catch(() => ({}));
    if (!upstream.ok || json.code !== 0) {
      return Response.json({
        error: json.message || "查询视频任务失败",
        code: json.code,
        request_id: json.request_id,
      }, { status: upstream.status || 502 });
    }

    const tasks = Array.isArray(json.data) ? json.data : [];
    const task = tasks.find((item: { id?: string; external_id?: string }) =>
      taskId ? String(item.id) === taskId : item.external_id === externalTaskId
    );
    if (!task) return Response.json({ error: "查询响应中未找到目标任务" }, { status: 502 });

    if (task.status === "failed") {
      return Response.json({
        status: "failed",
        task_id: String(task.id),
        message: task.message || "视频生成失败",
      });
    }
    if (task.status !== "succeeded") {
      return Response.json({ status: task.status, task_id: String(task.id) });
    }

    const outputs = (task.outputs || []).filter(
      (item: { type?: string; url?: string }) => item.type === "video" && item.url,
    );
    if (!outputs.length) {
      return Response.json({ error: "任务成功但没有视频输出" }, { status: 502 });
    }

    const videos = await Promise.all(outputs.map(async (output: {
      id?: string; url: string; duration?: string; watermark_url?: string;
    }) => {
      try {
        const persistentUrl = await transferVideo(String(task.id), output);
        return {
          id: output.id,
          url: persistentUrl,
          source_url: output.url,
          duration: output.duration,
          storage_transfer_success: true,
        };
      } catch (error) {
        console.error("[motion-control transfer]", error);
        return {
          id: output.id,
          url: output.url,
          duration: output.duration,
          storage_transfer_success: false,
        };
      }
    }));

    return Response.json({
      status: "succeeded",
      task_id: String(task.id),
      videos,
    });
  } catch (error) {
    console.error("[kling-motion-control-query]", error);
    return Response.json({ error: "查询服务异常" }, { status: 502 });
  }
});
```

## Web 前端：提交后自动轮询

```typescript
interface MotionVideo {
  id?: string;
  url: string;
  duration?: string;
  storage_transfer_success?: boolean;
}

async function queryMotionTask(taskId: string) {
  const { data, error } = await supabase.functions.invoke(
    "kling-motion-control-query",
    { body: { task_id: taskId } },
  );
  if (error) throw error;
  return data as {
    status: "submitted" | "processing" | "succeeded" | "failed";
    task_id: string;
    message?: string;
    videos?: MotionVideo[];
  };
}

async function pollMotionTask(
  taskId: string,
  onStatus: (status: string) => void,
) {
  const startedAt = Date.now();
  const deadline = startedAt + 10 * 60 * 1000;
  while (Date.now() < deadline) {
    const result = await queryMotionTask(taskId);
    onStatus(result.status);
    if (result.status === "succeeded") {
      if (!result.videos?.length) throw new Error("任务成功但没有视频结果");
      return result.videos;
    }
    if (result.status === "failed") {
      throw new Error(result.message || "视频生成失败");
    }
    const interval = Date.now() - startedAt < 30_000 ? 3_000 : 7_000;
    await new Promise((resolve) => setTimeout(resolve, interval));
  }
  throw new Error("生成等待超时，可稍后从任务记录继续查询");
}

async function handleGenerate() {
  setStatus("submitting");
  setVideoUrl("");
  const { data, error } = await supabase.functions.invoke(
    "kling-motion-control-create",
    { body: formValues },
  );
  if (error) throw error;
  const taskId = String(data.task_id || data.data?.id || "");
  if (!taskId) throw new Error("创建响应缺少任务 ID");

  setTaskId(taskId);
  setStatus("submitted");
  const videos = await pollMotionTask(taskId, setStatus);
  setVideoUrl(videos[0].url);
  setStatus("succeeded");
}
```

## 强制结果 UI

```tsx
{["submitted", "processing"].includes(status) && (
  <section aria-live="polite">
    <p>{status === "submitted" ? "任务已提交，正在排队" : "视频生成中"}</p>
    <progress />
    <small>任务 ID：{taskId}</small>
  </section>
)}

{status === "succeeded" && videoUrl && (
  <section className="video-result">
    <h2>生成结果</h2>
    <video src={videoUrl} controls playsInline preload="metadata" />
    <div className="result-actions">
      <a href={videoUrl} download="kling-motion-control.mp4">
        下载视频
      </a>
      <button type="button" onClick={() => window.open(videoUrl, "_blank")}>
        新窗口预览
      </button>
    </div>
  </section>
)}
```

跨域URL的浏览器 `download` 属性可能被忽略。若需要保证下载文件而不是打开链接，增加服务端下载代理，返回：

```http
Content-Type: video/mp4
Content-Disposition: attachment; filename="kling-motion-control.mp4"
```

## 页面状态要求

- `idle`：显示上传和参数表单；
- `submitting`：禁用生成按钮；
- `submitted`：显示排队状态和任务 ID，但不显示“生成成功”；
- `processing`：显示生成中与轮询提示；
- `succeeded`：必须同时显示视频预览和下载按钮；
- `failed`：显示失败原因和保留原参数的重试按钮；
- `timeout`：保留任务 ID，提供“继续查询”按钮。

刷新恢复：将 `task_id`、状态和最终持久化视频URL存入业务表；页面加载时对非终态任务继续轮询。用户历史列表只读取业务表中归属于当前登录用户的记录。
