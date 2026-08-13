---
name: process-video
description: Run the full YouTube-to-Ark pipeline end to end — download every video in the nominated playlist, then process them one at a time (transcribe, extract metadata, build one curated Obsidian note in the Ark vault, and delete the source folder) until video-injest/download-video/ ends up empty. Use whenever the user wants to "process the videos", "process the playlist", "run the whole/full pipeline", "download and build the Ark notes", or otherwise take a playlist all the way from URL to finished knowledge-base notes in one go. This runs its own download stage (scripts/download.sh) and then orchestrates the transcribe-audio, extract-video-meta, and build-ark-note skills in the correct dependency order.
---

# Process Video (full pipeline)

End-to-end orchestrator. Takes the playlist URLs in `video-injest/video.json` all the way to
finished **Ark** notes, then leaves `video-injest/download-video/` empty. Stage 1 is its own
script (`scripts/download.sh` — there is no separate downloader skill); stages 2–4 chain three
existing skills (`transcribe-audio`, `extract-video-meta`, `build-ark-note`) — it does **not**
reimplement them.

The shape is: **download is batch** (one resilient yt-dlp pass over the whole
playlist), then the workflow **switches to per-video** — each downloaded video is
transcribed, has its metadata extracted, gets its Ark note authored, and is then
**deleted to mark it done**, before the next video starts. Completing one video
fully before the next means an interrupted run only ever removes finished work, so
re-running resumes cleanly.

## Pipeline stages and their dependencies

```
video-injest/video.json
   │ 1. download (yt-dlp)          BATCH, one pass per playlist URL
   ▼                               produces: video-injest/download-video/<Title>/{.mp3,.info.json,.jpg}
video-injest/download-video/
   │
   │  ── then, PER VIDEO (for each <Title>/ folder, one at a time) ──
   │   2. transcribe (whisper)     needs: .mp3        produces: .srt
   │   3. extract-meta (jq)        needs: .info.json  produces: .meta.json
   │   4. build-ark-note           needs: .srt AND .meta.json AND .jpg
   │                               produces: Ark/Learning/<MM>/<DD-MM-YYYY>-<N>.md + thumbnail
   │   5. delete video-injest/download-video/<Title>/   (marks this video done)
   ▼
Ark/   (video-injest/download-video/ ends up empty)
```

**Order is not optional.** The batch download must finish first (stages 2–4 need
its output). Within a video, stage 4 deletes the folder, so it must run only after
2 and 3 have produced the `.srt` and `.meta.json`.

## How to run it

### Stage 1 — download the whole playlist (batch)

From the project root, run the download script in the **foreground**:

```bash
bash .claude/skills/process-video/scripts/download.sh
```

> **⚠️ Run this in the FOREGROUND — do not background it.** Backgrounding the
> download makes **every** video fail with
> `ERROR: unable to download video data: HTTP Error 403: Forbidden`, while the
> script still **exits 0**. Playlist enumeration and per-video extraction succeed
> either way, so yt-dlp writes `<Title>.info.json` and `<Title>.jpg` and the
> folders *look* populated — they are simply missing the `.mp3`. Observed
> 13-08-2026: 0/5 twice backgrounded, then 5/5 in the foreground, identical
> command and flags, minutes apart. Ruled out by direct test: rate limiting, the
> yt-dlp version, the `android_vr` player client, and playlist-vs-watch-URL. The
> mechanism is unconfirmed (it behaves like a network policy applied to
> backgrounded tasks that permits the YouTube API hosts but blocks the
> `googlevideo.com` media hosts). **Stage 2's whisper call is the opposite — that
> one should still be backgrounded**, because it is local and needs no network.

