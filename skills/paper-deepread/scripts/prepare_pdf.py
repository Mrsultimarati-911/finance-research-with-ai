"""Extract a supplied PDF with honest page signals; no OCR or scientific parsing."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def extract_pages(source: Path, engine: str = "auto") -> tuple[str, list[str]]:
    if engine == "auto":
        engine = "pdfplumber" if importlib.util.find_spec("pdfplumber") else "pypdf"
    if not importlib.util.find_spec(engine):
        raise RuntimeError(f"Missing {engine}; use an existing host PDF tool or a Python runtime with this package.")
    if engine == "pdfplumber":
        import pdfplumber
        with pdfplumber.open(source) as pdf:
            return engine, [(page.extract_text(layout=False) or "") for page in pdf.pages]
    from pypdf import PdfReader
    reader = PdfReader(source)
    if reader.is_encrypted and not reader.decrypt(""):
        raise RuntimeError("PDF is encrypted and cannot be read without its password.")
    return engine, [(page.extract_text() or "") for page in reader.pages]


def prepare(source: Path, output: Path, engine: str = "auto") -> dict:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"PDF not found: {source}")
    if source.suffix.lower() != ".pdf":
        raise ValueError("Input must be a PDF file.")
    used_engine, texts = extract_pages(source, engine)
    if not texts:
        raise ValueError("PDF contains no pages.")
    records, lines = [], []
    for page_no, content in enumerate(texts, 1):
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        page_lines = content.splitlines()
        visible = sum(not char.isspace() for char in content)
        # A signal for review, never a certification of readability.
        signal = "empty" if visible == 0 else "sparse" if visible < 30 else "text_present"
        if content.count("\ufffd") / max(visible, 1) > .05:
            signal = "encoding_suspect"
        records.append({"pdf_page": page_no, "lines": len(page_lines),
                        "nonspace_characters": visible, "signal": signal,
                        "needs_review": signal != "text_present"})
        lines.append(f"\n=== PDF page {page_no} ===")
        lines.extend(f"P{page_no:03d}-L{n:04d} {line}" for n, line in enumerate(page_lines, 1))
        if not page_lines:
            lines.append("[NO EXTRACTED TEXT; page may require OCR or visual reading]")
    review_pages = [r["pdf_page"] for r in records if r["needs_review"]]
    status = "needs_ocr_or_visual_review" if all(r["signal"] == "empty" for r in records) else "mixed_or_sparse" if review_pages else "text_extracted"
    manifest = {"schema_version": 1, "source_pdf": str(source),
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "engine": used_engine, "page_count": len(texts), "status": status,
                "review_pages": review_pages, "pages": records,
                "locator": "Physical PDF page and extracted line: P001-L0001",
                "limitations": ["Extraction order, formulas and table alignment require visual checking.",
                                "Signals are heuristic; no OCR, metadata or scientific claims are inferred."]}
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "paper_text.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--engine", choices=["auto", "pdfplumber", "pypdf"], default="auto")
    args = parser.parse_args()
    try:
        result = prepare(args.pdf, args.out, args.engine)
        print(json.dumps({k: result[k] for k in ["source_pdf", "engine", "page_count", "status", "review_pages"]}, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc), "source": str(args.pdf)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
