#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visual Design Director Search CLI.

Usage:
    python3 search.py "<query>" --design-system --app-type <requirementType> \
        [--lang <lang_user>] [--output <DESIGN.md path>] \
        --theme-query <native visual theme ≤20 chars>
    # platform 由 --app-type 自动映射；--platform 仅作可选覆盖。
    python3 search.py "<query>" --domain style [-n 3]
    python3 search.py "<query>" --domain color [-n 1]
    python3 search.py "<query>" --domain font [-n 3]
    python3 search.py "<query>" --domain product [-n 1]

--platform defaults to 'web' (filters out Mobile-only styles).
'mobile' for miniprogram / native app; 'any' for H5 / cross-platform.
"""

import argparse
import sys
import io
from core import CSV_CONFIG, MAX_RESULTS, search
from design_system import generate, fonts_only

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8"
    )
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8"
    )


def format_output(result):
    """Format the search results for display."""
    if "error" in result:
        return f"Error: {result['error']}"

    lines = []
    lines.append(f"## Search Results")
    lines.append(
        f"**Domain:** {result['domain']} | "
        f"**Query:** {result['query']}"
    )
    lines.append(
        f"**Source:** {result['file']} | "
        f"**Found:** {result['count']} results\n"
    )

    for i, row in enumerate(result["results"], 1):
        lines.append(f"### Result {i}")
        for key, value in row.items():
            val = str(value)
            if len(val) > 300:
                val = val[:300] + "..."
            lines.append(f"- **{key}:** {val}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Visual Design Director Search"
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--domain", "-d",
        choices=list(CSV_CONFIG.keys()),
        help="Search domain"
    )
    parser.add_argument(
        "--max-results", "-n",
        type=int,
        default=MAX_RESULTS,
        help="Max results (default: 3)"
    )
    parser.add_argument(
        "--design-system", "-ds",
        action="store_true",
        help="Generate design system candidates"
    )
    parser.add_argument(
        "--fonts-only", "-fo",
        action="store_true",
        help="Output only Font Candidates (platform-filtered, CJK-aware)."
    )
    parser.add_argument(
        "--platform", "-p",
        choices=["web", "mobile", "any"],
        default=None,
        help="可选覆盖。省略时 --design-system 由 --app-type 自动映射"
             "（Mobile App/Mini Program→mobile, H5→any, 其余→web）；--fonts-only→mobile。",
    )
    parser.add_argument(
        "--lang", "-l",
        default="",
        help=(
            "User language from LANGUAGE_SETTINGS lang_user "
            "(e.g. 'Chinese' / 'English' / 'Japanese'). "
            "Enforces a CJK-capable body font for Chinese/Japanese apps."
        ),
    )
    parser.add_argument(
        "--app-type", "-at",
        default="",
        help="requirementType from PRDAgent result (e.g. 'Web', 'Mobile App'). "
             "Filters theme.xlsx; 'Mobile App' miss → fonts-only output.",
    )
    parser.add_argument(
        "--output", "-o",
        default="",
        help="Path to write DESIGN.md content when a theme is auto-hit.",
    )
    parser.add_argument(
        "--theme-query", "-tq",
        default="",
        help=(
            "Workflow-required native-language visual theme phrase (≤20 chars). "
            "Used for local theme matching."
        ),
    )
    args = parser.parse_args()

    if args.fonts_only:
        print(fonts_only(args.query, platform=args.platform, lang=args.lang))
    elif args.design_system:
        # 去 MCP：本地 theme 自动检索（按 app_type 过滤），命中即写 --output，
        # 未命中 → Mobile App 出字体候选 / 其余出 3+3+3 候选。
        print(generate(
            args.query,
            platform=args.platform,
            lang=args.lang,
            app_type=args.app_type,
            output_path=args.output,
            theme_query=args.theme_query,
        ))
    else:
        result = search(args.query, args.domain, args.max_results)
        print(format_output(result))
