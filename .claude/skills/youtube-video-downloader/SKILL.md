---
name: youtube-video-downloader
description: >
  Download audio tracks and metadata from YouTube playlists listed in a JSON
  file. Use when the user says "download YouTube playlists", "fetch audio from
  YouTube", "bulk download playlists", or refers to a JSON file of YouTube URLs.
  Reads an array of playlist URLs, downloads each video's audio as MP3, and
  saves JSON metadata alongside it. Triggers on any request to process a
  playlist JSON file, extract audio from YouTube, or automate YouTube downloads.
---

# YouTube Playlist Downloader

## Steps

1. Read the JSON file passed as the argument (default: `video.json`) to get the list of playlist URLs.
2. For each playlist URL, run a single `yt-dlp` pass against the playlist. yt-dlp expands the playlist and downloads every video in it:
   - Extract audio as MP3 at best quality (`--extract-audio --audio-format mp3 --audio-quality 0`)
   - Save info JSON sidecar (`--write-info-json`)
   - Download the video thumbnail and convert it to JPEG (`--write-thumbnail --convert-thumbnails jpg`)
   - Suppress playlist-level metadata with `--no-write-playlist-metafiles` so yt-dlp does **not** create a stray folder holding the playlist's own `info.json`/thumbnail. Only per-video folders should be produced.
   - Output each video into its own folder (named after the title) nested inside a single parent folder `download-video`, with files inside named the same:
     ```
     --output "download-video/%(title)s/%(title)s.%(ext)s"
     ```
   - This produces a structure like:
     ```
     download-video/
     ├── Song Title/
     │   ├── Song Title.mp3
     │   ├── Song Title.info.json
     │   └── Song Title.jpg
     └── Another Song/
         └── ...
     ```
3. All output goes into the `download-video/` folder in the current working directory.
4. Report how many videos were downloaded when done.

## Command

**Download every video in a playlist (one resilient pass):**
```bash
yt-dlp \
  --extract-audio \
  --audio-format mp3 \
  --audio-quality 0 \
  --write-info-json \
  --write-thumbnail \
  --convert-thumbnails jpg \
  --no-write-playlist-metafiles \
  --output "download-video/%(title)s/%(title)s.%(ext)s" \
  "<PLAYLIST_URL>"
```

`--no-write-playlist-metafiles` is what prevents the extra playlist-named folder (containing only the playlist's `info.json` and thumbnail) from being created alongside the per-video folders.