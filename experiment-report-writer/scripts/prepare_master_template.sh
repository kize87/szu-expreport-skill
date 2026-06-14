#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 input-template.doc output-master.docx [preview-dir]" >&2
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
  exit 2
fi

input=$1
output=$2
preview_dir=${3:-}

if [[ ! -f "$input" ]]; then
  echo "Input template not found: $input" >&2
  exit 1
fi

if command -v soffice >/dev/null 2>&1; then
  soffice_bin=$(command -v soffice)
elif command -v libreoffice >/dev/null 2>&1; then
  soffice_bin=$(command -v libreoffice)
else
  echo "LibreOffice is required for high-fidelity template preparation. Install LibreOffice and retry." >&2
  exit 1
fi

mkdir -p "$(dirname "$output")"
tmpdir=$(mktemp -d)
profile_dir=$(mktemp -d)
trap 'rm -rf "$tmpdir" "$profile_dir"' EXIT

profile_uri="file://$profile_dir"

if ! "$soffice_bin" --headless --nologo --nofirststartwizard "-env:UserInstallation=$profile_uri" --convert-to docx --outdir "$tmpdir" "$input" >/dev/null; then
  echo "LibreOffice conversion failed. Check LibreOffice installation, macOS quarantine/signing, or provide a Word/WPS-saved .docx master." >&2
  exit 1
fi
converted="$tmpdir/$(basename "${input%.*}").docx"
if [[ ! -f "$converted" ]]; then
  echo "LibreOffice did not create expected DOCX output" >&2
  exit 1
fi
cp "$converted" "$output"

if [[ -n "$preview_dir" ]]; then
  mkdir -p "$preview_dir"
  if ! "$soffice_bin" --headless --nologo --nofirststartwizard "-env:UserInstallation=$profile_uri" --convert-to pdf --outdir "$preview_dir" "$output" >/dev/null; then
    echo "LibreOffice preview rendering failed. Check installation/quarantine or render manually in Word/WPS." >&2
    exit 1
  fi
  pdf="$preview_dir/$(basename "${output%.*}").pdf"
  if command -v pdftoppm >/dev/null 2>&1 && [[ -f "$pdf" ]]; then
    pdftoppm -png -r 150 "$pdf" "$preview_dir/page" >/dev/null
  fi
fi

echo "$output"
