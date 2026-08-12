---
name: csv-spliter
description: Split a blog-factory CSV manifest into fixed-size chunk files of 1, 2 or 3 rows each, written to blog-factory/output/<Topic>/ with the header replicated into every chunk so each one is a valid standalone manifest. Invoke as "/csv-spliter <1|2|3> <csv>", e.g. "/csv-spliter 1 Investment". Use whenever the user wants to split a CSV manifest, break a batch CSV into one-row (or two- or three-row) manifests, turn one big manifest into per-note manifests, or prepare a manifest folder for a per-post produce-blog run. Triggers on phrases like "split the csv", "split Investment.csv into single rows", "chunk the manifest", "one row per file", or any request to cut a blog-factory CSV into smaller manifests.
---

# CSV Spliter

Cuts one `blog-factory/` CSV manifest into N smaller CSVs, each holding a fixed
number of data rows and a verbatim copy of the source header. Every chunk is
therefore a valid standalone manifest that `produce-blog` can consume on its own.

This is the step that turns a single synthesized batch post into a set of
focused, smaller-source posts — the manual procedure described in CLAUDE.md §8,
automated.

## Invocation

`/csv-spliter <rows_per_file> <csv>` — two required parameters.

- **`rows_per_file`** — `1`, `2`, or `3`. Anything else is rejected. One row per
  file is the common case (one post per Ark note).
- **`csv`** — the source manifest. Accepts a bare name with or without the
  extension (`Investment`, `Investment.csv`), a path relative to
  `blog-factory/`, or a repo-relative or absolute path. If it doesn't resolve,
  the script lists the CSVs actually present in `blog-factory/` — surface that
  list rather than guessing.

If either parameter is missing, ask for it. Guessing a chunk size writes the
wrong number of files, and guessing a manifest writes the wrong batch entirely.

```bash
python3 .claude/skills/csv-spliter/scripts/split-csv.py <1|2|3> <csv> [--dry-run] [--force]
```

**Run `--dry-run` first** on anything you haven't split before. It prints the
full planned file list and touches nothing.

## Output layout

Chunks land in `blog-factory/output/<Topic>/`, where `<Topic>` is the source
file's basename. The folder is reused if it already exists and created if it
doesn't.

```
blog-factory/Investment.csv   (40 data rows, rows_per_file = 3)
  -> blog-factory/output/Investment/Investment-01.csv    rows  1-3
     blog-factory/output/Investment/Investment-02.csv    rows  4-6
     ...
     blog-factory/output/Investment/Investment-14.csv    row  40   <- remainder
```

Files are numbered from `01`, zero-padded to at least two digits (wider if the
split produces 100+ files), so they sort correctly.

Note that `blog-factory/output/<Topic>/` is also where `produce-blog` writes its
finished posts, as `<slug>/index.md` subfolders. Manifests and post folders
coexist there — **scope any sweep to `*.csv`** so it doesn't pick up post
directories.

## Remainder handling

Chunks are cut in source order and the last file simply holds whatever is left
over (`row_total % rows_per_file` rows, when non-zero). Nothing is padded,
dropped, or redistributed to even the files out. The run reports the remainder
explicitly.

## Safety properties

- **The source CSV is never modified.** It stays where it is after the split;
  removing it, if that's wanted, is a separate deliberate act.
- **Existing targets abort the run before anything is written.** The script
  lists what it would have clobbered and exits non-zero. `--force` overwrites.
- **Stale files are reported, not deleted.** Files matching `<Topic>-*.csv` that
  aren't part of this run — typically left over from an earlier split at a
  different chunk size — are listed at the end so you can clear them. The script
  won't remove them for you.
- **The split is verified by round-trip.** After writing, every chunk is read
  back, its header checked against the source header, and the reassembled rows
  compared against the rows actually read in. A mismatch fails the run loudly.
- **Ragged rows are flagged.** Any row whose field count differs from the header
  is written through unchanged but reported — that's usually the missing-newline
  corruption from CLAUDE.md §8, where two rows ran together. Check the source
  before trusting the output.

## Why it's a Python script and not shell

Manifest `title` fields routinely contain commas and are already quoted, and
past batches have included CJK text. `cut`/`awk` corrupt both; `csv.reader` and
`csv.writer` round-trip them correctly. All I/O is explicitly UTF-8. Never
hand-roll this split in shell.

## What this skill does not do

- **No dedup.** It doesn't check for duplicate `name` values, and it doesn't
  check whether several rows point at the same underlying video via their notes'
  `origin link`. With `<Topic>-NN` numbering, duplicate names can't collide on a
  filename, so they pass through silently. Run the §8 duplicate-source check
  separately before authoring.
- **No note resolution.** It never opens `Ark/Learning/`, so a row naming a note
  that doesn't exist splits cleanly and only fails later. Pre-flight the note
  paths before producing posts.
- **No blog production.** Splitting is where this skill stops.

## After the split

The chunk folder is what you hand to `produce-blog`. Passing a folder where a
single CSV is expected means *one post per file* — the established convention
across these skills:

```
/produce-blog <profile> blog-factory/output/<Topic>
```

Confirm the post count with the user before that step when the split produced
many files. Forty manifests means forty posts, which is expensive to get wrong.

## Reporting

Relay the script's summary: source file, data row count, rows per file, number
of chunks written, whether there was a remainder, and the destination folder.
Surface any ragged-row or stale-file warnings verbatim — both mean something
about the source or the folder needs a human look.
