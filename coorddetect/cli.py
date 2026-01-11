import argparse
from .core import detect_xyz_batch

def main():
    parser = argparse.ArgumentParser(
        description="coorddetect: robust XYZ detection + QA/QC spatial diagnostics (CSV & Excel)"
    )

    parser.add_argument("input", help="Input folder containing CSV/Excel files")
    parser.add_argument("output", help="Output folder for XYZ exports")

    parser.add_argument("--recursive", action="store_true", help="Include subfolders")

    parser.add_argument("--export-format", default="csv", choices=["csv", "xlsx"],
                        help="Export format for extracted XYZ files")

    parser.add_argument("--excel-sheet", default=None,
                        help="Excel sheet name or index (default: first sheet)")

    # Extras toggles (all default ON)
    parser.add_argument("--no-bounds", action="store_true", help="Disable bounds output")
    parser.add_argument("--no-hull", action="store_true", help="Disable convex hull output")
    parser.add_argument("--no-density", action="store_true", help="Disable density metrics")

    parser.add_argument("--raw-bounds", action="store_true",
                        help="Use min/max bounds instead of robust percentile bounds")

    parser.add_argument("--hull-dim", type=int, default=2, choices=[2, 3],
                        help="Convex hull dimension (2=XY, 3=XYZ)")

    args = parser.parse_args()

    sheet = args.excel_sheet
    if sheet is not None:
        # allow numeric sheet indexes in CLI
        try:
            sheet = int(sheet)
        except Exception:
            pass

    results = detect_xyz_batch(
        input_folder=args.input,
        output_folder=args.output,
        recursive=args.recursive,
        export_format=args.export_format,
        excel_sheet=sheet,
        return_bounds=not args.no_bounds,
        robust_bounds=not args.raw_bounds,
        return_hull=not args.no_hull,
        hull_dim=args.hull_dim,
        return_density=not args.no_density,
    )

    # Simple summary
    ok = sum(1 for r in results if "error" not in r)
    bad = len(results) - ok
    print(f"✅ Completed. Success: {ok}, Failed: {bad}")
    if bad:
        print("Failures:")
        for r in results:
            if "error" in r:
                print(f" - {r['file']}: {r['error']}")
