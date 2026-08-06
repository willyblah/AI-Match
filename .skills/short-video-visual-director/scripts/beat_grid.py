#!/usr/bin/env python3
"""Create a deterministic beat/bar grid for storyboard planning."""
from __future__ import annotations
import argparse, csv, json, sys

def parser():
    p=argparse.ArgumentParser(description="生成音乐节拍与小节时间网格")
    p.add_argument("--bpm",type=float,required=True)
    p.add_argument("--fps",type=float,default=30)
    p.add_argument("--beats-per-bar",type=int,default=4)
    p.add_argument("--bars",type=int,default=8)
    p.add_argument("--json",action="store_true")
    p.add_argument("--csv",dest="csv_path")
    return p

def make_grid(bpm,fps,beats_per_bar,bars):
    if bpm<=0 or fps<=0 or beats_per_bar<1 or bars<1: raise ValueError("参数必须为正数")
    spb=60/bpm; rows=[]
    for i in range(bars*beats_per_bar+1):
        sec=i*spb
        rows.append({"beat":i,"bar":i//beats_per_bar+1,"beat_in_bar":i%beats_per_bar+1,"seconds":round(sec,6),"frame":round(sec*fps)})
    return {"bpm":bpm,"fps":fps,"beats_per_bar":beats_per_bar,"bars":bars,"seconds_per_beat":round(spb,6),"seconds_per_bar":round(spb*beats_per_bar,6),"duration_seconds":round(spb*beats_per_bar*bars,6),"grid":rows}

def main():
    a=parser().parse_args()
    try: data=make_grid(a.bpm,a.fps,a.beats_per_bar,a.bars)
    except ValueError as e: print(json.dumps({"error":str(e)},ensure_ascii=False),file=sys.stderr); return 2
    if a.csv_path:
        with open(a.csv_path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=["beat","bar","beat_in_bar","seconds","frame"]); w.writeheader(); w.writerows(data["grid"])
    print(json.dumps(data,ensure_ascii=False,indent=2) if a.json or not a.csv_path else a.csv_path)
    return 0
if __name__=="__main__": raise SystemExit(main())
