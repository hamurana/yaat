---
name: transcribe-audio
description: Batch-transcribe downloaded YouTube audio into .srt subtitle files using openai-whisper (base model). Use this whenever the user wants to transcribe audio, generate subtitles or captions, run whisper over the video-injest/download-video folder, turn MP3s into text/SRT, or process newly downloaded videos into transcripts. Triggers on phrases like "transcribe the audio", "make subtitles", "run whisper", "generate srt files", or any request to convert the downloaded MP3s into transcripts — even if the user doesn't name whisper or srt explicitly.
---

# Transcribe Audio

Convert every downloaded video's MP3 into an `.srt` subtitle file with
openai-whisper, walking each subfolder of `video-injest/download-video/` in turn.

## Layout this skill expects

The `youtube-video-downloader` skill leaves one folder per video, each holding
three files:

```
video-injest/download-video/
  <Title>/
    <Title>.mp3        <- source audio (input)
    <Title>.info.json  <- yt-dlp metadata (leave alone)
    <Title>.jpg        <- thumbnail (leave alone)
```

After this skill runs, each folder also contains `<Title>.srt` — same base name
as the audio track, as required.

## How to run it

Run the bundled script from the project root. It loops over every subfolder,
transcribes the MP3 with the **base** model, and writes only the `.srt`:

```bash
bash .claude/skills/transcribe-audio/scripts/transcribe.sh
```

Pass a different base folder as the first argument if needed
(`bash .../transcribe.sh some-other-folder`). The default is `video-injest/download-video`.

When it finishes, report the summary line it prints: how many folders were
found, transcribed, skipped, and failed.

## Why the script works the way it does

- **Only the `.srt` is produced**, via `whisper --output_format srt`. Whisper
  *can* emit `.txt`, `.vtt`, `.tsv`, and `.json` too, but we don't want them.
  Generating only the srt is cleaner and safer than producing all five and then
  deleting four — a bulk delete could accidentally remove the sibling
  `.info.json` or `.jpg`, which are source files we must keep. Same end state,
  no risk.
- **Output name matches the soundtrack.** Whisper names its output after the
  input stem and `--output_dir` points back at the same folder, so
  `<Title>.mp3` yields `<Title>.srt` right beside it.
- **Idempotent.** A folder whose `.srt` already exists is skipped, so if a long
  batch is interrupted, re-running resumes instead of redoing finished work.
- **One bad file doesn't abort the batch.** Failures are counted and reported;
  the loop continues to the next folder.

## Notes

- The base model is a deliberate accuracy/speed tradeoff — fast, but less
  accurate than larger models. To change it, edit `MODEL` in
  `scripts/transcribe.sh`.
- First run downloads the base model weights (~140 MB) once; later runs reuse
  the cache.
- The base model is small and fast — on CPU it runs comfortably faster than real
  time, so even a long playlist finishes quickly.
