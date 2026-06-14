#!/usr/bin/env python3
"""Extract text and simple OOXML structure counts from a DOCX file."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def inspect_docx(path: str | Path) -> dict:
    path = Path(path)
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
        names = zf.namelist()

    root = ET.fromstring(xml)
    paragraphs = []
    for para in root.findall(".//w:p", WORD_NS):
        text = "".join(node.text or "" for node in para.findall(".//w:t", WORD_NS))
        if text.strip():
            paragraphs.append(text)

    return {
        "path": str(path),
        "paragraph_count": len(root.findall(".//w:p", WORD_NS)),
        "table_count": len(root.findall(".//w:tbl", WORD_NS)),
        "drawing_count": xml.count("<w:drawing"),
        "picture_count": xml.count("<w:pict"),
        "object_count": xml.count("<w:object"),
        "content_controls": xml.count("<w:sdt"),
        "media_files": [name for name in names if name.startswith("word/media/")],
        "text": "\n".join(paragraphs),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", help="DOCX file to inspect")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of readable text")
    args = parser.parse_args()

    info = inspect_docx(args.docx)
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print(f"Path: {info['path']}")
        print(f"Paragraphs: {info['paragraph_count']}")
        print(f"Tables: {info['table_count']}")
        print(f"Drawings: {info['drawing_count']}")
        print(f"Pictures: {info['picture_count']}")
        print(f"Objects: {info['object_count']}")
        print(f"Content controls: {info['content_controls']}")
        print(f"Media files: {len(info['media_files'])}")
        print()
        print(info["text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
