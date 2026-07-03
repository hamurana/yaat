# YAAT
This is my knowledge collector, it collection information for various sources and produces content - Blog and Podcast.

## Skills

### youtube-video-downloader
give it a youTube playlist, this skill will download all videos listed in that playlist, the playlist must set to Public for this script to work.

### transcribe-audio
this skill will take a mp3 formatted audio trasck as input, it then transcribes the entire track. the output is saved as srt file.

### extract-video-meta
this skill will analyse the meta.json file that skill /youtube-video-downloader generates, it will then extract requested information from the file, it produces .meta.json as output.

### build-ark-note
this skll creates a Obsidian note, it consists 2 main parts, heder and main body. where header fields list important meta information, while main body contains the transcribed text of the video.

### process-video
this skill orchestrates these skills - youtube-video-downloader trajnscribe-audio extract-video-meta build-ark-note, this skill is the  initiator.
```
/process-video
```

### produce-blog
this skill reads reference file in folder blog-factory, it will use referenced notes as study guide, it will study it, draws own conclusion, then does own research, find support, then create a blog in Markdown format, save it in the same folder.
```
/produce-blog
```