#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 input.doc output.docx [--require-libreoffice]" >&2
  exit 2
fi

input=$1
output=$2
require_libreoffice=${3:-}

if [[ ! -f "$input" ]]; then
  echo "Input file not found: $input" >&2
  exit 1
fi

mkdir -p "$(dirname "$output")"

if command -v soffice >/dev/null 2>&1; then
  tmpdir=$(mktemp -d)
  if ! soffice --headless --convert-to docx --outdir "$tmpdir" "$input" >/dev/null; then
    echo "LibreOffice conversion failed. Check LibreOffice installation, macOS quarantine/signing, or provide a Word/WPS-saved .docx master." >&2
    exit 1
  fi
  converted="$tmpdir/$(basename "${input%.*}").docx"
  if [[ ! -f "$converted" ]]; then
    echo "LibreOffice did not create expected DOCX output" >&2
    exit 1
  fi
  mv "$converted" "$output"
  rmdir "$tmpdir" 2>/dev/null || true
elif [[ "$require_libreoffice" == "--require-libreoffice" ]]; then
  echo "LibreOffice is required for this conversion; refusing textutil fallback." >&2
  exit 1
elif command -v textutil >/dev/null 2>&1; then
  textutil -convert docx -output "$output" "$input"
else
  echo "No converter found. Install LibreOffice or use macOS textutil." >&2
  exit 1
fi

echo "$output"
