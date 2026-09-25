"""Deterministic synthetic validation of the multi-scale ground filter."""

from pathlib import Path
import sys
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lidar_ground_filter.filtering import GroundFilterConfig, multiscale_grid_ground_filter


def make_synthetic_cloud(seed=7):
    rng = np.random.default_rng(seed)

    gx = np.linspace(0.0, 20.0, 101)
    gy = np.linspace(0.0, 20.0, 101)
    X, Y = np.meshgrid(gx, gy)

    terrain = 100.0 + 0.05 * X + 0.03 * Y
    Z = terrain + rng.normal(0.0, 0.03, terrain.shape)

    x_ground = X.ravel()
    y_ground = Y.ravel()
    z_ground = Z.ravel()

    n_obj = 2000
    x_obj = rng.uniform(5.0, 15.0, n_obj)
    y_obj = rng.uniform(5.0, 15.0, n_obj)
    terrain_obj = 100.0 + 0.05 * x_obj + 0.03 * y_obj
    z_obj = terrain_obj + rng.uniform(2.0, 8.0, n_obj)

    x = np.concatenate([x_ground, x_obj])
    y = np.concatenate([y_ground, y_obj])
    z = np.concatenate([z_ground, z_obj])

    truth = np.concatenate([
        np.ones(len(x_ground), dtype=bool),
        np.zeros(n_obj, dtype=bool),
    ])
    return x, y, z, truth


def main():
    root = Path(__file__).resolve().parents[1]
    x, y, z, truth = make_synthetic_cloud()

    predicted, diagnostics = multiscale_grid_ground_filter(
        x, y, z, GroundFilterConfig()
    )

    recall = (predicted & truth).sum() / truth.sum()
    rejection = ((~predicted) & (~truth)).sum() / (~truth).sum()

    fig = plt.figure(figsize=(11, 5))

    ax1 = fig.add_subplot(121, projection="3d")
    ax1.scatter(x[truth], y[truth], z[truth], s=1, label="Ground")
    ax1.scatter(x[~truth], y[~truth], z[~truth], s=2, label="Non-ground")
    ax1.set_title("Synthetic Ground Truth")
    ax1.legend()

    ax2 = fig.add_subplot(122, projection="3d")
    ax2.scatter(x[predicted], y[predicted], z[predicted], s=1, label="Predicted ground")
    ax2.scatter(x[~predicted], y[~predicted], z[~predicted], s=2, label="Predicted non-ground")
    ax2.set_title("Multi-scale Grid Filter")
    ax2.legend()

    fig.tight_layout()
    out = root / "figures" / "synthetic_filter_demo.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print(f"Ground recall: {recall:.4f}")
    print(f"Non-ground rejection: {rejection:.4f}")
    for d in diagnostics:
        print(d)
    print("Saved:", out)


if __name__ == "__main__":
    main()
