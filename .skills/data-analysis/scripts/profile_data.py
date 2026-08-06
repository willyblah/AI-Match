#!/usr/bin/env python3
"""Quick data profiling script.

Usage:
    python profile_data.py <file_path> [--top N] [--output FORMAT]

Reads a CSV, Excel, or JSON file and prints a comprehensive data profile
including shape, types, missing values, descriptive stats, and value distributions.

Arguments:
    file_path   Path to the data file (.csv, .xlsx, .json, .tsv)
    --top N     Number of top values to show per column (default: 5)
    --output    Output format: text (default) or json
"""

import argparse
import json
import math
import sys
from pathlib import Path


def load_data(file_path):
    """Load data from various file formats."""
    try:
        import pandas as pd
    except ImportError:
        print("Error: pandas is required. Install with: pip install pandas", file=sys.stderr)
        sys.exit(1)

    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Data file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        try:
            return pd.read_csv(path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="gb18030")
    elif suffix == ".tsv":
        try:
            return pd.read_csv(path, sep="\t", encoding="utf-8-sig")
        except UnicodeDecodeError:
            return pd.read_csv(path, sep="\t", encoding="gb18030")
    elif suffix in (".xlsx", ".xls"):
        return pd.read_excel(path)
    elif suffix == ".json":
        try:
            return pd.read_json(path)
        except ValueError:
            return pd.read_json(path, lines=True)
    else:
        raise ValueError(f"Unsupported file format: {suffix or '(none)'}")


def finite_number(value):
    """Convert a numeric value to JSON-safe float, or None when undefined."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def positive_int(value):
    """Parse a positive integer for argparse."""
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def format_number(value):
    """Format an optional numeric statistic for text output."""
    return "N/A" if value is None else f"{value:.4f}"


def format_value(value, max_length=120):
    """Keep free-text values compact in terminal output."""
    text = str(value).replace("\r", " ").replace("\n", " ")
    return text if len(text) <= max_length else text[: max_length - 3] + "..."


def value_key(value, pandas):
    """Return a stable, printable key for scalar or nested values."""
    try:
        if pandas.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


def profile(df, top_n=5):
    """Generate a data profile dictionary."""
    import pandas as pd

    row_count = len(df)
    result = {
        "shape": {"rows": row_count, "columns": len(df.columns)},
        "columns": {},
        "missing_summary": {},
    }

    for col in df.columns:
        series = df[col]
        null_count = int(series.isnull().sum())
        null_pct = round(null_count / row_count * 100, 2) if row_count else 0.0
        is_numeric = (
            pd.api.types.is_numeric_dtype(series.dtype)
            and not pd.api.types.is_bool_dtype(series.dtype)
        )
        keys = None if is_numeric else series.map(lambda value: value_key(value, pd))
        col_info = {
            "dtype": str(series.dtype),
            "non_null_count": int(series.count()),
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": int(
                series.nunique(dropna=True) if is_numeric
                else keys.nunique(dropna=True)
            ),
        }

        if is_numeric:
            desc = series.describe()
            col_info["stats"] = {
                "mean": finite_number(desc["mean"]),
                "std": finite_number(desc["std"]),
                "min": finite_number(desc["min"]),
                "25%": finite_number(desc["25%"]),
                "50%": finite_number(desc["50%"]),
                "75%": finite_number(desc["75%"]),
                "max": finite_number(desc["max"]),
            }
        else:
            high_cardinality = (
                col_info["non_null_count"] >= 20
                and col_info["unique_count"] / col_info["non_null_count"] > 0.8
            )
            col_info["high_cardinality"] = high_cardinality
            if not high_cardinality:
                top_vals = keys.value_counts().head(top_n)
                col_info["top_values"] = {
                    str(k): int(v) for k, v in top_vals.items()
                }

        result["columns"][col] = col_info

        if col_info["null_pct"] > 0:
            result["missing_summary"][col] = col_info["null_pct"]

    return result


def print_text_report(report):
    """Print a human-readable text report."""
    shape = report["shape"]
    print(f"Dataset: {shape['rows']} rows x {shape['columns']} columns\n")

    print("=" * 60)
    print("COLUMN PROFILES")
    print("=" * 60)

    for col, info in report["columns"].items():
        print(f"\n--- {col} ---")
        print(f"  Type: {info['dtype']}")
        print(f"  Non-null: {info['non_null_count']} | Null: {info['null_count']} ({info['null_pct']}%)")
        print(f"  Unique values: {info['unique_count']}")

        if "stats" in info:
            s = info["stats"]
            print(f"  Mean: {format_number(s['mean'])} | Std: {format_number(s['std'])}")
            print(
                f"  Min: {format_number(s['min'])} | 25%: {format_number(s['25%'])} | "
                f"50%: {format_number(s['50%'])} | 75%: {format_number(s['75%'])} | "
                f"Max: {format_number(s['max'])}"
            )

        if info.get("top_values"):
            print("  Top values:")
            for val, count in info["top_values"].items():
                print(f"    {format_value(val)}: {count}")
        elif info.get("high_cardinality"):
            print("  Top values omitted (high cardinality)")

    if report["missing_summary"]:
        print("\n" + "=" * 60)
        print("MISSING DATA SUMMARY")
        print("=" * 60)
        for col, pct in sorted(report["missing_summary"].items(), key=lambda x: -x[1]):
            print(f"  {col}: {pct}% missing")


def main():
    """Main entry point for the data profiling script.

    Parses command line arguments and generates a data profile report
    in either text or JSON format.
    """
    parser = argparse.ArgumentParser(description="Profile a data file")
    parser.add_argument("file_path", help="Path to data file")
    parser.add_argument("--top", type=positive_int, default=5, help="Top N values per column")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    try:
        df = load_data(args.file_path)
        report = profile(df, top_n=args.top)
    except (FileNotFoundError, ImportError, OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.output == "json":
        print(json.dumps(report, indent=2, allow_nan=False))
    else:
        print_text_report(report)


if __name__ == "__main__":
    main()
