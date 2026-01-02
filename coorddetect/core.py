import os
import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull

# ============================================================
# Coordinate System Profiles
# ============================================================

COORD_PROFILES = {
    "latlon": {"x": (-180, 180), "y": (-90, 90)},
    "utm": {"x": (100000, 900000), "y": (0, 1e7)},
    "local": {"x": (-1e6, 1e6), "y": (-1e6, 1e6)},
}

# ============================================================
# Helpers
# ============================================================

def _numeric_cleanup(df):
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace(",", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="ignore")
    return df


def _compute_confidence(scores, xyz_cols, numeric_cols, contiguous):
    top = scores.loc[xyz_cols]
    rest = scores.drop(xyz_cols)

    separation = (top.mean() - rest.mean()) / (scores.max() + 1e-9)
    contig_bonus = 0.15 if contiguous else 0.0

    return float(np.clip(0.6 * separation + contig_bonus + 0.25, 0, 1))


def _compute_bounds(xyz, robust=False, q=(0.01, 0.99)):
    if robust:
        mins = xyz.quantile(q[0])
        maxs = xyz.quantile(q[1])
    else:
        mins = xyz.min()
        maxs = xyz.max()

    return {
        "min": mins.to_dict(),
        "max": maxs.to_dict(),
        "extent": (maxs - mins).to_dict(),
        "center": ((maxs + mins) / 2).to_dict(),
        "robust": robust,
    }


def _infer_crs(x, y):
    for name, r in COORD_PROFILES.items():
        if (
            x.between(*r["x"]).all()
            and y.between(*r["y"]).all()
        ):
            return name
    return "unknown"


def _point_density(xyz):
    hull = ConvexHull(xyz[:, :2])
    area = hull.volume  # 2D area
    density = len(xyz) / area if area > 0 else np.nan
    spacing = np.sqrt(1 / density) if density > 0 else np.nan

    return {
        "area": area,
        "points": len(xyz),
        "density": density,
        "avg_spacing": spacing,
    }


def _convex_hull(xyz, dim=2):
    if dim == 2:
        hull = ConvexHull(xyz[:, :2])
        return xyz[hull.vertices].tolist()
    elif dim == 3:
        hull = ConvexHull(xyz)
        return xyz[hull.vertices].tolist()
    return None

# ============================================================
# Core API
# ============================================================

def detect_xyz(
    df,
    id_col=None,
    expected_range="auto",
    prefer_contiguous=True,
    return_bounds=True,
    robust_bounds=True,
    return_hull=True,
    hull_dim=2,
    return_density=True,
):
    """
    Full-feature XYZ detection with spatial diagnostics.
    """

    df = _numeric_cleanup(df)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 3:
        raise ValueError("Not enough numeric columns.")

    variances = df[numeric_cols].var()
    ranges = df[numeric_cols].max() - df[numeric_cols].min()
    scores = variances + ranges / (ranges.max() + 1e-9)

    xyz_candidates = scores.sort_values(ascending=False).head(3).index.tolist()
    xyz_cols = [c for c in df.columns if c in xyz_candidates]

    contiguous = False
    if prefer_contiguous:
        for i in range(len(numeric_cols) - 2):
            block = numeric_cols[i:i + 3]
            if all(c in xyz_candidates for c in block):
                xyz_cols = block
                contiguous = True
                break

    if id_col and id_col in df.columns:
        out = df[[id_col] + xyz_cols].copy()
        out.columns = ["ID", "X", "Y", "Z"]
        xyz_only = out[["X", "Y", "Z"]]
    else:
        out = df[xyz_cols].copy()
        out.columns = ["X", "Y", "Z"]
        xyz_only = out

    confidence = _compute_confidence(scores, xyz_cols, numeric_cols, contiguous)

    bounds = _compute_bounds(xyz_only, robust=robust_bounds) if return_bounds else None

    crs_guess = _infer_crs(xyz_only["X"], xyz_only["Y"])

    density = (
        _point_density(xyz_only.values)
        if return_density and len(xyz_only) >= 10
        else None
    )

    hull = (
        _convex_hull(xyz_only.values, hull_dim)
        if return_hull and len(xyz_only) >= 10
        else None
    )

    metadata = {
        "selected_columns": xyz_cols,
        "confidence": confidence,
        "crs_guess": crs_guess,
        "bounds": bounds,
        "density": density,
        "convex_hull": hull,
    }

    return out, metadata

# ============================================================
# Batch API (CSV + Excel)
# ============================================================

def detect_xyz_batch(
    input_folder,
    output_folder,
    recursive=False,
    **kwargs
):
    os.makedirs(output_folder, exist_ok=True)
    results = []

    for root, _, files in os.walk(input_folder):
        for f in files:
            if not f.lower().endswith((".csv", ".xlsx", ".xls")):
                continue

            path = os.path.join(root, f)

            try:
                df = (
                    pd.read_csv(path)
                    if f.lower().endswith(".csv")
                    else pd.read_excel(path)
                )

                xyz, meta = detect_xyz(df, **kwargs)

                out_name = os.path.splitext(f)[0] + "_xyz.csv"
                xyz.to_csv(os.path.join(output_folder, out_name), index=False)

                results.append({
                    "file": f,
                    "confidence": meta["confidence"],
                    "crs": meta["crs_guess"]
                })

            except Exception as e:
                results.append({"file": f, "error": str(e)})

        if not recursive:
            break

    return results
