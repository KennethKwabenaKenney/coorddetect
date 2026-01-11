import os
import pandas as pd
import inspect
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from itertools import combinations

# Optional dependency (used only if hull/density is requested)
try:
    from scipy.spatial import ConvexHull
except Exception:  # pragma: no cover
    ConvexHull = None


# ============================================================
# Helpers (extras only — do NOT affect XYZ detection)
# ============================================================

def _numeric_cleanup(df: pd.DataFrame) -> pd.DataFrame:
    """Clean object columns and convert numeric-looking values (your approach)."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = (
                df[col].astype(str)
                .str.strip()
                .str.replace(",", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="ignore")
    return df


def _compute_bounds(xyz_df: pd.DataFrame, robust: bool = True, q=(0.01, 0.99)) -> dict:
    """
    Bounding box for XYZ. If robust=True, uses quantiles to reduce outlier influence.
    """
    if robust:
        mins = xyz_df.quantile(q[0])
        maxs = xyz_df.quantile(q[1])
    else:
        mins = xyz_df.min()
        maxs = xyz_df.max()

    return {
        "min": mins.to_dict(),
        "max": maxs.to_dict(),
        "extent": (maxs - mins).to_dict(),
        "center": ((maxs + mins) / 2).to_dict(),
        "robust": robust,
        "quantiles": q if robust else None,
    }


def _convex_hull_points(xyz: np.ndarray, dim: int = 2):
    """
    Returns hull vertices points (as list of [x,y] or [x,y,z]) for plotting/export.
    dim=2 uses XY hull. dim=3 uses XYZ hull.
    """
    if ConvexHull is None:
        raise ImportError("scipy is required for convex hull. Install with: pip install scipy")

    if dim == 2:
        pts = xyz[:, :2]
    elif dim == 3:
        pts = xyz
    else:
        raise ValueError("hull_dim must be 2 or 3")

    if len(pts) < 3:
        return None

    hull = ConvexHull(pts)
    return pts[hull.vertices].tolist()


def _hull_area_xy(xy: np.ndarray) -> float:
    """
    Returns convex hull area in XY.
    - For ConvexHull in 2D: hull.volume == area
    """
    if ConvexHull is None:
        raise ImportError("scipy is required for convex hull. Install with: pip install scipy")

    if len(xy) < 3:
        return float("nan")

    hull = ConvexHull(xy)
    return float(hull.volume)


def _point_density_metrics(xyz: np.ndarray) -> dict:
    """
    QA/QC metrics based on XY hull area:
    - area_xy: hull area
    - points: number of points
    - density: points per unit area
    - avg_spacing: sqrt(1/density) (rough mean spacing)
    """
    xy = xyz[:, :2]
    area = _hull_area_xy(xy)
    n = int(len(xyz))

    if not np.isfinite(area) or area <= 0:
        return {
            "area_xy": area,
            "points": n,
            "density": float("nan"),
            "avg_spacing": float("nan"),
        }

    density = n / area
    avg_spacing = float(np.sqrt(1.0 / density)) if density > 0 else float("nan")

    return {
        "area_xy": float(area),
        "points": n,
        "density": float(density),
        "avg_spacing": avg_spacing,
    }

def _integer_fraction(series: pd.Series) -> float:
    x = pd.to_numeric(series, errors="coerce").dropna().to_numpy()
    if x.size == 0:
        return 1.0
    return float(np.mean(np.isclose(x, np.round(x))))


def _unique_count(series: pd.Series) -> int:
    x = pd.to_numeric(series, errors="coerce").dropna()
    return int(x.nunique())


# ============================================================
# Core API — XYZ detection
# ============================================================

def detect_xyz(
    df: pd.DataFrame,
    id_col: Optional[str] = None,
    prefer_contiguous: bool = True,
    return_bounds: bool = True,
    robust_bounds: bool = True,
    bounds_quantiles=(0.01, 0.99),
    return_hull: bool = True,
    hull_dim: int = 2,
    return_density: bool = True,
    **ignored_kwargs
) -> Tuple[pd.DataFrame, dict]:
    """
    Detect X, Y, Z columns using your variance+range logic + contiguous block heuristic,
    then optionally return spatial diagnostics (bounds/hull/density).

    Returns
    -------
    xyz_df : DataFrame
        ['X','Y','Z'] or ['ID','X','Y','Z'] if id_col provided.
    metadata : dict
        detection info + optional diagnostics
    """

    df = _numeric_cleanup(df)

    numeric_cols_all = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols_all) < 3:
        raise ValueError("Not enough numeric columns to identify X, Y, Z coordinates.")
    
    # ✅ HARD FILTER: remove quantized attribute-like columns (e.g., intensity)
    # General rule: mostly-integer AND limited unique values => likely not coordinate axis
    n = len(df)
    
    quantized_cols = []
    for c in numeric_cols_all:
        frac_int = _integer_fraction(df[c])
        nunique = _unique_count(df[c])
    
        # limited unique values threshold:
        # - absolute cap: 4096 (covers 8-bit/12-bit/16-bit-ish attributes)
        # - relative cap: <= 5% of rows (prevents small discrete attributes from winning)
        limited_unique = (nunique <= 4096) or (nunique <= max(20, int(0.05 * n)))
    
        if frac_int >= 0.98 and limited_unique:
            quantized_cols.append(c)
    
    # Use filtered numeric columns if it leaves at least 3; otherwise fall back
    numeric_cols = [c for c in numeric_cols_all if c not in quantized_cols]
    if len(numeric_cols) < 3:
        numeric_cols = numeric_cols_all

    # ---- Scoring logic ----
    variances = df[numeric_cols].var()
    ranges = df[numeric_cols].max() - df[numeric_cols].min()
    range_norm = ranges / (ranges.max() + 1e-9)
    scores = variances + range_norm

    xyz_candidates = scores.sort_values(ascending=False).head(3).index.tolist()
    xyz_cols = [col for col in df.columns if col in xyz_candidates]

    # Contiguous heuristic
    contiguous = False
    if prefer_contiguous:
        best_block = None
        for i in range(len(numeric_cols) - 2):
            block = numeric_cols[i:i + 3]
            if all(col in xyz_candidates for col in block):
                best_block = block
                contiguous = True
                break
        if best_block:
            xyz_cols = best_block

    # Safety check
    if len(xyz_cols) != 3:
        raise ValueError(f"XYZ detection failed to select 3 columns. Selected: {xyz_cols}")

    # Output formatting
    if id_col and id_col in df.columns:
        out = df[[id_col] + xyz_cols].copy()
        out.columns = ["ID", "X", "Y", "Z"]
        xyz_only = out[["X", "Y", "Z"]]
    else:
        out = df[xyz_cols].copy()
        out.columns = ["X", "Y", "Z"]
        xyz_only = out

    meta = {
        "numeric_columns": numeric_cols,
        "scores": scores.to_dict(),
        "xyz_candidates": xyz_candidates,
        "selected_columns": xyz_cols,
        "contiguous_block_used": contiguous,
    }

    # Extras (do not affect selection)
    if return_bounds:
        meta["bounds"] = _compute_bounds(
            xyz_only, robust=robust_bounds, q=bounds_quantiles
        )

    if return_hull:
        if ConvexHull is None:
            meta["convex_hull"] = None
            meta["convex_hull_warning"] = "scipy not installed; hull unavailable"
        else:
            # only compute if enough points
            meta["convex_hull"] = _convex_hull_points(xyz_only.values, dim=hull_dim) if len(xyz_only) >= 3 else None
            meta["convex_hull_dim"] = hull_dim

    if return_density:
        if ConvexHull is None:
            meta["density"] = None
            meta["density_warning"] = "scipy not installed; density unavailable"
        else:
            meta["density"] = _point_density_metrics(xyz_only.values) if len(xyz_only) >= 3 else None

    return out, meta


# ============================================================
# Batch Processing — CSV + Excel
# ============================================================
def detect_xyz_batch(
    input_folder: str,
    output_folder: str,
    recursive: bool = False,
    export_format: str = "csv",
    excel_sheet: Optional[object] = None,
    **detect_kwargs
) -> List[dict]:
    """
    Process all .csv/.xlsx/.xls in a folder. Exports extracted XYZ results.

    This implementation is bulletproof:
    it forwards ONLY arguments that detect_xyz() actually accepts,
    so 'export_format' can NEVER reach detect_xyz().
    """

    os.makedirs(output_folder, exist_ok=True)
    results = []
    supported = (".csv", ".xlsx", ".xls")

    # ✅ Only pass kwargs that detect_xyz accepts (prevents export_format issue forever)
    detect_sig = inspect.signature(detect_xyz)
    allowed_detect_keys = set(detect_sig.parameters.keys())

    # Copy and filter once (caller dict may contain garbage)
    detect_kwargs = dict(detect_kwargs)
    detect_only_kwargs = {k: v for k, v in detect_kwargs.items() if k in allowed_detect_keys}

    for root, _, files in os.walk(input_folder):
        for f in files:
            if not f.lower().endswith(supported):
                continue

            in_path = os.path.join(root, f)
            base = os.path.splitext(f)[0]
            ext = os.path.splitext(f)[1].lower().replace(".", "")  # csv/xlsx/xls

            try:
                # Read input
                if f.lower().endswith(".csv"):
                    df = pd.read_csv(in_path)
                else:
                    # ✅ Always ensure we get a DataFrame, not a dict of DataFrames
                    if excel_sheet is None:
                        df = pd.read_excel(in_path, sheet_name=0)   # first sheet
                    else:
                        df = pd.read_excel(in_path, sheet_name=excel_sheet)
                
                    # If pandas still returns dict (paranoia safety), pick the first sheet
                    if isinstance(df, dict):
                        df = next(iter(df.values()))


                # Detect XYZ (ONLY safe kwargs forwarded)
                xyz_df, meta = detect_xyz(df, **detect_only_kwargs)

                # Avoid overwriting when both sample.csv and sample.xlsx exist
                # -> sample_csv_xyz.csv and sample_xlsx_xyz.csv
                out_stem = f"{base}_{ext}_xyz"

                if export_format.lower() == "csv":
                    out_name = f"{out_stem}.csv"
                    out_path = os.path.join(output_folder, out_name)
                    xyz_df.to_csv(out_path, index=False)

                elif export_format.lower() in ("xlsx", "excel"):
                    out_name = f"{out_stem}.xlsx"
                    out_path = os.path.join(output_folder, out_name)
                    xyz_df.to_excel(out_path, index=False)

                else:
                    raise ValueError("export_format must be 'csv' or 'xlsx'.")

                results.append({
                    "file": f,
                    "output": out_name,
                    "selected_columns": meta.get("selected_columns"),
                    "contiguous_block_used": meta.get("contiguous_block_used"),
                    "has_bounds": "bounds" in meta,
                    "has_hull": meta.get("convex_hull") is not None,
                    "has_density": meta.get("density") is not None,
                })

            except Exception as e:
                results.append({"file": f, "error": str(e)})

        if not recursive:
            break

    return results
