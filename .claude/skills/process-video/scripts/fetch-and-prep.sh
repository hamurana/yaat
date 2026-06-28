#!/usr/bin/env bash
#
# fetch-and-prep.sh — the three deterministic stages of the process-video
# pipeline, run in dependency order in a single pass:
#
#   1. download   yt-dlp over every playlist URL in video.json
#                   -> download-video/<Title>/{<Title>.mp3,.info.json,.jpg}
#   2. transcribe whisper over each mp3   -> <Title>.srt   (needs stage 1's mp3)
#   3. extract    jq over each info.json  -> <Title>.meta.json (needs stage 1)
#
# Stages run top-to-bottom, so the dependency barriers are guaranteed by
# execution order: download fully finishes before transcribe/extract, both of
# which depend only on stage 1's output. Stage 4 (build-ark-note) is NOT here —
# it is destructive (deletes the source folder) and requires Claude to author
# each summary body, so the orchestrator runs it afterwards, per video, gated.
#
# set -u, not -e: with --ignore-errors a single region-locked video must not
# abort the batch. Per-video correctness for stage 4 is enforced by the
# orchestrator's precondition guard, not by this script's exit code. The two
# child scripts and yt-dlp are all idempotent, so re-running resumes cleanly.
#
# Usage: fetch-and-prep.sh [JSON] [BASE_DIR]
#   JSON     defaults to "video.json"     (array of playlist URLs)
#   BASE_DIR defaults to "download-video"

set -u

JSON="${1:-video.json}"
BASE="${2:-download-video}"
SKILLS=".claude/skills"

# --- live log --------------------------------------------------------------
# Mirror everything (this script's banners + every child process's stdout/stderr)
# to the terminal AND a log file, so progress is watchable live and persisted.
# PYTHONUNBUFFERED=1 is essential: yt-dlp and whisper are Python, and when their
# output goes through a pipe (tee) or into a file it is block-buffered by default,
# which hides live progress behind big delayed chunks. Unbuffering keeps download
# percentages and whisper timestamps streaming as they happen.
export PYTHONUNBUFFERED=1
mkdir -p "$BASE"
LOG="${LOG:-$BASE/process-video.log}"
: > "$LOG"                          # fresh log each run
exec > >(tee -a "$LOG") 2>&1        # stdout+stderr -> terminal AND log
echo "Live log: $LOG   (watch in another Terminal with:  tail -f \"$LOG\")"

# --- preflight -------------------------------------------------------------
for tool in yt-dlp whisper jq python3; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "ERROR: required tool '$tool' not found on PATH." >&2
    exit 1
  fi
done

if [[ ! -f "$JSON" ]]; then
  echo "ERROR: playlist JSON not found: $JSON" >&2
  exit 1
fi

# --- 1. download -----------------------------------------------------------
# One resilient yt-dlp pass per playlist URL; yt-dlp expands the playlist.
# Flags follow CLAUDE.md §4: extract mp3, write info.json + jpg thumbnail,
# suppress the stray playlist-metadata folder, and stay resilient across a batch.
echo "######################################################################"
echo "# [$(date +%T)] Stage 1/3: download (yt-dlp)"
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

# --- 2. transcribe ---------------------------------------------------------
echo "######################################################################"
echo "# [$(date +%T)] Stage 2/3: transcribe (whisper)"
echo "######################################################################"
bash "$SKILLS/transcribe-audio/scripts/transcribe.sh" "$BASE"

# --- 3. extract metadata ---------------------------------------------------
echo "######################################################################"
echo "# [$(date +%T)] Stage 3/3: extract metadata (jq)"
echo "######################################################################"
bash "$SKILLS/extract-video-meta/scripts/extract-meta.sh" "$BASE"

echo "######################################################################"
echo "# [$(date +%T)] fetch-and-prep done. Hand off to stage 4 (build-ark-note)."
echo "######################################################################"
