"""Render one physical PDF page, optionally cropping a verified figure/table."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def render(source: Path, page: int, output: Path, bbox=None, dpi: int = 160, poppler: str | None = None) -> dict:
    from pypdf import PdfReader
    from PIL import Image
    source, output = source.resolve(), output.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"PDF not found: {source}")
    if output == source or output.suffix.lower() != ".png":
        raise ValueError("Output must be a separate PNG file.")
    if dpi <= 0:
        raise ValueError("DPI must be positive.")
    reader = PdfReader(source)
    if not 1 <= page <= len(reader.pages):
        raise ValueError(f"Page must be in 1..{len(reader.pages)}.")
    pdf_page = reader.pages[page - 1]
    width, height = float(pdf_page.mediabox.width), float(pdf_page.mediabox.height)
    rotation = pdf_page.rotation % 360
    if rotation not in (0, 90, 180, 270):
        raise ValueError("Unsupported page rotation.")
    if rotation in (90, 270):
        width, height = height, width
    if bbox is not None:
        x0, y0, x1, y1 = map(float, bbox)
        if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
            raise ValueError(f"BBox must stay inside rendered page ({width} x {height} PDF points).")
    binary = str(Path(poppler).resolve()) if poppler else shutil.which("pdftoppm")
    if not binary or not Path(binary).is_file():
        raise RuntimeError("pdftoppm unavailable; use a host renderer or supply --poppler with its executable path.")
    output.parent.mkdir(parents=True, exist_ok=True)
    # The temporary directory is generated and bounded inside the intended output directory.
    with tempfile.TemporaryDirectory(prefix=".paper-render-", dir=output.parent) as temp:
        prefix = Path(temp) / "page"
        command = [binary, "-f", str(page), "-l", str(page), "-singlefile", "-r", str(dpi), "-png", str(source), str(prefix)]
        process = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120)
        if process.returncode:
            raise RuntimeError(f"pdftoppm failed: {process.stderr.strip()}")
        with Image.open(prefix.with_suffix(".png")) as image:
            if bbox is not None:
                sx, sy = image.width / width, image.height / height
                area = (round(x0 * sx), round(y0 * sy), round(x1 * sx), round(y1 * sy))
                if area[2] <= area[0] or area[3] <= area[1]:
                    raise ValueError("BBox is too small at the selected DPI.")
                selected = image.crop(area)
            else:
                selected = image.copy()
            selected.save(output, "PNG")
            size = list(selected.size)
    return {"source_pdf": str(source), "pdf_page": page, "image": str(output),
            "bbox_pdf_points": bbox, "pixels": size, "visually_verified": False}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", required=True, type=int)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--bbox", type=float, nargs=4)
    parser.add_argument("--dpi", type=int, default=160)
    parser.add_argument("--poppler")
    args = parser.parse_args()
    try:
        print(json.dumps(render(args.pdf, args.page, args.out, args.bbox, args.dpi, args.poppler), ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
