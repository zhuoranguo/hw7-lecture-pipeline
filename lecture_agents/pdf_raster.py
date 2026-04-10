"""Rasterize a PDF to one PNG per slide."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def rasterize_pdf(pdf_path: Path, out_dir: Path, zoom: float = 2.0) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(zoom, zoom)
    count = 0
    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        idx = i + 1
        out_path = out_dir / f"slide_{idx:03d}.png"
        pix.save(out_path.as_posix())
        count += 1
    doc.close()
    return count
