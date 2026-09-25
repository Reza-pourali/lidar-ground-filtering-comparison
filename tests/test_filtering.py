import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lidar_ground_filter.filtering import (
    GroundFilterConfig,
    legacy_fixed_grid_filter,
    multiscale_grid_ground_filter,
)


class TestFiltering(unittest.TestCase):
    def synthetic_cloud(self):
        rng = np.random.default_rng(42)

        gx = np.linspace(0.0, 20.0, 101)
        gy = np.linspace(0.0, 20.0, 101)
        X, Y = np.meshgrid(gx, gy)

        terrain = 100.0 + 0.05 * X + 0.03 * Y
        Z = terrain + rng.normal(0.0, 0.03, terrain.shape)

        xg, yg, zg = X.ravel(), Y.ravel(), Z.ravel()

        n = 1500
        xo = rng.uniform(5.0, 15.0, n)
        yo = rng.uniform(5.0, 15.0, n)
        zo = 100.0 + 0.05 * xo + 0.03 * yo + rng.uniform(2.0, 8.0, n)

        x = np.concatenate([xg, xo])
        y = np.concatenate([yg, yo])
        z = np.concatenate([zg, zo])
        truth = np.concatenate([
            np.ones(len(xg), dtype=bool),
            np.zeros(n, dtype=bool),
        ])
        return x, y, z, truth

    def test_multiscale_separates_synthetic_objects(self):
        x, y, z, truth = self.synthetic_cloud()
        mask, diagnostics = multiscale_grid_ground_filter(
            x, y, z, GroundFilterConfig()
        )

        recall = (mask & truth).sum() / truth.sum()
        rejection = ((~mask) & (~truth)).sum() / (~truth).sum()

        self.assertGreater(recall, 0.98)
        self.assertGreater(rejection, 0.98)
        self.assertEqual(len(diagnostics), 3)

    def test_legacy_matches_original_iteration_logic(self):
        rng = np.random.default_rng(3)
        x = rng.uniform(0, 20, 5000)
        y = rng.uniform(0, 20, 5000)
        z = rng.uniform(100, 110, 5000)

        grid = 2.0
        simplified = legacy_fixed_grid_filter(x, y, z, grid_resolution=grid)

        cx = np.floor(x / grid) * grid
        cy = np.floor(y / grid) * grid
        cells, inv = np.unique(
            np.column_stack((cx, cy)),
            axis=0,
            return_inverse=True,
        )

        mins = np.full(len(cells), np.inf)
        np.minimum.at(mins, inv, z)
        rel = z - mins[inv]

        original = np.ones(len(z), dtype=bool)
        for i in range(5):
            original &= rel <= grid * (i + 1)

        np.testing.assert_array_equal(simplified, original)

    def test_z_bounds_exclude_points(self):
        x = np.array([0.0, 0.1, 0.2])
        y = np.array([0.0, 0.1, 0.2])
        z = np.array([-10.0, 100.0, 5000.0])

        mask = legacy_fixed_grid_filter(
            x, y, z, z_min=0.0, z_max=2000.0
        )

        self.assertFalse(mask[0])
        self.assertTrue(mask[1])
        self.assertFalse(mask[2])


if __name__ == "__main__":
    unittest.main()
