you need ro learn a new skill, extract video meta,

1. for each subfolder within download-video folder, 
2. use jq to extract meta info from the .info.json for that specific video with in the subfolder.
3. save the output as [video name].meta.json
4. the output file is a json file, it will have following format:
    - field name: published date, the value is derived from step 2.
    - field name: title, the value is derived from step 2.
    - field name: channel, the value is derived from step 2.
    - field name: watch date, this is today's system date.
    - field name: category, this is derived from step 2.
    - field name: origin, this is derived from step 2.
5. repeat this process for all subfolders under download-video folder.