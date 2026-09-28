#!/usr/bin/env bash
# Tao thu muc writeup cho mot bai CTF theo dung cau truc CTF-Writeups.
# Cach dung: bash new_case.sh <ten-bai> [duong-dan-file-de]
#   bash new_case.sh very-hidden "./encoded.bmp"
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLUG="${1:?ten bai la bat buoc (viet thuong, noi dau gach noi)}"
ARTIFACT="${2:-}"
CASE="$ROOT/$SLUG"

[ -e "$CASE" ] && { echo "Da ton tai: $CASE" >&2; exit 1; }
[ -d "$ROOT/_template" ] || { echo "Thieu _template/ trong $ROOT" >&2; exit 1; }

mkdir -p "$CASE/analysis" "$CASE/files"
cp "$ROOT/_template/de.md"      "$CASE/de.md"
cp "$ROOT/_template/writeup.md" "$CASE/writeup.md"
cp "$ROOT/_template/notes.md"   "$CASE/notes.md"
cp "$ROOT/_template/solve.py"   "$CASE/exploit.py"

# Ten bai vao tung file
for f in de.md writeup.md notes.md exploit.py; do
  sed -i "s|<tên bài>|$SLUG|g" "$CASE/$f"
done

if [ -n "$ARTIFACT" ]; then
  [ -f "$ARTIFACT" ] || { echo "Khong tim thay file de: $ARTIFACT" >&2; exit 1; }
  NAME="$(basename "$ARTIFACT" | sed -E 's/ \([0-9]+\)//; s/[^A-Za-z0-9._-]/_/g')"
  cp "$ARTIFACT" "$CASE/files/$NAME"
  SIZE="$(stat -c %s "$CASE/files/$NAME")"
  SHA="$(sha256sum "$CASE/files/$NAME" | cut -d' ' -f1)"
  TYPE="$(file -b "$CASE/files/$NAME" | cut -c1-120)"
  sed -i "s|<artifact>|$NAME|g; s|<kích thước>|${SIZE} byte|; s|<sha256>|$SHA|;
          s|<file type>|$TYPE|; s|<đường dẫn gốc>|$ARTIFACT|" "$CASE/de.md"
  echo "Da copy de: $ARTIFACT -> files/$NAME"
  echo "  size  : ${SIZE} byte"
  echo "  type  : $TYPE"
  echo "  sha256: $SHA"
fi

echo ""
echo "Da tao $CASE"
find "$CASE" -mindepth 1 | sed "s|$CASE/|  |"
