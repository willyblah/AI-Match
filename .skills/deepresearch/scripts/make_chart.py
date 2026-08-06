#!/usr/bin/env python3
"""从 JSON 配置生成静态 PNG 图表，供嵌入 docx 研究报告。

用法：
    python make_chart.py --spec chart_spec.json

配置格式（JSON 文件）：
{
  "type": "bar | hbar | grouped_bar | stacked_bar | line | pie | scatter",
  "title": "标题（写结论而非数据名，如“开源框架 Star 数差距悬殊”）",
  "x": ["类别1", "类别2", ...],                 # 分类标签 / x 轴值
  "series": [{"name": "系列名", "data": [1, 2, 3]}],  # 一个或多个系列
  "xlabel": "x 轴标题（可选）",
  "ylabel": "y 轴标题（可选）",
  "source": "数据来源与时间范围（可选，作为图注）",
  "output": "outputs/chart_1.png"
}

说明：
- pie：用 series[0].data 作为数值，x 作为各扇区标签（类别数建议 2–6）
- scatter：x 为横坐标值，series[0].data 为纵坐标值
- grouped_bar / stacked_bar：多个 series，共享同一组 x 分类
"""

import argparse
import json
import sys
from pathlib import Path


def setup_cjk_font():
    """设置中文字体，避免中文乱码。按常见字体依次尝试。"""
    import matplotlib
    from matplotlib import font_manager

    candidates = [
        "Microsoft YaHei", "SimHei", "PingFang SC", "Heiti SC",
        "Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Zen Hei",
        "Arial Unicode MS",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            matplotlib.rcParams["font.sans-serif"] = [name]
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


def main():
    """入口：读取配置，按类型绘图并输出 PNG。"""
    parser = argparse.ArgumentParser(description="Generate a PNG chart from a JSON spec.")
    parser.add_argument("--spec", required=True, help="图表配置 JSON 文件路径")
    args = parser.parse_args()

    try:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8-sig"))
    except Exception as exc:
        print(f"读取配置失败：{exc}", file=sys.stderr)
        sys.exit(1)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("需要 matplotlib，请安装：pip install matplotlib", file=sys.stderr)
        sys.exit(1)

    setup_cjk_font()

    ctype = spec.get("type", "bar")
    title = spec.get("title", "")
    x = spec.get("x", [])
    series = spec.get("series", [])
    output = spec.get("output")

    if not output:
        print("配置缺少 output 字段", file=sys.stderr)
        sys.exit(1)
    if ctype != "pie" and not series:
        print("配置缺少 series 数据", file=sys.stderr)
        sys.exit(1)

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    palette = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#EECA3B"]
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

    if ctype == "bar":
        ax.bar(x, series[0]["data"], color=palette[0])
    elif ctype == "hbar":
        ax.barh(x, series[0]["data"], color=palette[0])
        ax.invert_yaxis()
    elif ctype == "grouped_bar":
        import numpy as np
        n = len(series)
        width = 0.8 / n
        idx = np.arange(len(x))
        for i, s in enumerate(series):
            ax.bar(idx + i * width, s["data"], width, label=s.get("name", f"系列{i+1}"),
                   color=palette[i % len(palette)])
        ax.set_xticks(idx + width * (n - 1) / 2)
        ax.set_xticklabels(x)
        ax.legend()
    elif ctype == "stacked_bar":
        import numpy as np
        bottom = np.zeros(len(x))
        for i, s in enumerate(series):
            data = np.array(s["data"], dtype=float)
            ax.bar(x, data, bottom=bottom, label=s.get("name", f"系列{i+1}"),
                   color=palette[i % len(palette)])
            bottom += data
        ax.legend()
    elif ctype == "line":
        for i, s in enumerate(series):
            ax.plot(x, s["data"], marker="o", label=s.get("name", f"系列{i+1}"),
                    color=palette[i % len(palette)])
        if len(series) > 1:
            ax.legend()
    elif ctype == "pie":
        data = (series[0]["data"] if series else spec.get("data", []))
        ax.pie(data, labels=x, autopct="%1.1f%%", startangle=90,
               colors=palette[:len(x)])
        ax.axis("equal")
    elif ctype == "scatter":
        for i, s in enumerate(series):
            ax.scatter(x, s["data"], label=s.get("name", f"系列{i+1}"),
                       color=palette[i % len(palette)])
        if len(series) > 1:
            ax.legend()
    else:
        print(f"未知图表类型：{ctype}", file=sys.stderr)
        sys.exit(1)

    if title:
        ax.set_title(title, fontsize=13, fontweight="bold")
    if ctype not in ("pie",):
        if spec.get("xlabel"):
            ax.set_xlabel(spec["xlabel"])
        if spec.get("ylabel"):
            ax.set_ylabel(spec["ylabel"])

    # 分类多或标签长时旋转 x 轴标签，避免重叠
    if ctype in ("bar", "grouped_bar", "stacked_bar", "line") and x:
        max_len = max((len(str(v)) for v in x), default=0)
        if len(x) > 6 or max_len > 6:
            plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    if spec.get("source"):
        fig.text(0.99, 0.01, "来源：" + str(spec["source"]),
                 ha="right", va="bottom", fontsize=8, color="#666666")

    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    print(json.dumps({"status": "succeed", "output": output}, ensure_ascii=False))


if __name__ == "__main__":
    main()
