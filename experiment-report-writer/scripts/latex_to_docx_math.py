#!/usr/bin/env python3
"""Render LaTeX formulas to DOCX Office Math with Pandoc."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def wrap_latex(latex: str, display: bool) -> str:
    latex = normalize_latex(latex)
    if display:
        return f"$$\n{latex}\n$$\n"
    return f"${latex}$\n"


def normalize_latex(latex: str) -> str:
    return latex.replace("\\\\", "\\")


def render_latex_to_docx(latex: str, output: str | Path, display: bool = True) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "formula.md"
        source.write_text(wrap_latex(latex, display), encoding="utf-8")
        subprocess.run(
            ["pandoc", str(source), "-o", str(output)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    return output


def contains_office_math(docx: str | Path) -> bool:
    with zipfile.ZipFile(docx) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
    return "<m:oMath" in xml or "<m:oMathPara" in xml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("latex", help="LaTeX formula body, without surrounding $ delimiters")
    parser.add_argument("output", help="Output DOCX containing rendered Office Math")
    parser.add_argument("--inline", action="store_true", help="Render as inline math")
    args = parser.parse_args(argv)

    try:
        output = render_latex_to_docx(args.latex, args.output, display=not args.inline)
    except FileNotFoundError:
        print("pandoc is required to convert LaTeX formulas to Word Office Math.", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or str(exc), file=sys.stderr)
        return exc.returncode or 1

    if not contains_office_math(output):
        print("Output DOCX does not contain Office Math.", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
