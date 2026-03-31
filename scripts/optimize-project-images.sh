#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="${1:-images/projects}"
COVER_MAX_DIMENSION="${COVER_MAX_DIMENSION:-3200}"
COVER_QUALITY="${COVER_QUALITY:-84}"
GALLERY_MAX_DIMENSION="${GALLERY_MAX_DIMENSION:-2600}"
GALLERY_QUALITY="${GALLERY_QUALITY:-82}"
DRY_RUN="${DRY_RUN:-0}"

if ! command -v sips >/dev/null 2>&1; then
  echo "error: sips is required but was not found in PATH" >&2
  exit 1
fi

if [ ! -d "$ROOT_DIR" ]; then
  echo "error: directory not found: $ROOT_DIR" >&2
  exit 1
fi

tmp_base=""
cleanup() {
  if [ -n "$tmp_base" ] && [ -e "$tmp_base" ]; then
    rm -f "$tmp_base"
  fi
  if [ -n "$tmp_base" ] && [ -e "${tmp_base}.jpg" ]; then
    rm -f "${tmp_base}.jpg"
  fi
}
trap cleanup EXIT INT TERM

format_bytes() {
  awk -v bytes="$1" 'BEGIN {
    split("B KB MB GB", units, " ");
    value = bytes + 0;
    unit = 1;
    while (value >= 1024 && unit < 4) {
      value /= 1024;
      unit += 1;
    }
    printf "%.2f %s", value, units[unit];
  }'
}

total_before=0
total_after=0
files_changed=0
files_skipped=0

while IFS= read -r -d '' file; do
  original_size=$(stat -f '%z' "$file")
  total_before=$((total_before + original_size))

  tmp_base=$(mktemp /tmp/project-image-XXXXXX)
  tmp_file="${tmp_base}.jpg"

  if [ "$(basename "$file")" = "cover.jpg" ]; then
    max_dimension="$COVER_MAX_DIMENSION"
    quality="$COVER_QUALITY"
  else
    max_dimension="$GALLERY_MAX_DIMENSION"
    quality="$GALLERY_QUALITY"
  fi

  sips -s format jpeg -s formatOptions "$quality" -Z "$max_dimension" "$file" --out "$tmp_file" >/dev/null
  optimized_size=$(stat -f '%z' "$tmp_file")

  if [ "$optimized_size" -lt "$original_size" ]; then
    total_after=$((total_after + optimized_size))
    files_changed=$((files_changed + 1))
    printf 'optimized %s (%s -> %s)\n' \
      "$file" \
      "$(format_bytes "$original_size")" \
      "$(format_bytes "$optimized_size")"

    if [ "$DRY_RUN" -eq 0 ]; then
      mv "$tmp_file" "$file"
    fi
  else
    total_after=$((total_after + original_size))
    files_skipped=$((files_skipped + 1))
    printf 'skipped   %s (%s)\n' "$file" "$(format_bytes "$original_size")"
  fi

  rm -f "$tmp_base" "$tmp_file"
  tmp_base=""
done < <(find "$ROOT_DIR" -type f \( -iname '*.jpg' -o -iname '*.jpeg' \) -print0 | sort -z)

saved=$((total_before - total_after))
printf '\nSummary\n'
printf '  Changed: %s\n' "$files_changed"
printf '  Skipped: %s\n' "$files_skipped"
printf '  Before : %s\n' "$(format_bytes "$total_before")"
printf '  After  : %s\n' "$(format_bytes "$total_after")"
printf '  Saved  : %s\n' "$(format_bytes "$saved")"

if [ "$DRY_RUN" -eq 1 ]; then
  printf '  Mode   : dry run\n'
fi
