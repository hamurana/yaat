#!/usr/bin/env bash
#
# download.sh — stage 1 of the process-video pipeline: batch-download every video
# in the nominated playlist(s) with yt-dlp, in ONE resilient pass per playlist URL
# (yt-dlp expands the playlist itself). This is the only batch stage; once the
# download finishes, the orchestrator switches to a PER-VIDEO loop (transcribe ->
# extract-meta -> build-ark-note -> delete the folder) over each subfolder. See
# the process-video SKILL.md.
#
#   download   yt-dlp over every playlist URL in video-injest/video.json
#                -> video-injest/download-video/<Title>/{<Title>.mp3,.info.json,.jpg}
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
#   JSON     defaults to "video-injest/video.json"     (array of playlist URLs)
#   BASE_DIR defaults to "video-injest/download-video"

set -u

JSON="${1:-video-injest/video.json}"
BASE="${2:-video-injest/download-video}"

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

# --- retry pass: PO-token 403 fallback -------------------------------------
# YouTube requires a GVS PO Token to serve its adaptive audio-only streams
# (formats 140/251, the ones "bestaudio" picks). Without one, every metadata
# call still succeeds — so yt-dlp writes <Title>.info.json and <Title>.jpg and
# the folders LOOK populated — but each media fetch from googlevideo.com
# returns "HTTP Error 403: Forbidden" and no .mp3 is ever produced. Combined
# with --ignore-errors the script then exits 0 on a total failure, which is why
# the count check below is mandatory rather than advisory.
#
# The legacy progressive format 18 (360p MP4 with muxed 44k AAC audio) is still
# served WITHOUT a PO token, so it is the fallback. Its lower audio bitrate is
# immaterial downstream: whisper resamples everything to 16 kHz mono anyway.
#
# This must be a SECOND PASS, not "-f 251/18". yt-dlp resolves a "/" format
# fallback at SELECTION time, not download time — 251 is still advertised as
# available, so it would always win the selection and then 403 at fetch.
echo "----------------------------------------------------------------------"
echo "[$(date +%T)] Retry pass: videos that produced no .mp3 (403 fallback)"
retried=0
while IFS= read -r info; do
  dir="$(dirname "$info")"
  find "$dir" -maxdepth 1 -type f -name '*.mp3' | grep -q . && continue
  vid="$(jq -r '.id // empty' "$info")"
  [[ -n "$vid" ]] || continue
  echo "  no .mp3 -> retrying $vid with format 18: $(basename "$dir")"
  retried=$((retried + 1))
  yt-dlp \
    -f 18 \
    --extract-audio \
    --audio-format mp3 \
    --audio-quality 0 \
    --no-write-playlist-metafiles \
    --ignore-errors \
    --no-overwrites \
    --no-playlist \
    --output "$dir/%(title)s.%(ext)s" \
    "https://www.youtube.com/watch?v=$vid"
done < <(find "$BASE" -mindepth 2 -maxdepth 2 -type f -name '*.info.json')
[[ "$retried" -eq 0 ]] && echo "  (nothing to retry — every video already has audio)"

# --- verify ----------------------------------------------------------------
# Count .mp3 files, never folders: a 403'd video still leaves a populated
# folder, so "the folders are there" proves nothing about the audio.
n_dirs="$(find "$BASE" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
n_mp3="$(find "$BASE" -type f -name '*.mp3' | wc -l | tr -d ' ')"
echo "----------------------------------------------------------------------"
echo "Audio check: $n_mp3 .mp3 / $n_dirs video folders"
if [[ "$n_mp3" -lt "$n_dirs" ]]; then
  echo "WARNING: $((n_dirs - n_mp3)) folder(s) still have no .mp3." >&2
  find "$BASE" -mindepth 1 -maxdepth 1 -type d -print0 \
    | while IFS= read -r -d '' d; do
        find "$d" -maxdepth 1 -type f -name '*.mp3' | grep -q . \
          || echo "  MISSING AUDIO: $(basename "$d")" >&2
      done
  echo "These will fail the build-ark-note precondition guard and be left in place." >&2
fi

echo "######################################################################"
echo "# [$(date +%T)] Download done. Hand off to the per-video loop"
echo "#   (transcribe -> extract-meta -> build-ark-note -> delete folder)."
echo "######################################################################"
