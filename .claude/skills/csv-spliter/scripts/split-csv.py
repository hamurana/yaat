#!/usr/bin/env python3
"""
split-csv.py — split a blog-factory CSV manifest into fixed-size chunk files.

Given a rows-per-file count (1, 2 or 3) and an input CSV, this script writes
N smaller CSVs into blog-factory/output/<Topic>/, where <Topic> is the input
file's basename. Every chunk repeats the source header row verbatim, so each
output file is a valid standalone manifest.

  blog-factory/Investment.csv  (40 data rows, chunk size 3)
    -> blog-factory/output/Investment/Investment-01.csv   rows  1-3
       blog-factory/output/Investment/Investment-02.csv   rows  4-6
       ...
       blog-factory/output/Investment/Investment-14.csv   row  40   <- remainder

REMAINDER
  Chunks are cut in source order and the last file simply holds whatever is
  left over (row_total % rows_per_file rows, when that is non-zero). Nothing
  is padded, dropped, or redistributed to even the files out.

WHY THE csv MODULE
  Manifest `title` fields routinely contain commas and are already quoted, and
  batches have included CJK text. Shell text-slicing (cut/awk) corrupts both;
  csv.reader/csv.writer round-trip them correctly. All I/O is utf-8, and the
  split is verified by reassembling the chunks and comparing against the rows
  actually read from the source.

SAFETY
  The source CSV is never modified. If any target file already exists the run
  aborts before writing anything, unless --force is passed. Use --dry-run to
  see the planned split without touching disk.

Usage:
  python3 split-csv.py <1|2|3> <input.csv> [--force] [--dry-run]
"""

import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
BLOG_FACTORY = REPO_ROOT / "blog-factory"
OUTPUT_ROOT = BLOG_FACTORY / "output"

ALLOWED_CHUNK_SIZES = (1, 2, 3)


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def resolve_input(arg):
    """Resolve the input CSV argument to a real file.

    Accepts a bare name with or without the .csv extension ('Investment',
    'Investment.csv'), a path relative to blog-factory/, or a path relative to
    the repo root / an absolute path.
    """
    names = [arg] if arg.lower().endswith(".csv") else [arg + ".csv", arg]
    candidates = []
    for name in names:
        p = Path(name)
        if p.is_absolute():
            candidates.append(p)
        else:
            candidates.append(BLOG_FACTORY / name)
            candidates.append(REPO_ROOT / name)
            candidates.append(Path.cwd() / name)

    for c in candidates:
        if c.is_file():
            return c.resolve()

    available = sorted(p.name for p in BLOG_FACTORY.glob("*.csv")) if BLOG_FACTORY.is_dir() else []
    listing = "\n  ".join(available) if available else "(none)"
    die(
        f"Could not resolve '{arg}' to a CSV file.\n"
        f"Looked in {BLOG_FACTORY}, {REPO_ROOT}, and the current directory.\n"
        f"CSVs present in blog-factory/:\n  {listing}"
    )


def read_csv(path):
    """Return (header, rows). Blank rows are dropped; ragged rows are reported."""
    with path.open(newline="", encoding="utf-8") as fh:
        records = list(csv.reader(fh))

    if not records:
        die(f"{path} is empty — no header row to replicate.")

    header, body = records[0], records[1:]
    rows = [r for r in body if any(field.strip() for field in r)]

    ragged = [
        (i, len(r))
        for i, r in enumerate(rows, start=2)
        if len(r) != len(header)
    ]
    return header, rows, ragged


