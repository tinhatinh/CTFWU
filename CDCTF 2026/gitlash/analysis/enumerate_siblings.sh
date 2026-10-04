#!/usr/bin/env bash
# GitLash: Liet ke 54 instance tren GitLab chung va keo issue/tree/commits ve doc.
# Chi dung lenh co san trong container challenge: curl + jq (khong co python3, khong co nc).
# Chay trong terminal web cua mot instance bat ky:  bash enumerate_siblings.sh
set -u
G=${GITLAB:-http://gitlab.gitlash.internal}
OUT=/tmp/sib; rm -rf "$OUT"; mkdir -p "$OUT/iss" "$OUT/tr" "$OUT/cm"

curl -sS -m 25 "$G/api/v4/projects?per_page=100" -o "$OUT/projects.json"
echo "== so project an danh: $(jq 'length' "$OUT/projects.json")"
jq -r '.[]|[(.id|tostring),.path_with_namespace,.visibility]|@tsv' "$OUT/projects.json" | head -60

IDS=$(jq -r '.[].id' "$OUT/projects.json")
for id in $IDS; do
  curl -sS -m 10 "$G/api/v4/projects/$id/issues?state=all&per_page=100" -o "$OUT/iss/$id.json"
  curl -sS -m 10 "$G/api/v4/projects/$id/repository/tree?recursive=true&per_page=100" -o "$OUT/tr/$id.json"
  curl -sS -m 10 "$G/api/v4/projects/$id/repository/commits?per_page=30" -o "$OUT/cm/$id.json"
done

echo "== project co issue =="
for f in "$OUT"/iss/*.json; do
  n=$(jq 'length' "$f" 2>/dev/null); [ "${n:-0}" != "0" ] && printf '%s:%s ' "$(basename "$f" .json)" "$n"
done; echo

echo "== file khong phai template =="
for f in "$OUT"/tr/*.json; do jq -r '.[]?|.path' "$f"; done | sort | uniq -c

echo "== commit khong phai template =="
for f in "$OUT"/cm/*.json; do jq -r '.[]?|.title' "$f"; done \
  | grep -av 'add node diagnostic and contact info' | sort -u | head -40

echo "== ai da push (author vs committer) =="
for f in "$OUT"/cm/*.json; do
  id=$(basename "$f" .json)
  jq -r --arg id "$id" '.[]?|["p"+$id,.title,.author_name,.author_email,.committer_email]|@tsv' "$f"
done | grep -av 'add node diagnostic' | head -40

echo "== chuoi co trong body issue =="
: > /tmp/all_iss.txt
for f in "$OUT"/iss/*.json; do jq -r '.[]?|"#\(.iid) \(.title)\n\(.description//"\n")"' "$f" >> /tmp/all_iss.txt; done
grep -aoiE 'cdctf.[^"]{0,60}' "$OUT"/iss/*.json | sort -u | head -20
