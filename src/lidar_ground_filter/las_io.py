"""LAS/LAZ input-output helpers."""

from pathlib import Path
import copy
import numpy as np


def _laspy():
    try:
        import laspy
    except ImportError as exc:
        raise ImportError(
            "LAS I/O requires laspy. Install dependencies with "
            "`pip install -r requirements.txt`."
        ) from exc
    return laspy


def read_las(path):
    laspy = _laspy()
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    return laspy.read(path)


def write_classification_outputs(las, ground_mask, output_dir, prefix="classified"):
    laspy = _laspy()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ground_mask = np.asarray(ground_mask, dtype=bool)
    if len(ground_mask) != len(las.points):
        raise ValueError("ground_mask length must match LAS point count.")

    classified = laspy.LasData(copy.deepcopy(las.header))
    classified.points = las.points.copy()
    classified.classification = np.where(ground_mask, 2, 1).astype(np.uint8)

    ground = laspy.LasData(copy.deepcopy(las.header))
    ground.points = las.points[ground_mask].copy()
    if len(ground.points):
        ground.classification = np.full(len(ground.points), 2, dtype=np.uint8)

    non_ground = laspy.LasData(copy.deepcopy(las.header))
    non_ground.points = las.points[~ground_mask].copy()
    if len(non_ground.points):
        non_ground.classification = np.full(len(non_ground.points), 1, dtype=np.uint8)

    classified_path = output_dir / f"{prefix}.las"
    ground_path = output_dir / f"{prefix}_ground.las"
    non_ground_path = output_dir / f"{prefix}_non_ground.las"

    classified.write(classified_path)
    ground.write(ground_path)
    non_ground.write(non_ground_path)

    return classified_path, ground_path, non_ground_path