`download.sh` does one resilient yt-dlp pass per playlist URL in
`video-injest/video.json` (per CLAUDE.md §4 — **not** the "enumerate then
download each" flow), with `--ignore-errors --no-overwrites` so one bad video
doesn't abort the batch and a re-run skips already-downloaded files. Optional
args: `download.sh [video-injest/video.json] [video-injest/download-video]`. It mirrors all output to `video-injest/download-video/process-video.log`
(truncated each run) with `PYTHONUNBUFFERED=1` so yt-dlp progress streams live.
A long playlist can take a while in the foreground; if the call times out, the
`--no-overwrites` flag makes a re-run resume rather than restart.

**Verify the audio actually landed — exit 0 is not sufficient.** Count `.mp3`
files, not folders:

```bash
find video-injest/download-video -name '*.mp3' | wc -l
```

Report that count against the number expected. If it is 0 while folders exist,
you hit the backgrounding failure above — just re-run in the foreground, and
`--no-overwrites` will fetch only the missing audio.

### Stages 2–5 — process each video, one at a time

After the download finishes, list the folders and count them:

```bash
find video-injest/download-video -mindepth 1 -maxdepth 1 -type d | sort
```

Let **N** be that count. Print the progress checklist (below) once, then loop over
the folders **one at a time**. For each `video-injest/download-video/<Title>/`:

1. **Transcribe just this video** (whisper). The script auto-detects a single
   video folder, so pass the folder itself:
   ```bash
   bash .claude/skills/transcribe-audio/scripts/transcribe.sh "video-injest/download-video/<Title>"
   ```
   whisper can take minutes — run this **backgrounded** and continue once it
   completes, to avoid the foreground command timeout.

2. **Extract metadata for just this video** (jq):
   ```bash
   bash .claude/skills/extract-video-meta/scripts/extract-meta.sh "video-injest/download-video/<Title>"
   ```

3. **Precondition guard — required before any delete.** Confirm the folder now
   holds all three inputs: `<Title>.srt`, `<Title>.meta.json`, and `<Title>.jpg`.
   If **any** is missing (e.g. a video that failed to download has no `.mp3`, so
   transcribe produced no `.srt`), an upstream step failed for this video — **skip
   it, do NOT delete the folder**, mark it `❌` in the checklist as a leftover
   needing a retry, and move to the next video.

4. **Prepare the mechanical note parts:**
   ```bash
   bash .claude/skills/build-ark-note/scripts/prepare-note.sh "video-injest/download-video/<Title>"
   ```
   Read back `NOTE_PATH=...` and the block between the `FRONTMATTER` markers.

5. **Write the note** at `NOTE_PATH`: the frontmatter block verbatim, then the
   authored summary body below the `---` divider. **Author the body** from the
   `.srt` following **CLAUDE.md §1** (Hook & Core Thesis → Key Arguments by
   importance → High-Yield Assets kept specific → Case Studies → "So What?"),
   matching the prose of existing notes in `Ark/Learning/05` and `06`, with
   `[[wiki-links]]` on key concepts and named people. The `meta.json` `topic`
   is the `__INFER__` sentinel — infer it from the categories already used in
   `Ark/Learning` (e.g. Health, Investment, Habit, Charisma). **Zero
   hallucination** — write `[Transcript Unclear at this point]` rather than guess.

6. **Mark this video done — only after the note is written:**
   ```bash
   rm -rf "video-injest/download-video/<Title>"
   ```
   Update the checklist (`✅` + note filename) and reprint it.

### Visual progress indicator

Maintain and **reprint a checklist after every video** so overall progress is
always visible. One line per video with a status icon, plus a `k/N done` counter:

- `✅` done (show the note filename it produced)
- `⏳` in progress (transcribing / authoring)
- `⬜` pending
- `❌` left behind (failed the stage-3 guard — needs a retry)

```
Processing playlist — 12 videos
✅ 1. 8 Foods I Eat EVERY DAY as an ER Doctor    → 29-06-2026-16.md
✅ 2. Stop Walking 10,000 Steps a Day            → 29-06-2026-17.md
⏳ 3. I Wore An Apple Watch, Oura, Whoop…        (transcribing)
⬜ 4. …
2/12 done
```

(Optionally also back this with the harness Task tools — one task per video, set
`in_progress`/`completed` — for a live UI checklist. The printed checklist is the
required, always-works mechanism.)

## Finish

- Verify nothing is left: `find video-injest/download-video -mindepth 1 -type d` returns
  nothing. (A stray `.DS_Store` file is harmless and ignored by every loop;
  remove it if you want the folder truly empty.)
- Report: how many notes were created and where, plus any folders deliberately
  left behind (`❌`, failed the guard) and why.

## Partial-failure behavior (expected, not a bug)

A video that fails to download lacks the `.mp3` that transcribe needs, so it has no
`.srt` and fails the stage-3 guard — its folder is **left in place** for a retry
rather than deleted. "Nothing left in `video-injest/download-video/`" holds for the all-success
case; a surviving folder is the explicit signal of which video needs another pass.
Just re-run this skill — `download.sh` skips already-downloaded files, and the
per-video loop simply never sees the videos whose folders were already removed.

**If *every* folder is missing its `.mp3`, that is not a partial failure** — it is
the stage-1 backgrounding bug (see the warning in Stage 1). Re-run the download in
the foreground before entering the per-video loop, rather than letting all N videos
fail the stage-3 guard one by one.
