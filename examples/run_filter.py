"""Run LiDAR ground classification on a LAS file."""

from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lidar_ground_filter.filtering import (
    GroundFilterConfig,
    legacy_fixed_grid_filter,
    multiscale_grid_ground_filter,
)
from lidar_ground_filter.las_io import read_las, write_classification_outputs


def parse_args():
    p = argparse.ArgumentParser(description="Classify LiDAR ground points.")
    p.add_argument("input_las")
    p.add_argument("--output-dir", default="outputs")
    p.add_argument("--method", choices=["multiscale", "legacy"], default="multiscale")
    p.add_argument("--base-resolution", type=float, default=2.0)
    p.add_argument("--scales", type=float, nargs="+", default=[1.0, 2.0, 4.0])
    p.add_argument("--base-threshold", type=float, default=0.25)
    p.add_argument("--slope-tolerance", type=float, default=0.15)
    p.add_argument("--z-min", type=float, default=None)
    p.add_argument("--z-max", type=float, default=None)
    return p.parse_args()


def main():
    args = parse_args()
    las = read_las(args.input_las)

    if args.method == "legacy":
        mask = legacy_fixed_grid_filter(
            las.x,
            las.y,
            las.z,
            grid_resolution=args.base_resolution,
            z_min=args.z_min,
            z_max=args.z_max,
        )
        diagnostics = []
    else:
        config = GroundFilterConfig(
            base_resolution=args.base_resolution,
            scale_factors=tuple(args.scales),
            base_height_threshold=args.base_threshold,
            slope_tolerance=args.slope_tolerance,
            z_min=args.z_min,
            z_max=args.z_max,
        )
        mask, diagnostics = multiscale_grid_ground_filter(
            las.x, las.y, las.z, config
        )

    paths = write_classification_outputs(
        las,
        mask,
        args.output_dir,
        prefix=Path(args.input_las).stem + "_" + args.method,
    )

    print(f"Total points: {len(las.points):,}")
    print(f"Ground points: {int(mask.sum()):,}")
    print(f"Non-ground points: {int((~mask).sum()):,}")

    for d in diagnostics:
        print(
            f"resolution={d.resolution:.3f} m, "
            f"threshold={d.height_threshold:.3f} m, "
            f"candidates={d.candidate_count:,}"
        )

    print("Outputs:")
    for p in paths:
        print(" ", p)


if __name__ == "__main__":
    main()
