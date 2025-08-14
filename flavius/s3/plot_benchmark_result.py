#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import sys
from pathlib import Path

def plot_timings(timings_csv: Path, output_png: Path,
                 min_plot_value: float = 0.001, sort_by: str = "avg"):
    """
    绘制 timings.csv 的柱状图，y轴对数显示，保留最大最小误差线
    在柱子右上方显示真实平均、最大、最小耗时，并按 sort_by 排序
    """
    if not timings_csv.exists():
        print(f"Error: {timings_csv} does not exist.")
        sys.exit(1)

    # 1. 读取 timings.csv
    query_times = defaultdict(list)
    with open(timings_csv, "r") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            query = row.get("q")
            time_str = row.get("time")
            if query is None or time_str is None:
                continue
            try:
                duration = float(time_str)
                query_times[query].append(duration)
            except ValueError:
                continue

    if not query_times:
        print(f"No valid timing data found in {timings_csv}")
        sys.exit(1)

    # 2. 计算统计信息
    stats = []
    for q, times in query_times.items():
        if not times:
            continue
        avg_real = sum(times) / len(times)
        min_real = min(times)
        max_real = max(times)
        # 绘图用安全值
        avg_plot = max(avg_real, min_plot_value)
        min_plot = max(min_real, min_plot_value)
        max_plot = max(max_real, min_plot_value)
        stats.append({
            "query": q,
            "avg_display": avg_real,
            "min_display": min_real,
            "max_display": max_real,
            "avg_plot": avg_plot,
            "min_plot": min_plot,
            "max_plot": max_plot
        })

    if not stats:
        print(f"No valid queries with timing data in {timings_csv}")
        sys.exit(1)

    # 3. 按 sort_by 排序
    if sort_by not in ["avg", "min", "max"]:
        sort_by = "avg"
    stats.sort(key=lambda x: x[f"{sort_by}_plot"], reverse=True)

    queries = [x["query"] for x in stats]
    avg_times_plot = [x["avg_plot"] for x in stats]
    min_times_plot = [x["min_plot"] for x in stats]
    max_times_plot = [x["max_plot"] for x in stats]

    avg_times_display = [x["avg_display"] for x in stats]
    min_times_display = [x["min_display"] for x in stats]
    max_times_display = [x["max_display"] for x in stats]

    # 4. 绘图美化
    sns.set(style="whitegrid")
    fig, ax = plt.subplots(figsize=(14, 7))

    # 柱子颜色统一，半透明
    sns.set(style="whitegrid")
    fig, ax = plt.subplots(figsize=(14, 7))

    colors = sns.color_palette("coolwarm", len(queries))  # 新颜色风格
    bars = ax.bar(queries, avg_times_plot,
                  yerr=[ [a - b for a,b in zip(avg_times_plot,min_times_plot)],
                         [a - b for a,b in zip(max_times_plot,avg_times_plot)] ],
                  capsize=6, color=colors, alpha=0.6,
                  edgecolor="black", width=0.4)  # 更细柱子

    ax.set_yscale("log")
    ax.set_xlabel("Query", fontsize=12)
    ax.set_ylabel("Time (seconds, log scale)", fontsize=12)
    ax.set_title(f"Query Benchmark Results from {timings_csv.name} (sorted by {sort_by})", fontsize=14)
    plt.xticks(rotation=45, ha="right", fontsize=10)
    plt.yticks(fontsize=10)
    ax.grid(True, which="both", axis="y", linestyle="--", alpha=0.7)

    # 5. 在柱子右上方显示 max/avg/min 数值，不挡误差线
    for i, bar in enumerate(bars):
        height = bar.get_height()
        x = bar.get_x() + bar.get_width() + 0.01  # 右侧
        y_start = height
        spacing = 0.8  # 行间距
        ax.text(x, y_start, f"{max_times_display[i]:.3f}", color='red', ha='left', va='bottom', fontsize=7)
        ax.text(x, y_start*spacing, f"{avg_times_display[i]:.3f}", color='black', ha='left', va='bottom', fontsize=7)
        ax.text(x, y_start*spacing*spacing, f"{min_times_display[i]:.3f}", color='green', ha='left', va='bottom', fontsize=7)

    # 6. 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', edgecolor='black', label='max'),
        Patch(facecolor='black', edgecolor='black', label='avg'),
        Patch(facecolor='green', edgecolor='black', label='min')
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    plt.tight_layout()
    plt.savefig(output_png, dpi=300)
    print(f"Chart saved to {output_png}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot benchmark timings from a CSV file")
    parser.add_argument("--scale-factor", required=True, help="数据规模因子")
    parser.add_argument("--timings", type=str, default="timings.csv",
                        help="Path to timings.csv file")
    parser.add_argument("--output", type=str, default="timings.png",
                        help="Output PNG file path")
    parser.add_argument("--min-plot-value", type=float, default=0.001,
                        help="Minimal duration to avoid log(0), in seconds")
    parser.add_argument("--sort-by", type=str, default="avg",
                        help="Sort queries by 'avg', 'min', or 'max'")
    args = parser.parse_args()

    timings_csv = Path(args.timings)
    output_png = Path(f"output/query-sf{args.scale_factor}/{args.output}")

    plot_timings(timings_csv, output_png, args.min_plot_value, args.sort_by)