def main():
    parser = argparse.ArgumentParser(
        description="Split a blog-factory CSV into fixed-size chunks under output/<Topic>/.",
    )
    parser.add_argument(
        "rows_per_file",
        help="Rows of data per output file. One of: 1, 2, 3.",
    )
    parser.add_argument("input_csv", help="Input CSV (bare name, or a path).")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output files instead of aborting.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report the planned split without writing anything.",
    )
    args = parser.parse_args()

    # --- validate rows_per_file --------------------------------------------
    try:
        chunk_size = int(args.rows_per_file)
    except ValueError:
        die(
            f"rows_per_file must be an integer, got '{args.rows_per_file}'. "
            f"Allowed values: {', '.join(map(str, ALLOWED_CHUNK_SIZES))}."
        )
    if chunk_size not in ALLOWED_CHUNK_SIZES:
        die(
            f"rows_per_file must be one of {', '.join(map(str, ALLOWED_CHUNK_SIZES))}, "
            f"got {chunk_size}."
        )

    # --- read source --------------------------------------------------------
    src = resolve_input(args.input_csv)
    header, rows, ragged = read_csv(src)

    if not rows:
        die(f"{src.name} has a header but no data rows — nothing to split.")

    topic = src.stem
    stem = src.stem
    out_dir = OUTPUT_ROOT / topic

    # --- plan the split -----------------------------------------------------
    chunks = [rows[i:i + chunk_size] for i in range(0, len(rows), chunk_size)]
    width = max(2, len(str(len(chunks))))
    targets = [out_dir / f"{stem}-{i:0{width}d}.csv" for i in range(1, len(chunks) + 1)]

    remainder = len(rows) % chunk_size

    print(f"source        : {src.relative_to(REPO_ROOT)}")
    print(f"header        : {','.join(header)}")
    print(f"data rows     : {len(rows)}")
    print(f"rows per file : {chunk_size}")
    print(f"output files  : {len(chunks)}"
          + (f" (last file holds the remainder: {remainder} row{'s' if remainder != 1 else ''})"
             if remainder else " (divides evenly, no remainder)"))
    print(f"destination   : {out_dir.relative_to(REPO_ROOT)}/{stem}-{'0' * width}.csv")

    if ragged:
        print(f"\nWARNING: {len(ragged)} row(s) have a field count differing from the "
              f"{len(header)}-column header — these are written through unchanged, but "
              f"check the source for a missing line break:")
        for line_no, count in ragged[:10]:
            print(f"  source line ~{line_no}: {count} fields")
        if len(ragged) > 10:
            print(f"  ... and {len(ragged) - 10} more")

    # --- collision check ----------------------------------------------------
    existing = [t for t in targets if t.exists()]
    if existing and not args.force:
        listed = "\n  ".join(str(t.relative_to(REPO_ROOT)) for t in existing[:10])
        more = f"\n  ... and {len(existing) - 10} more" if len(existing) > 10 else ""
        die(
            f"\n{len(existing)} target file(s) already exist. Nothing was written.\n"
            f"  {listed}{more}\n"
            f"Re-run with --force to overwrite, or clear the folder first."
        )

    stale = []
    if out_dir.is_dir():
        planned = {t.name for t in targets}
        stale = sorted(p for p in out_dir.glob(f"{stem}-*.csv") if p.name not in planned)

    if args.dry_run:
        print("\n[dry run] planned files:")
        for t, c in zip(targets, chunks):
            print(f"  {t.relative_to(REPO_ROOT)}  ({len(c)} row{'s' if len(c) != 1 else ''})")
        if stale:
            print("\n[dry run] pre-existing files matching the pattern that this run "
                  "would NOT overwrite (left in place — delete them if they are from "
                  "an earlier split at a different chunk size):")
            for p in stale:
                print(f"  {p.relative_to(REPO_ROOT)}")
        return

    # --- write --------------------------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)
    for target, chunk in zip(targets, chunks):
        with target.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(chunk)

    # --- verify by round-trip ----------------------------------------------
    reassembled = []
    problems = []
    for target in targets:
        with target.open(newline="", encoding="utf-8") as fh:
            records = list(csv.reader(fh))
        if not records or records[0] != header:
            problems.append(f"{target.name}: header row missing or altered")
            continue
        reassembled.extend(records[1:])

    if reassembled != rows:
        problems.append(
            f"round-trip mismatch: read {len(rows)} rows from the source, "
            f"recovered {len(reassembled)} from the chunks"
        )

    print()
    for target, chunk in zip(targets, chunks):
        print(f"wrote {target.relative_to(REPO_ROOT)}  "
              f"({len(chunk)} row{'s' if len(chunk) != 1 else ''})")

    if stale:
        print("\nNOTE: these pre-existing files match the naming pattern but were not "
              "part of this run — they are probably left over from an earlier split at "
              "a different chunk size:")
        for p in stale:
            print(f"  {p.relative_to(REPO_ROOT)}")

    if problems:
        print("\nVERIFICATION FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        sys.exit(1)

    print(f"\nOK: {len(rows)} data rows -> {len(chunks)} files, "
          f"header replicated in each, round-trip verified.")
    print(f"Source {src.name} left untouched.")


if __name__ == "__main__":
    main()
