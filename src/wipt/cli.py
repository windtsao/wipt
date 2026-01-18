import argparse
import json
from pathlib import Path

from wipt.pdf_processor import PdfProcessor


def _extract_command(pdf_path: Path) -> int:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    pdf_bytes = pdf_path.read_bytes()
    processor = PdfProcessor()
    result = processor.extract(pdf_bytes)
    print(json.dumps(result.rows, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="WIPT integration helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract", help="Extract fields from a PDF")
    extract_parser.add_argument("--pdf", type=Path, required=True, help="Path to the PDF file")

    args = parser.parse_args()
    if args.command == "extract":
        return _extract_command(args.pdf)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
