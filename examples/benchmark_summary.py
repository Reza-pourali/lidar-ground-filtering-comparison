"""Print documented KNTU ground-classification counts."""

from pathlib import Path
import csv


def main():
    path = Path(__file__).resolve().parents[1] / "data" / "kntu_ground_counts.csv"
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        print(
            f"{row['method']}: "
            f"{int(row['ground_points']):,} ground points "
            f"({float(row['ground_percent']):.3f}%)"
        )


if __name__ == "__main__":
    main()
