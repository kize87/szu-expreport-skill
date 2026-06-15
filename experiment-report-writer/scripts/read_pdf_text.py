#!/usr/bin/env python3
"""Extract text from a PDF as plain UTF-8 — never as a `document` content block.

Many third-party Anthropic-compatible backends (GLM, GPT-via-proxy, etc.) reject
the `document` content type that Claude Code's built-in Read tool emits for
binary documents. To stay portable across backends, this skill reads PDFs
through this script instead of through Read.

The script tries pdftotext first (fastest, ships with poppler), then pdfminer.six,
then PyPDF2/pypdf, and finally falls back to a graceful error if no extractor is
available. Output is plain text on stdout (or --output).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _try_pdftotext(path: Path) -> str | None:
    if shutil.which("pdftotext") is None:
        return None
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _try_pdfminer(path: Path) -> str | None:
    try:
        from pdfminer.high_level import extract_text  # type: ignore
    except ImportError:
        return None
    try:
        return extract_text(str(path))
    except Exception:
        return None


def _try_pypdf(path: Path) -> str | None:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            return None
    try:
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return None


def extract_pdf_text(path: str | Path) -> str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    for extractor in (_try_pdftotext, _try_pdfminer, _try_pypdf):
        text = extractor(path)
        if text is not None and text.strip():
            return text
    raise RuntimeError(
        "No PDF text extractor available. Install one of: poppler (pdftotext), "
        "pdfminer.six, pypdf, or PyPDF2."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", help="PDF file to read")
    parser.add_argument("--output", help="Write text to this path instead of stdout")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON with `path` and `text` fields instead of raw text",
    )
    args = parser.parse_args()

    try:
        text = extract_pdf_text(args.pdf)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        payload = json.dumps({"path": args.pdf, "text": text}, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
    else:
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
