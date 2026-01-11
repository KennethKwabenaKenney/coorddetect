# Changelog

All notable changes to this project are documented in this file.

The format follows a simplified version of Keep a Changelog.

---

## [0.1.1] – 2026-01-10

### Added
- Robust bounding box computation for detected XYZ coordinates (optional percentile-based bounds).
- Convex hull geometry extraction (2D XY hull by default, optional 3D hull).
- Point density metrics based on convex hull area.
- Batch processing support for CSV and Excel files (`.csv`, `.xlsx`, `.xls`).
- Command-line interface (CLI) for folder-based XYZ extraction and QA/QC processing.

### Fixed
- Python 3.9 compatibility by replacing PEP 604 union type hints (`|`) with `typing.Optional`.
- Improved robustness when handling numeric columns stored as strings with commas and whitespace.

### Changed
- Refactored spatial diagnostics to run **after** XYZ detection without affecting column selection logic.
- Updated README with detailed usage examples, batch processing, and CLI documentation.

---

## [0.1.0] – Initial Release

### Added
- Automatic detection of X, Y, Z coordinate columns from tabular data using variance and range heuristics.
- Numeric cleanup for object-type columns containing numeric-like values.

