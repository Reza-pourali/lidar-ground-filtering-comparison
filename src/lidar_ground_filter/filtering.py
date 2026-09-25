"""Ground filtering algorithms for LiDAR point clouds.

The repository includes two related implementations:

1. legacy_fixed_grid_filter
   A mathematically simplified equivalent of the original coursework loop.

2. multiscale_grid_ground_filter
   A corrected multi-scale version in which the spatial ground reference
   changes as grid resolution increases.
"""

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class GroundFilterConfig:
    base_resolution: float = 2.0
    scale_factors: tuple[float, ...] = (1.0, 2.0, 4.0)
    base_height_threshold: float = 0.25
    slope_tolerance: float = 0.15
    z_min: float | None = None
    z_max: float | None = None


@dataclass(frozen=True)
class FilterDiagnostics:
    resolution: float
    height_threshold: float
    candidate_count: int


def _validate_xyz(x, y, z):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)

    if x.ndim != 1 or y.ndim != 1 or z.ndim != 1:
        raise ValueError("x, y, and z must be one-dimensional arrays.")
    if not (len(x) == len(y) == len(z)):
        raise ValueError("x, y, and z must have the same length.")
    if len(x) == 0:
        raise ValueError("Point cloud is empty.")
    return x, y, z


def _valid_mask(z, z_min, z_max):
    valid = np.isfinite(z)
    if z_min is not None:
        valid &= z >= z_min
    if z_max is not None:
        valid &= z <= z_max
    return valid


def _cell_minimum_per_point(x, y, z, resolution):
    if resolution <= 0:
        raise ValueError("resolution must be positive.")

    ix = np.floor((x - np.min(x)) / resolution).astype(np.int64)
    iy = np.floor((y - np.min(y)) / resolution).astype(np.int64)
    cells = np.column_stack((ix, iy))

    _, inverse = np.unique(cells, axis=0, return_inverse=True)
    cell_min = np.full(inverse.max() + 1, np.inf, dtype=np.float64)
    np.minimum.at(cell_min, inverse, z)
    return cell_min[inverse]


def legacy_fixed_grid_filter(
    x,
    y,
    z,
    grid_resolution=2.0,
    z_min=0.0,
    z_max=2000.0,
):
    """Equivalent of the original coursework Python classification logic.

    The original script reused one fixed cell-minimum surface while applying
    thresholds of 2, 4, 6, 8, and 10 m and intersecting the masks. Since later
    thresholds are supersets of the first threshold, the final result equals
    the first pass.

    This function expresses that behavior directly and reproducibly.
    """
    x, y, z = _validate_xyz(x, y, z)
    valid = _valid_mask(z, z_min, z_max)

    result = np.zeros(len(z), dtype=bool)
    if not np.any(valid):
        return result

    xv, yv, zv = x[valid], y[valid], z[valid]
    local_min = _cell_minimum_per_point(xv, yv, zv, grid_resolution)
    result[valid] = (zv - local_min) <= grid_resolution
    return result


def multiscale_grid_ground_filter(
    x,
    y,
    z,
    config=GroundFilterConfig(),
):
    """Classify ground points with a multi-scale grid-minimum filter.

    At each scale:
    - compute the minimum elevation in each XY cell;
    - measure each point's height above that minimum;
    - accept points below a scale-dependent height threshold.

    Final ground points must satisfy all scales.
    """
    x, y, z = _validate_xyz(x, y, z)

    if config.base_resolution <= 0:
        raise ValueError("base_resolution must be positive.")
    if config.base_height_threshold < 0:
        raise ValueError("base_height_threshold must be non-negative.")
    if config.slope_tolerance < 0:
        raise ValueError("slope_tolerance must be non-negative.")
    if not config.scale_factors or any(s <= 0 for s in config.scale_factors):
        raise ValueError("scale_factors must contain positive values.")

    valid = _valid_mask(z, config.z_min, config.z_max)
    result = np.zeros(len(z), dtype=bool)
    diagnostics = []

    if not np.any(valid):
        return result, diagnostics

    xv, yv, zv = x[valid], y[valid], z[valid]
    ground_valid = np.ones(len(zv), dtype=bool)

    for factor in config.scale_factors:
        resolution = config.base_resolution * float(factor)
        local_min = _cell_minimum_per_point(xv, yv, zv, resolution)
        threshold = (
            config.base_height_threshold
            + config.slope_tolerance * resolution
        )

        current = (zv - local_min) <= threshold
        ground_valid &= current

        diagnostics.append(
            FilterDiagnostics(
                resolution=resolution,
                height_threshold=threshold,
                candidate_count=int(np.count_nonzero(ground_valid)),
            )
        )

    result[valid] = ground_valid
    return result, diagnostics
