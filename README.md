# YAAT
This is my knowledge collector, it collection information for various sources and produces content - Blog and Podcast.

## Skills

### download.sh — stage 1 of process-video (not a standalone skill)
give it a youTube playlist, this script will download all videos listed in that playlist, the playlist must set to Public for this script to work. It lives at `.claude/skills/process-video/scripts/download.sh` and runs as the first stage of `/process-video`. **Run it in the foreground** — backgrounding it makes every video fail with HTTP 403 while still exiting 0 (see CLAUDE.md §4).

### transcribe-audio
this skill will take a mp3 formatted audio trasck as input, it then transcribes the entire track. the output is saved as srt file.

### extract-video-meta
this skill will analyse the .info.json file that the download stage generates, it will then extract requested information from the file, it produces .meta.json as output.

### build-ark-note
this skll creates a Obsidian note, it consists 2 main parts, heder and main body. where header fields list important meta information, while main body contains the transcribed text of the video.

### process-video
this skill is the initiator. it runs its own download stage (scripts/download.sh) and then orchestrates these skills - transcribe-audio extract-video-meta build-ark-note.
```
/process-video
```

### produce-blog
this skill reads reference file in folder blog-factory, it will use referenced notes as study guide, it will study it, draws own conclusion, then does own research, find support, then create a blog in Markdown format, save it in the same folder.
```
/produce-blog
```