---
name: build-ark-note
description: Turn each processed video in download-video/ into a curated Obsidian note in the Ark Learning vault, with its thumbnail wired up, then delete the source folder. Use whenever the user wants to build Ark notes, create the Obsidian/Learning note for a video, add a downloaded video to the knowledge base, summarise the transcript into Ark, or finish the pipeline after transcription and metadata extraction. Triggers on phrases like "build the Ark note", "add this video to Ark", "create the Learning note", "process the download-video folder into the vault", or "summarise these into the knowledge base".
---

# Build Ark Note

Final stage of the pipeline. For every video folder under `download-video/`, this
skill produces one clean Obsidian note in the **Ark** vault (`Ark/Learning/`),
copies the thumbnail into the vault, then deletes the source folder so
`download-video/` only ever holds unprocessed work.

This runs **after** `transcribe-audio` (makes the `.srt`) and `extract-video-meta`
(makes the `.meta.json`).

## Layout this skill expects

```
download-video/
  <Title>/
    <Title>.jpg        <- thumbnail (input)
    <Title>.srt        <- transcript, summarised into the note body (input)
    <Title>.meta.json  <- trimmed metadata (input)
    <Title>.mp3        <- audio (ignored)
    <Title>.info.json  <- raw yt-dlp metadata (ignored)
```

`.meta.json` fields (from `extract-video-meta`): `title`, `channel`, `category`,
`origin`, `published date`, `watch date`.

## Output: one note per video

Path: `Ark/Learning/<MM>/<DD-MM-YYYY>-<N>.md`
- `<MM>` and `<DD-MM-YYYY>` come from the **watch date** (`YYYY-MM-DD`).
- `<N>` is the next free sequence number for that date — three videos watched on
  19-06-2026 become `19-06-2026-1.md`, `-2.md`, `-3.md`.

Note shape (match the existing notes in `Ark/Learning/05` and `06`):

```
---
title: <meta title>
topic:
  - <meta category>
channel: <meta channel>
origin link: <meta origin>
publish date: <meta published date>
watch date: <meta watch date>
---
![[<videoId>.jpg]]

---
<summary body>
```

- `<videoId>` = the `v=` value of the origin URL (also `id` in `.info.json`).
- `![[<videoId>.jpg]]` is an Obsidian filename-only embed; it resolves anywhere in
  the vault, so the thumbnail folder name does not matter to the link.

## Thumbnail

Copy `<Title>.jpg` → `Ark/Misc/Thnmbnails/<videoId>.jpg`. Use that **existing**
folder (the spelling "Thnmbnails" is intentional — all current thumbnails live
there; do not create a second folder).

## How to run it — per video, in order

For each `download-video/<Title>/` folder, one at a time:

1. **Prepare** the mechanical parts with the helper. It copies the thumbnail,
   computes the note path, and prints the frontmatter + embed header:
   ```bash
   bash .claude/skills/build-ark-note/scripts/prepare-note.sh "download-video/<Title>"
   ```
   Read back `NOTE_PATH=...` and the block between the `FRONTMATTER` markers.

2. **Read the `.srt`** and write the note at `NOTE_PATH`: the frontmatter block from
   step 1 verbatim, then the authored summary body below the `---` divider.

3. **Author the body** from the transcript following the Section 1 rules in
   `.claude/CLAUDE.md` and matching the prose style of existing notes:
   - bold section headers (`**...**`), `---` dividers between major sections;
   - lead with the hook / core thesis, then key arguments by importance;
   - keep **High-Yield Assets** specific — exact names, numbers, book/tool/framework
     names, studies, quotes. Never generalise ("85% of top TED Talks", not "most");
   - summarise case studies / anecdotes the speaker tells;
   - close with the actionable "so what";
   - add `[[wiki-links]]` on key concepts and named people so the graph connects.
   - **Zero hallucination**: if a transcript segment is garbled, write
     `[Transcript Unclear at this point]` — do not guess. Note any mismatch between
     the title's claim and the actual content rather than inventing to fit.

4. **Delete** the source folder only after the note is written:
   ```bash
   rm -rf "download-video/<Title>"
   ```

When all folders are done, report: how many notes were created, where, and confirm
`download-video/` is empty.
