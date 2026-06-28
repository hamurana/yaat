---
name: process-video
description: Run the full YouTube-to-Ark pipeline end to end — download every video in the nominated playlist, transcribe it, extract its metadata, and build one curated Obsidian note per video in the Ark vault, deleting each source folder as it finishes so download-video/ ends up empty. Use whenever the user wants to "process the videos", "process the playlist", "run the whole/full pipeline", "download and build the Ark notes", or otherwise take a playlist all the way from URL to finished knowledge-base notes in one go. This orchestrates the youtube-video-downloader, transcribe-audio, extract-video-meta, and build-ark-note skills in the correct dependency order.
---

# Process Video (full pipeline)

End-to-end orchestrator. Takes the playlist URLs in `video.json` all the way to
finished **Ark** notes, then leaves `download-video/` empty. It chains four
existing skills in strict dependency order — it does **not** reimplement them.

## Pipeline stages and their dependencies

```
video.json
   │ 1. download (yt-dlp)          produces: <Title>.mp3 .info.json .jpg
   ▼
download-video/<Title>/
   │ 2. transcribe (whisper)       needs: .mp3        produces: .srt
   │ 3. extract-meta (jq)          needs: .info.json  produces: .meta.json
   ▼
   │ 4. build-ark-note  needs: .srt AND .meta.json AND .jpg
   ▼                    produces: Ark/Learning/<MM>/<DD-MM-YYYY>-<N>.md + thumbnail
Ark/   (then the source folder is DELETED)
```

**Order is not optional.** Stage 4 deletes the source folder, so running it
before 2 and 3 finish destroys un-summarised work. Stages 2 and 3 both depend
only on stage 1, so the download must complete first; 2 and 3 are independent of
each other.

## How to run it

### Stages 1–3 — one script (deterministic, no authoring needed)

From the project root:

```bash
bash .claude/skills/process-video/scripts/fetch-and-prep.sh
```

It runs download → transcribe → extract-meta top-to-bottom (so the dependency
barriers hold), reusing `transcribe-audio` and `extract-video-meta`'s own
scripts. Optional args: `fetch-and-prep.sh [video.json] [download-video]`.

Every stage is idempotent — yt-dlp uses `--no-overwrites`, transcribe/extract
skip folders already done — so a re-run after an interruption resumes cleanly.
The script uses `set -u` (not `-e`) so one region-locked video under
`--ignore-errors` won't abort the batch.

When it finishes, report the per-stage summary lines it printed (downloaded /
transcribed / extracted counts).

#### Watching progress live

The script mirrors **all** of its output (its own stage banners plus every
yt-dlp/whisper line) to both the terminal and a log file at
`download-video/process-video.log`, and runs Python unbuffered so progress
streams as it happens rather than in delayed chunks. The log is truncated at the
start of each run.

- **To watch in real time**, open a second Terminal and run:
  ```bash
  tail -f download-video/process-video.log
  ```
- **When the orchestrator (Claude) runs it**, start `fetch-and-prep.sh` in the
  **background** and periodically `tail` `download-video/process-video.log` to
  surface progress to the user — do **not** block silently until the whole pass
  finishes. (Backgrounding alone hides output in a temp file the user can't see;
  the log file is what makes the run watchable.)

### Stage 4 — build one Ark note per video (you author each body)

Run **only after `fetch-and-prep.sh` has finished**. Process each
`download-video/<Title>/` folder **one at a time**, in this exact order:

0. **Precondition guard — required before any delete.** Confirm the folder holds
   all three inputs: `<Title>.srt`, `<Title>.meta.json`, and `<Title>.jpg`. If
   **any** is missing, an upstream stage failed for this video — **skip the
   folder, do NOT delete it**, and record it as a leftover needing a retry. Only
   proceed when all three exist.

1. **Prepare** the mechanical parts:
   ```bash
   bash .claude/skills/build-ark-note/scripts/prepare-note.sh "download-video/<Title>"
   ```
   Read back `NOTE_PATH=...` and the block between the `FRONTMATTER` markers.

2. **Write the note** at `NOTE_PATH`: the frontmatter block verbatim, then the
   authored summary body below the `---` divider.

3. **Author the body** from the `.srt` following **CLAUDE.md §1** (Hook & Core
   Thesis → Key Arguments by importance → High-Yield Assets kept specific →
   Case Studies → "So What?"), matching the prose of existing notes in
   `Ark/Learning/05` and `06`, with `[[wiki-links]]` on key concepts and named
   people. **Zero hallucination** — write `[Transcript Unclear at this point]`
   rather than guess.

4. **Delete the source folder — only after the note is written:**
   ```bash
   rm -rf "download-video/<Title>"
   ```

## Finish

- Verify nothing is left: `find download-video -mindepth 1 -type d` returns
  nothing. (A stray `.DS_Store` file is harmless and ignored by every loop;
  remove it if you want the folder truly empty.)
- Report: how many notes were created and where, plus any folders deliberately
  left behind (failed the stage-0 guard) and why.

## Partial-failure behavior (expected, not a bug)

A video that fails to download or transcribe lacks the inputs stage 4 needs, so
its folder is **left in place** for a retry rather than deleted. "Nothing left in
`download-video/`" holds for the all-success case; a surviving folder is the
explicit signal of which video needs another pass — just re-run this skill.
