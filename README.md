# coorddetect

`coorddetect` automatically detects **X, Y, Z coordinate columns** from messy tabular
data (CSV and Excel) using a robust, file-order–preserving heuristic.
It also provides optional **spatial QA/QC diagnostics** such as robust bounding boxes,
convex hull geometry, and point density metrics.

The XYZ detection logic does **not** rely on column names and is designed for
real-world geomatics applications, GIS, and survey datasets.

---

## Installation

```bash
pip install coorddetect
```

---

## Quick Usage

```python
import pandas as pd
from coorddetect import detect_xyz

df = pd.read_csv("points.csv")

xyz, meta = detect_xyz(df)

print(xyz.head())
print("Selected XYZ columns:", meta["selected_columns"])
```

---

## Preserve an ID Column

```python
xyz, meta = detect_xyz(
    df,
    id_col="WallStationID"
)
```

**Output columns**
```
ID, X, Y, Z
```

---

## Spatial Diagnostics (All Features)

By default, `detect_xyz()` can return:

- **Robust bounding box**
- **Convex hull geometry**
- **Point density metrics**

```python
xyz, meta = detect_xyz(
    df,
    return_bounds=True,
    robust_bounds=True,
    bounds_quantiles=(0.01, 0.99),
    return_hull=True,
    hull_dim=2,            # 2 = XY hull, 3 = XYZ hull
    return_density=True
)

print("Bounds:", meta["bounds"])
print("Hull dimension:", meta["convex_hull_dim"])
print("Density:", meta["density"])
```

---

## Robust vs Raw Bounding Box

```python
# Outlier-resistant (recommended)
xyz, meta = detect_xyz(
    df,
    robust_bounds=True,
    bounds_quantiles=(0.01, 0.99)
)

# Raw min / max bounds
xyz, meta = detect_xyz(
    df,
    robust_bounds=False
)
```

---

## Disable Diagnostics (Pure XYZ Detection)

```python
xyz, meta = detect_xyz(
    df,
    return_bounds=False,
    return_hull=False,
    return_density=False
)
```

---

## Batch Processing (CSV & Excel)

Process all `.csv`, `.xlsx`, and `.xls` files in a folder.

```python
from coorddetect import detect_xyz_batch

results = detect_xyz_batch(
    input_folder="data/raw",
    output_folder="data/out",
    recursive=True,
    export_format="csv",     # or "xlsx"
    excel_sheet=None,        # sheet name or index for Excel
    id_col="WallStationID",
    return_bounds=True,
    robust_bounds=True,
    return_hull=True,
    hull_dim=2,
    return_density=True
)

print(results)
```

Each file is exported as:
```
<original_name>_xyz.csv
```

---

## Command Line Interface (CLI)

After installation, the CLI is available:

```bash
coorddetect INPUT_FOLDER OUTPUT_FOLDER
```

### Common Examples

```bash
# Process a folder recursively
coorddetect data/raw data/out --recursive

# Export Excel instead of CSV
coorddetect data/raw data/out --export-format xlsx

# Use raw min/max bounds
coorddetect data/raw data/out --raw-bounds

# Use 3D convex hull
coorddetect data/raw data/out --hull-dim 3

# Disable hull and density metrics
coorddetect data/raw data/out --no-hull --no-density
```

### View all options

```bash
coorddetect --help
```

---

## Notes

- Convex hull and point density metrics require `scipy`
- Convex hull requires at least 3 points (2D) or 4 non-coplanar points (3D)
- All diagnostics are computed **after** XYZ detection
- XYZ detection logic does **not** rely on column names

---

## Applications

- GIS applications
- Survey data validation
- Geomatics research pipelines

---

## License

MIT
