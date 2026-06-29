#!/usr/bin/env bash
#
# download.sh — stage 1 of the process-video pipeline: batch-download every video
# in the nominated playlist(s) with yt-dlp, in ONE resilient pass per playlist URL
# (yt-dlp expands the playlist itself). This is the only batch stage; once the
# download finishes, the orchestrator switches to a PER-VIDEO loop (transcribe ->
# extract-meta -> build-ark-note -> delete the folder) over each subfolder. See
# the process-video SKILL.md.
#
#   download   yt-dlp over every playlist URL in video.json
#                -> download-video/<Title>/{<Title>.mp3,.info.json,.jpg}
#
# Flags follow CLAUDE.md §4: extract mp3, write info.json + jpg thumbnail,
# suppress the stray playlist-metadata folder (--no-write-playlist-metafiles),
# and stay resilient across a batch (--ignore-errors --no-overwrites). The
# download is deliberately a single pass over each playlist URL — NOT the old
# "enumerate URLs then download each with --no-playlist" flow.
#
# set -u, not -e: with --ignore-errors a single region-locked video must not
# abort the batch. yt-dlp's --no-overwrites makes re-running resume cleanly.
#
# Usage: download.sh [JSON] [BASE_DIR]
#   JSON     defaults to "video.json"     (array of playlist URLs)
#   BASE_DIR defaults to "download-video"

set -u

JSON="${1:-video.json}"
BASE="${2:-download-video}"

# --- live log --------------------------------------------------------------
# Mirror everything (this script's banners + yt-dlp's stdout/stderr) to the
# terminal AND a log file, so progress is watchable live and persisted.
# PYTHONUNBUFFERED=1 is essential: yt-dlp is Python, and when its output goes
# through a pipe (tee) or into a file it is block-buffered by default, which
# hides live progress behind big delayed chunks. Unbuffering keeps download
# percentages streaming as they happen.
export PYTHONUNBUFFERED=1
mkdir -p "$BASE"
LOG="${LOG:-$BASE/process-video.log}"
: > "$LOG"                          # fresh log each run
exec > >(tee -a "$LOG") 2>&1        # stdout+stderr -> terminal AND log
echo "Live log: $LOG   (watch in another Terminal with:  tail -f \"$LOG\")"

# --- preflight -------------------------------------------------------------
for tool in yt-dlp jq; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "ERROR: required tool '$tool' not found on PATH." >&2
    exit 1
  fi
done

if [[ ! -f "$JSON" ]]; then
  echo "ERROR: playlist JSON not found: $JSON" >&2
  exit 1
fi

# --- download --------------------------------------------------------------
echo "######################################################################"
echo "# [$(date +%T)] Download (yt-dlp) — batch, one pass per playlist URL"
echo "######################################################################"
while IFS= read -r url; do
  [[ -n "$url" ]] || continue
  echo "----------------------------------------------------------------------"
  echo "Playlist: $url"
  yt-dlp \
    --extract-audio \
    --audio-format mp3 \
    --audio-quality 0 \
    --write-info-json \
    --write-thumbnail \
    --convert-thumbnails jpg \
    --no-write-playlist-metafiles \
    --ignore-errors \
    --no-overwrites \
    --output "$BASE/%(title)s/%(title)s.%(ext)s" \
    "$url"
done < <(jq -r '.[]' "$JSON")

echo "######################################################################"
echo "# [$(date +%T)] Download done. Hand off to the per-video loop"
echo "#   (transcribe -> extract-meta -> build-ark-note -> delete folder)."
echo "######################################################################"
