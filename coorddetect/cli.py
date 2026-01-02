import argparse
from .core import detect_xyz_batch

def main():
    parser = argparse.ArgumentParser(
        description="Automatic XYZ coordinate detection from CSV and Excel files"
    )

    parser.add_argument("input", help="Input folder containing CSV/Excel files")
    parser.add_argument("output", help="Output folder for XYZ results")

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process subfolders recursively"
    )

    parser.add_argument(
        "--robust-bounds",
        action="store_true",
        help="Use percentile-based bounding box"
    )

    args = parser.parse_args()

    detect_xyz_batch(
        input_folder=args.input,
        output_folder=args.output,
        recursive=args.recursive,
        robust_bounds=args.robust_bounds
    )
