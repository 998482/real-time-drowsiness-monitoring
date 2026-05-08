"""
Fatigue alert log visualization using Matplotlib.
"""

import csv
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt


def read_alert_log(csv_path: Path) -> tuple[list[datetime], list[int]]:
    # Load time series columns used by the line chart.
    timestamps: list[datetime] = []
    alert_counts: list[int] = []

    with csv_path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            # Parse ISO timestamp strings from the log file.
            timestamps.append(datetime.fromisoformat(row["timestamp"]))
            alert_counts.append(int(row["alert_count"]))

    return timestamps, alert_counts


def generate_alert_graph(timestamps: list[datetime], alert_counts: list[int], output_path: Path) -> None:
    # Generate a readable alert-count trend chart.
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, alert_counts, marker="o", color="tab:red", linewidth=2)

    plt.title("Drowsiness Alert Count Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Alert Count")
    plt.grid(True, linestyle="--", alpha=0.4)

    # Rotate labels to keep timestamps readable.
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    # Persist graph as an image for reports/portfolio use.
    plt.savefig(output_path)
    plt.close()


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    csv_path = project_root / "logs" / "alert_log.csv"
    output_path = project_root / "logs" / "alert_count_over_time.png"

    if not csv_path.exists():
        print(f"Log file not found: {csv_path}")
        print("Run the webcam alert system first to generate some log data.")
        return

    timestamps, alert_counts = read_alert_log(csv_path)

    if not timestamps:
        print("Log file is empty. No graph generated.")
        return

    generate_alert_graph(timestamps, alert_counts, output_path)
    print(f"Graph saved to: {output_path}")


if __name__ == "__main__":
    main()
