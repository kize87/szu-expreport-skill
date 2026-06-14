#!/usr/bin/env python3
"""Validate common structural hazards in generated experiment report DOCX files."""

from __future__ import annotations

import argparse
import dataclasses
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

REQUIRED_SECTIONS = (
    "Experimental Purposes and Requirements",
    "Algorithms or Models Used",
    "Experiment Contents and Process",
    "Discussion and Conclusions",
)

RAW_MARKERS = ("$", "\\(", "\\)", "\\[", "\\]")
PLAIN_FORMULA_PATTERNS = (
    r"\bexp\s*\(",
    r"\bargmax\b",
    r"\bsum[_\(]",
    r"\bprod(?:uct)?[_\(]",
    r"\^\s*[A-Za-z0-9_]",
    r"\|\|.*\|\|",
)


@dataclasses.dataclass
class ValidationResult:
    path: Path
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def extract_document_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        return zf.read("word/document.xml").decode("utf-8")


def extract_text(path: Path) -> str:
    xml = extract_document_xml(path)
    root = ET.fromstring(xml)
    paragraphs = []
    for para in root.findall(".//w:p", WORD_NS):
        text = "".join(node.text or "" for node in para.findall(".//w:t", WORD_NS))
        if text.strip():
            paragraphs.append(text)
    return "\n".join(paragraphs)


def has_section(text: str, section: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).lower()
    target = section.lower()
    if target in normalized:
        return True
    if section == "Experiment Contents and Process":
        return "experimental contents" in normalized and "process" in normalized
    return False


def validate_docx(path: str | Path) -> ValidationResult:
    path = Path(path)
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return ValidationResult(path, [f"File not found: {path}"], warnings)
    if path.suffix.lower() != ".docx":
        errors.append("Output must be a .docx file for structural validation")
        return ValidationResult(path, errors, warnings)

    try:
        text = extract_text(path)
        xml = extract_document_xml(path)
    except (KeyError, zipfile.BadZipFile, ET.ParseError, UnicodeDecodeError) as exc:
        errors.append(f"Could not read DOCX structure: {exc}")
        return ValidationResult(path, errors, warnings)

    for section in REQUIRED_SECTIONS:
        if not has_section(text, section):
            errors.append(f"Missing section: {section}")

    for marker in RAW_MARKERS:
        if marker in text:
            errors.append(f"Raw LaTeX/math marker found: {marker}")

    has_word_equation = "<m:oMath" in xml or "<m:oMathPara" in xml
    if any(re.search(pattern, text) for pattern in PLAIN_FORMULA_PATTERNS) and not has_word_equation:
        errors.append("Formula-like plain text found but no editable Word equation object detected")

    if re.search(r"(?<!\\)\{[^{}\n]{1,80}\}", text):
        warnings.append("Brace-delimited text found; confirm it is not uncompiled LaTeX")

    if not re.search(r"Figure\s+\d+[\.:]", text, flags=re.IGNORECASE):
        warnings.append("No figure captions found")

    if "Table" in text and not re.search(r"Table\s+\d+[\.:]", text, flags=re.IGNORECASE):
        warnings.append("Table text found but no numbered table caption detected")

    if "<w:tbl" not in xml and re.search(r"\bTable\s+\d+[\.:]", text, flags=re.IGNORECASE):
        warnings.append("Table caption found but no Word table structure detected")

    if re.search(r" {6,}", text):
        warnings.append("Long visible space run found")

    return ValidationResult(path, errors, warnings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", help="Generated experiment report .docx")
    args = parser.parse_args(argv)

    result = validate_docx(args.docx)
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    for warning in result.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if result.ok:
        print(f"OK: {result.path}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
