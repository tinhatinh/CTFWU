#!/usr/bin/env bash
# Tao thu muc writeup cho mot bai CTF theo dung cau truc repo CTFWU.
# Cach dung: bash new_case.sh "<Ten Event>" <ten-bai> [duong-dan-file-de] [--wip]
#   bash new_case.sh "SunshineCTF 2026" very-hidden "./encoded.bmp"
#   bash new_case.sh "H7CTF 2026 Quals" broken-telephone "" --wip
# --wip: bai chua ra co, dat duoi <Event>/_wip/.
set -euo pipefail

TPL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../CTFWU/_template
ROOT="$(dirname "$TPL")"                              # .../CTFWU

EVENT="${1:?tham so 1 la ten cuoc thi, vi du \"SunshineCTF 2026\"}"
SLUG="${2:?ten bai la bat buoc (viet thuong, noi dau gach noi)}"
ARTIFACT="${3:-}"
WIP="${4:-}"

[ -d "$TPL" ] || { echo "Thieu _template/ trong $ROOT" >&2; exit 1; }

CASE="$ROOT/$EVENT"
[ -n "$WIP" ] && CASE="$CASE/_wip"
CASE="$CASE/$SLUG"

[ -e "$CASE" ] && { echo "Da ton tai: $CASE" >&2; exit 1; }

if [ ! -d "$ROOT/$EVENT" ]; then
  echo "Event moi: $ROOT/$EVENT (chua co README.md chi muc nao)." >&2
fi

mkdir -p "$CASE/analysis" "$CASE/files"
cp "$TPL/de.md"      "$CASE/de.md"
cp "$TPL/writeup.md" "$CASE/writeup.md"
cp "$TPL/notes.md"   "$CASE/notes.md"
cp "$TPL/solve.py"   "$CASE/exploit.py"

# Ten bai vao tung file
for f in de.md writeup.md notes.md exploit.py; do
  sed -i "s|<tên bài>|$SLUG|g; s|<Challenge Name>|$SLUG|g" "$CASE/$f"
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
echo ""
echo "Nho: copy anh the de vao files/de.png va chen ![de](files/de.png) vao de.md;"
echo "     xong thi commit trong $ROOT (chi push khi nguoi dung yeu cau)."
