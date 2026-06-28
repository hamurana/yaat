#!/usr/bin/env bash
#
# Extract a compact metadata record from each video's yt-dlp <Title>.info.json
# and write it beside the source as <Title>.meta.json.
#
# One subfolder of the base dir = one video. For each, we read the rich
# .info.json yt-dlp produced and project just the six fields we care about,
# using jq. The .info.json itself is left untouched (it is a source file).
#
# Output object (keys kept exactly as specified, spaces and all):
#   "published date" <- .upload_date, reformatted YYYYMMDD -> YYYY-MM-DD
#   "title"          <- .title
#   "channel"        <- .channel
#   "watch date"     <- today's system date (when this script runs)
#   "category"       <- .categories[0]
#   "origin"         <- .webpage_url
#
# Idempotent: a folder whose .meta.json already exists is skipped. This also
# preserves the original "watch date" on re-runs (re-running tomorrow won't
# overwrite a record written today); only newly added videos get processed.
#
# Usage: extract-meta.sh [BASE_DIR]
#   BASE_DIR defaults to "download-video" relative to the current directory.

set -u

BASE_DIR="${1:-download-video}"

if [[ ! -d "$BASE_DIR" ]]; then
  echo "ERROR: base folder not found: $BASE_DIR" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: 'jq' not found on PATH. Install with: brew install jq" >&2
  exit 1
fi

# One "watch date" for the whole run, in local time.
today="$(date +%F)"

total=0
done_count=0
skipped=0
failed=0

# Iterate immediate subfolders only. Each is treated as one video.
for dir in "$BASE_DIR"/*/; do
  [[ -d "$dir" ]] || continue
  total=$((total + 1))
  dir="${dir%/}"
  name="$(basename "$dir")"

  # Pick the first .info.json in the folder (there should be exactly one).
  info="$(find "$dir" -maxdepth 1 -type f -name '*.info.json' | head -n 1)"
  if [[ -z "$info" ]]; then
    echo "SKIP  (no info.json):  $name" >&2
    skipped=$((skipped + 1))
    continue
  fi

  # Name the output after the metadata stem: <Title>.info.json -> <Title>.meta.json
  stem="$(basename "$info")"
  stem="${stem%.info.json}"
  meta="$dir/$stem.meta.json"
  if [[ -f "$meta" ]]; then
    echo "SKIP  (already done):  $name"
    skipped=$((skipped + 1))
    continue
  fi

  echo "----------------------------------------------------------------------"
  echo "Extracting:            $name"
  if jq --arg watch "$today" '{
        "published date": (.upload_date
          | if . and (test("^[0-9]{8}$")) then "\(.[0:4])-\(.[4:6])-\(.[6:8])" else . end),
        "title":          .title,
        "channel":        .channel,
        "watch date":     $watch,
        "category":       (.categories[0] // null),
        "origin":         .webpage_url
      }' "$info" > "$meta"; then
    done_count=$((done_count + 1))
    echo "OK ->                  $meta"
  else
    failed=$((failed + 1))
    rm -f "$meta"   # don't leave a half-written/empty file behind
    echo "FAILED:                $name" >&2
  fi
done

echo "======================================================================"
echo "Folders found: $total | written: $done_count | skipped: $skipped | failed: $failed"

[[ "$failed" -eq 0 ]]
