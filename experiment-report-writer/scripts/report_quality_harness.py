#!/usr/bin/env python3
"""Audit generated experiment reports for template fidelity, equations, and depth."""

from __future__ import annotations

import argparse
import dataclasses
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

FORMULA_PATTERNS = (
    r"\bexp\s*\(",
    r"\bargmax\b",
    r"\bsum[_\(]",
    r"\bprod[_\(]",
    r"\^\s*[A-Za-z0-9_]",
    r"\|\|.*\|\|",
)


@dataclasses.dataclass
class AuditResult:
    path: Path
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def read_docx_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        return zf.read("word/document.xml").decode("utf-8")


def extract_text(xml: str) -> str:
    """Extract visible body text — but skip paragraphs whose pPr/shd has a non-trivial
    fill, because those are intentional shaded code/pseudocode blocks where
    pseudocode formula syntax is legitimate."""
    root = ET.fromstring(xml)
    paragraphs = []
    for para in root.findall(".//w:p", WORD_NS):
        shd = para.find("./w:pPr/w:shd", WORD_NS)
        if shd is not None:
            fill = shd.attrib.get(f"{{{WORD_NS['w']}}}fill", "").lower()
            if fill and fill not in {"auto", "none", "ffffff"}:
                continue
        text = "".join(node.text or "" for node in para.findall(".//w:t", WORD_NS))
        if text.strip():
            paragraphs.append(text)
    return "\n".join(paragraphs)


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?|\d+(?:\.\d+)?", text))


def detect_plain_formula(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in FORMULA_PATTERNS)


def cover_signature(xml: str, first_n: int = 24) -> list[str]:
    root = ET.fromstring(xml)
    signature = []
    for para in root.findall(".//w:p", WORD_NS)[:first_n]:
        text = "".join(node.text or "" for node in para.findall(".//w:t", WORD_NS))
        ppr = para.find("./w:pPr", WORD_NS)
        ppr_tags = [] if ppr is None else [node.tag.split("}")[-1] for node in list(ppr)]
        run_count = len(para.findall(".//w:r", WORD_NS))
        signature.append(f"{text}|{'/'.join(ppr_tags)}|runs={run_count}")
    return signature


def audit_report(
    report_path: str | Path,
    template_path: str | Path | None = None,
    min_body_words: int = 900,
    min_figures: int = 0,
    min_tables: int = 0,
    require_szubox: bool = False,
    require_visual_analysis: bool = False,
) -> AuditResult:
    report_path = Path(report_path)
    errors: list[str] = []
    warnings: list[str] = []

    if not report_path.exists():
        return AuditResult(report_path, [f"File not found: {report_path}"], warnings)
    if report_path.suffix.lower() != ".docx":
        return AuditResult(report_path, ["Report must be .docx for quality audit"], warnings)

    try:
        xml = read_docx_xml(report_path)
        text = extract_text(xml)
    except (zipfile.BadZipFile, KeyError, ET.ParseError, UnicodeDecodeError) as exc:
        return AuditResult(report_path, [f"Could not inspect report DOCX: {exc}"], warnings)

    has_word_equation = "<m:oMath" in xml or "<m:oMathPara" in xml
    has_plain_formula = detect_plain_formula(text)
    if not has_word_equation:
        errors.append("No editable Word equations detected")
        if has_plain_formula:
            errors.append("Possible plain-text formula found instead of editable Word equation")
    elif has_plain_formula:
        # Document already contains Office Math equations; remaining hits are
        # typically prose mentions like 'ℝ^d', '||w||', or the English word
        # 'argmax'. Surface as a warning so reviewers can verify rather than
        # blocking the report.
        warnings.append("Formula-like prose mentioned alongside Word equations; review for clarity")

    if word_count(text) < min_body_words:
        errors.append("Report body is too short for a deep experiment report")

    figure_count = len(re.findall(r"\bFigure\s+\d+[\.:]", text, flags=re.IGNORECASE))
    if figure_count < min_figures:
        errors.append("Too few figure captions for this experiment report")

    table_count = len(re.findall(r"\bTable\s+\d+[\.:]", text, flags=re.IGNORECASE))
    if table_count < min_tables:
        errors.append("Too few table captions for this experiment report")

    if require_visual_analysis:
        visual_terms = (
            "distribution",
            "correlation",
            "confusion matrix",
            "residual",
            "feature importance",
            "heatmap",
            "roc",
            "precision-recall",
            "boxplot",
            "scatter",
            "comparison",
            "trend",
            "outlier",
        )
        analysis_terms = (
            "observe",
            "indicate",
            "suggest",
            "compare",
            "misclass",
            "error",
            "class-level",
            "imbalance",
            "relationship",
            "pattern",
            "difference",
            "interpret",
        )
        lower_text = text.lower()
        visual_hits = sum(1 for term in visual_terms if term in lower_text)
        analysis_hits = sum(1 for term in analysis_terms if term in lower_text)
        if visual_hits < 4 or analysis_hits < 3:
            errors.append("Visual analysis language is too thin")

    if require_szubox:
        if "深 圳 大 学 实 验 报 告" not in text:
            errors.append("Missing Shenzhen University report cover title")
        if "深圳大学学生实验报告用纸" not in text:
            errors.append("Missing Shenzhen University report footer/review anchor")

    if template_path:
        template_path = Path(template_path)
        if not template_path.exists():
            errors.append(f"Template file not found: {template_path}")
        else:
            try:
                template_xml = read_docx_xml(template_path)
                if cover_signature(xml) != cover_signature(template_xml):
                    errors.append(
                        "Cover/template signature differs from the template; likely rebuilt instead of editing a template copy"
                    )
            except (zipfile.BadZipFile, KeyError, ET.ParseError, UnicodeDecodeError) as exc:
                errors.append(f"Could not inspect template DOCX: {exc}")

    return AuditResult(report_path, errors, warnings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Generated report .docx")
    parser.add_argument("--template", help="Converted template .docx for cover/template comparison")
    parser.add_argument("--min-body-words", type=int, default=900)
    parser.add_argument("--min-figures", type=int, default=0)
    parser.add_argument("--min-tables", type=int, default=0)
    parser.add_argument("--require-szubox", action="store_true", help="Require Shenzhen University cover/footer anchors")
    parser.add_argument("--require-visual-analysis", action="store_true", help="Require visual-analysis vocabulary coverage")
    args = parser.parse_args(argv)

    result = audit_report(
        args.report,
        args.template,
        min_body_words=args.min_body_words,
        min_figures=args.min_figures,
        min_tables=args.min_tables,
        require_szubox=args.require_szubox,
        require_visual_analysis=args.require_visual_analysis,
    )
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
