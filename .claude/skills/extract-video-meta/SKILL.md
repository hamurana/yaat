---
name: extract-video-meta
description: Extract a compact metadata record from each downloaded video's yt-dlp .info.json and save it as <Title>.meta.json. Use whenever the user wants to pull, extract, or summarise video metadata, build .meta.json files, get the published date / channel / category / source URL out of the info.json files, or otherwise distil the download-video folder's metadata. Triggers on phrases like "extract video meta", "make meta.json", "pull the metadata", "get publish dates and channels", or any request to turn the info.json files into a trimmed metadata file.
---

# Extract Video Meta

For every downloaded video, read the rich `<Title>.info.json` yt-dlp produced and
write a trimmed `<Title>.meta.json` beside it, keeping only six fields. Walks each
subfolder of `download-video/` in turn.

## Layout this skill expects

The `youtube-video-downloader` skill leaves one folder per video, each holding
the source `.info.json` (plus the `.mp3`, `.jpg`, and possibly an `.srt`):

```
download-video/
  <Title>/
    <Title>.info.json  <- yt-dlp metadata (input, leave alone)
    <Title>.mp3        <- audio (leave alone)
    <Title>.jpg        <- thumbnail (leave alone)
```

After this skill runs, each folder also contains `<Title>.meta.json`.

## Output format

Each `<Title>.meta.json` is a JSON object with exactly these keys (kept verbatim,
spaces and all):

```json
{
  "published date": "2019-08-19",
  "title": "4 Tips To IMPROVE Your Public Speaking - How to CAPTIVATE an Audience",
  "channel": "Motivation2Study",
  "watch date": "2026-06-28",
  "category": "Education",
  "origin": "https://www.youtube.com/watch?v=962eYqe--Yc"
}
```

Field sources (all but "watch date" come from the `.info.json`):

| Field            | Source in `.info.json`                          |
|------------------|-------------------------------------------------|
| `published date` | `.upload_date` (`YYYYMMDD` reformatted to `YYYY-MM-DD`) |
| `title`          | `.title`                                        |
| `channel`        | `.channel`                                       |
| `watch date`     | today's system date, when the script runs       |
| `category`       | `.categories[0]` (first category, or `null`)    |
| `origin`         | `.webpage_url` (the source video URL)           |

## How to run it

Run the bundled script from the project root. It loops over every subfolder,
extracts the six fields with `jq`, and writes one `.meta.json` per video:

```bash
bash .claude/skills/extract-video-meta/scripts/extract-meta.sh
```

Pass a different base folder as the first argument if needed
(`bash .../extract-meta.sh some-other-folder`). The default is `download-video`.

When it finishes, report the summary line it prints: how many folders were
found, written, skipped, and failed.

## Why the script works the way it does

- **jq projects, never mutates.** It reads the `.info.json` and emits a brand-new
  small object to a separate `.meta.json`; the source metadata file is never
  modified.
- **One "watch date" per run.** The system date is captured once at the start so
  every file written in a single run shares the same `watch date`.
- **Idempotent.** A folder whose `.meta.json` already exists is skipped. This
  resumes cleanly after an interruption and, importantly, preserves the original
  `watch date` — re-running on a later day won't overwrite a record written
  earlier. Only newly added videos get processed. Delete a `.meta.json` to force
  it to be rebuilt.
- **One bad file doesn't abort the batch.** A failed jq run is counted, its
  half-written output removed, and the loop continues to the next folder.

## Notes

- Requires `jq` on PATH (`brew install jq`).
- `published date` reformats yt-dlp's compact `YYYYMMDD` to `YYYY-MM-DD`; if the
  field is missing or not 8 digits, the raw value is passed through unchanged.
- `category` takes the first entry of `.categories`; videos with no category get
  `null`.
