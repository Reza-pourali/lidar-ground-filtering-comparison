# Refactor Notes

## Original Python behavior

The submitted coursework script used a fixed 2 m XY grid, computed the
minimum elevation in each cell once, and then ran five iterations with height
thresholds of 2, 4, 6, 8, and 10 m.

The ground mask was updated with logical AND.

Because every later threshold is larger than the first threshold and the same
cell-minimum surface is reused, every later mask is a superset of the first
mask. Their intersection therefore remains equal to the first 2 m threshold
mask.

The public repository keeps a `legacy_fixed_grid_filter` function that
expresses this effective operation directly.

## Corrected public implementation

The recommended `multiscale_grid_ground_filter` changes grid resolution
between iterations. Each scale therefore produces a different local ground
reference.

The height tolerance is:

```text
height_threshold = base_height_threshold + slope_tolerance * grid_resolution
```

This gives the filter a simple terrain-slope allowance as the spatial scale
grows.

## Evaluation limitation

The original KNTU LAS file was not included during repository cleanup.
Therefore the refactored multi-scale implementation is validated on a
deterministic synthetic point cloud.

The real KNTU counts are preserved as documented coursework results, and the
legacy function is provided for reproducibility when the original LAS file is
available.
