"""Analyze one declared CSV interval column without conflating FG/swapchains."""
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


def numeric(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def percentile(values, fraction):
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def statistics(values):
    if not values:
        return {"count": 0}
    return {"count": len(values), "mean": sum(values) / len(values),
            "median": percentile(values, .5), "maximum": max(values),
            **{f"p{p:g}": percentile(values, p / 100)
               for p in (90, 95, 99, 99.9, 99.99)}}


def analyze(rows, interval_column):
    intervals = [numeric(row.get(interval_column)) for row in rows]
    values = [x for x in intervals if x is not None and x > 0]
    result = {"rows": len(rows), "valid_intervals": len(values),
              "missing_or_nonpositive_intervals": len(rows) - len(values),
              "interval_ms": statistics(values)}
    if values:
        result["interval_rate_fps"] = 1000 / (sum(values) / len(values))
        result["sum_interval_seconds"] = sum(values) / 1000
        result["slow_tails"] = {}
        for fraction in (.01, .001, .0001):
            count = math.ceil(len(values) * fraction)
            slow = sorted(values, reverse=True)[:count]
            reliable = count >= 20
            result["slow_tails"][f"{fraction * 100:g}%"] = {
                "count": count, "sufficient_tail_samples": reliable,
                "slowest_mean_reciprocal_fps": 1000 / (sum(slow) / count) if reliable else None,
                "percentile_reciprocal_fps": 1000 / percentile(values, 1 - fraction) if reliable else None,
                "method": "ceil(N*fraction) slowest intervals; percentile uses linear interpolation",
            }
        segment_median = percentile(values, .5)
        result["spikes"] = {
            "threshold_counts": {str(t): sum(x > t for x in values) for t in (33.3, 50, 100)},
            "above_twice_segment_median": sum(x > 2 * segment_median for x in values),
            "worst_10_ms": sorted(values, reverse=True)[:10],
        }
    result["timing_fields"] = {}
    for column in ("MsGPULatency", "GPULatency", "MsGPUTime", "MsGPUBusy", "GPUBusy",
                   "DisplayLatency", "MsUntilDisplayed", "MsRenderPresentLatency", "MsPCLatency",
                   "MsClickToPhotonLatency", "ClickToPhotonLatency", "MsAllInputToPhotonLatency",
                   "AllInputToPhotonLatency", "InstrumentedLatency", "MsAnimationError"):
        if any(column in row for row in rows):
            all_values = [numeric(row.get(column)) for row in rows]
            valid = [x for x in all_values if x is not None and x >= 0]
            result["timing_fields"][column] = {**statistics(valid), "missing": len(rows) - len(valid)}
    result["not_displayed_rows"] = sum(row.get("DisplayedTime") == "NA" or row.get("Dropped") == "1" for row in rows)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--interval-column", required=True)
    parser.add_argument("--time-column")
    parser.add_argument("--start", type=float)
    parser.add_argument("--end", type=float)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if (args.start is not None or args.end is not None) and not args.time_column:
        parser.error("A time column is required for segment bounds")
    if args.start is not None and args.end is not None and args.end <= args.start:
        parser.error("End must follow start")
    with args.csv.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if args.interval_column not in (reader.fieldnames or []):
            parser.error("Declared interval column is absent")
        if args.time_column and args.time_column not in reader.fieldnames:
            parser.error("Declared time column is absent")
        rows = list(reader)
    selected = []
    excluded = 0
    for row in rows:
        time = numeric(row.get(args.time_column)) if args.time_column else None
        if args.time_column and (time is None or (args.start is not None and time < args.start)
                                or (args.end is not None and time > args.end)):
            excluded += 1
            continue
        selected.append(row)
    groups = defaultdict(list)
    for row in selected:
        groups[(row.get("SwapChainAddress", "unknown"), row.get("FrameType") or "unclassified")].append(row)
    result = {"schema_version": 1, "interval_column": args.interval_column,
              "input_rows": len(rows), "selected_rows": len(selected), "excluded_rows": excluded,
              "segment": {"time_column": args.time_column, "start": args.start, "end": args.end},
              "limitations": ["Rate describes the selected interval column only.",
                              "FrameType requires verified producer instrumentation.",
                              "Software timing fields are not physical display photon measurements.",
                              "Trace loss and capture overhead must be validated independently."],
              "groups": [{"swapchain": key[0], "frame_type": key[1], **analyze(value, args.interval_column)}
                         for key, value in groups.items()]}
    with args.output.open("x", encoding="utf-8") as target:
        json.dump(result, target, indent=2, allow_nan=False)
    print(json.dumps({"groups": len(groups), "selected_rows": len(selected)}))


if __name__ == "__main__":
    main()
