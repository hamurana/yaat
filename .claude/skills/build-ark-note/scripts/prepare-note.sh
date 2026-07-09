#!/usr/bin/env bash
#
# prepare-note.sh — mechanical setup for one Ark Learning note.
#
# Given a single video-injest/download-video/<Title>/ folder, this script handles the
# deterministic parts of building the note (everything except the summary body,
# which Claude must author from the .srt):
#
#   1. reads the video's .meta.json
#   2. copies <Title>.jpg -> Ark/Misc/Thnmbnails/<videoId>.jpg
#   3. computes the next free Ark/Learning/<MM>/<DD-MM-YYYY>-<N>.md slot
#   4. prints the YAML frontmatter + ![[<videoId>.jpg]] header to stdout
#
# It does NOT write the note and does NOT delete the source folder — Claude
# writes the file (frontmatter + authored summary) and deletes the folder after.
#
# Usage:
#   bash .claude/skills/build-ark-note/scripts/prepare-note.sh "video-injest/download-video/<Title>"
#
# Output (stdout): two labelled blocks —
#   NOTE_PATH=Ark/Learning/06/28-06-2026-1.md
#   ---8<--- FRONTMATTER ---8<---
#   <frontmatter + embed line>
#   ---8<--- END ---8<---

set -euo pipefail

VIDEO_DIR="${1:?usage: prepare-note.sh <video-injest/download-video/Title-folder>}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
THUMB_DIR="$REPO_ROOT/Ark/Misc/Thnmbnails"
LEARNING_DIR="$REPO_ROOT/Ark/Learning"

VIDEO_DIR="${VIDEO_DIR%/}"
META_JSON="$(find "$VIDEO_DIR" -maxdepth 1 -name '*.meta.json' | head -1)"
[ -n "$META_JSON" ] || { echo "ERROR: no .meta.json in $VIDEO_DIR" >&2; exit 1; }

# Pull everything we need out of the meta.json in one python pass and emit it as
# shell-eval-able assignments. videoId is the v= param of the origin URL.
eval "$(python3 - "$META_JSON" <<'PY'
import json, sys, re, shlex
m = json.load(open(sys.argv[1]))
origin = m.get("origin", "")
vid = ""
mo = re.search(r"[?&]v=([^&]+)", origin)
if mo:
    vid = mo.group(1)
elif "youtu.be/" in origin:
    vid = origin.rsplit("/", 1)[-1].split("?")[0]
fields = {
    "VIDEO_ID": vid,
    "TITLE": m.get("title", ""),
    "CHANNEL": m.get("channel", ""),
    "ORIGIN": origin,
    "PUBLISH_DATE": m.get("published date", ""),
    "WATCH_DATE": m.get("watch date", ""),
    "CATEGORY": m.get("category", ""),
}
for k, v in fields.items():
    print(f"{k}={shlex.quote(str(v))}")
PY
)"

[ -n "$VIDEO_ID" ] || { echo "ERROR: could not derive videoId from origin '$ORIGIN'" >&2; exit 1; }
[ -n "$WATCH_DATE" ] || { echo "ERROR: meta.json has no watch date" >&2; exit 1; }

# --- 1. copy the thumbnail -------------------------------------------------
SRC_JPG="$(find "$VIDEO_DIR" -maxdepth 1 -name '*.jpg' | head -1)"
[ -n "$SRC_JPG" ] || { echo "ERROR: no .jpg in $VIDEO_DIR" >&2; exit 1; }
mkdir -p "$THUMB_DIR"
cp -f "$SRC_JPG" "$THUMB_DIR/$VIDEO_ID.jpg"

# --- 2. compute the note path ----------------------------------------------
# watch date is YYYY-MM-DD; folder is MM, filename is DD-MM-YYYY-<N>.
YYYY="${WATCH_DATE%%-*}"
MM="$(echo "$WATCH_DATE" | cut -d- -f2)"
DD="$(echo "$WATCH_DATE" | cut -d- -f3)"
DATE_PREFIX="$DD-$MM-$YYYY"
MONTH_DIR="$LEARNING_DIR/$MM"
mkdir -p "$MONTH_DIR"

N=1
while [ -e "$MONTH_DIR/$DATE_PREFIX-$N.md" ]; do
  N=$((N + 1))
done
NOTE_PATH="Ark/Learning/$MM/$DATE_PREFIX-$N.md"

# --- 3. emit frontmatter for Claude to prepend -----------------------------
echo "NOTE_PATH=$NOTE_PATH"
echo "THUMBNAIL=Ark/Misc/Thnmbnails/$VIDEO_ID.jpg"
echo "---8<--- FRONTMATTER ---8<---"
cat <<EOF
---
title: $TITLE
topic:
  - $CATEGORY
channel: $CHANNEL
origin link: $ORIGIN
publish date: $PUBLISH_DATE
watch date: $WATCH_DATE
---
![[$VIDEO_ID.jpg]]

---
EOF
echo "---8<--- END ---8<---"
