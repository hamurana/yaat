#!/usr/bin/env bash
#
# Transcribe every MP3 under a base folder to an .srt subtitle file using
# openai-whisper (base model). One subfolder = one video.
#
# Why --output_format srt instead of "produce everything then delete":
# each video folder also holds yt-dlp's <Title>.info.json and <Title>.jpg.
# Producing only the .srt leaves those source/metadata files untouched, which
# is exactly what we want. The end state is identical to "keep only the srt"
# but there is no risky bulk-delete step that could clobber the source files.
#
# Idempotent: a folder whose .srt already exists is skipped, so re-running
# after an interruption resumes where it left off instead of redoing work.
#
# Usage: transcribe.sh [DIR]
#   DIR defaults to "download-video" relative to the current directory.
#   DIR may be EITHER a base folder of video subfolders (batch mode) OR a single
#   video folder (per-video mode). If the folder itself directly contains an
#   *.mp3, it is treated as one video; otherwise its immediate subfolders are
#   each treated as a video. This lets the process-video pipeline transcribe one
#   folder at a time while the original `transcribe.sh download-video` batch call
#   keeps working unchanged.

set -u

BASE_DIR="${1:-download-video}"
MODEL="base"

if [[ ! -d "$BASE_DIR" ]]; then
  echo "ERROR: base folder not found: $BASE_DIR" >&2
  exit 1
fi

if ! command -v whisper >/dev/null 2>&1; then
  echo "ERROR: 'whisper' not found on PATH. Install with: pip install -U openai-whisper" >&2
  exit 1
fi

total=0
done_count=0
skipped=0
failed=0

# Decide what to iterate: a single video folder (it directly holds an mp3) or a
# base dir of video subfolders. Either way, each element of "dirs" is one video.
if find "$BASE_DIR" -maxdepth 1 -type f -name '*.mp3' | grep -q .; then
  dirs=("$BASE_DIR")
else
  dirs=("$BASE_DIR"/*/)
fi

for dir in "${dirs[@]}"; do
  [[ -d "$dir" ]] || continue
  total=$((total + 1))
  dir="${dir%/}"
  name="$(basename "$dir")"

  # Pick the first .mp3 in the folder (there should be exactly one).
  mp3="$(find "$dir" -maxdepth 1 -type f -name '*.mp3' | head -n 1)"
  if [[ -z "$mp3" ]]; then
    echo "SKIP  (no mp3):        $name" >&2
    skipped=$((skipped + 1))
    continue
  fi

  # Whisper names the output after the input stem, so <stem>.srt lands here.
  stem="$(basename "${mp3%.*}")"
  srt="$dir/$stem.srt"
  if [[ -f "$srt" ]]; then
    echo "SKIP  (already done):  $name"
    skipped=$((skipped + 1))
    continue
  fi

  echo "----------------------------------------------------------------------"
  echo "Transcribing:          $name"
  if whisper "$mp3" --model "$MODEL" --output_format srt --output_dir "$dir"; then
    done_count=$((done_count + 1))
    echo "OK ->                  $srt"
  else
    failed=$((failed + 1))
    echo "FAILED:                $name" >&2
  fi
done

echo "======================================================================"
echo "Folders found: $total | transcribed: $done_count | skipped: $skipped | failed: $failed"

[[ "$failed" -eq 0 ]]
