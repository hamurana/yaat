#!/usr/bin/env python3
"""
adapt-post.py — mechanical NCW adaptation of one produce-blog output post.

Given a path/slug identifying a blog-factory/output/<slug>/index.md file, this
script, in place:
  1. Removes the `sources:` block from the frontmatter.
  2. Extracts the post's first body paragraph (the executive summary — skipping
     a leading H1 title line if present) and adds it as a new `description:`
     frontmatter field.
  3. Wraps that same paragraph in the body with {{< lead >}} / {{< /lead >}}.
  4. If --tags is given, adds a `tags:` frontmatter field (a YAML list) from
     the supplied comma-separated tag values. Tag *selection* is a judgment
     call made by whoever invokes this script (read the full post, decide up
     to 5 representative tags) — this script only performs the mechanical
     frontmatter insertion.
  5. Adds `draft: true` to the frontmatter, so an adapted post lands unpublished
     and has to be promoted deliberately.

Each of the five steps is independently idempotent: already-present pieces
(an existing description:, an existing {{< lead >}} wrap, an existing tags:
field, an existing draft: value, an absent sources: block) are left untouched
and reported as such, so the script is safe to re-run and safe to use to
backfill just one missing piece (e.g. add tags: to a post already adapted
before this field existed). Note that an existing `draft: false` is therefore
preserved — re-running never un-publishes a post you have already promoted.

Usage:
  python3 adapt-post.py <slug|folder|path/to/index.md> [--tags "Tag One, Tag Two, Tag Three"]
"""
import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
OUTPUT_ROOT = REPO_ROOT / "blog-factory" / "output"
LEAD_OPEN = "{{< lead >}}"
LEAD_CLOSE = "{{< /lead >}}"


def resolve_path(arg: str) -> Path:
    p = Path(arg)
    candidates = []
    if p.is_absolute():
        candidates.append(p)
    else:
        candidates.append(REPO_ROOT / p)
        candidates.append(Path(arg))
    # allow bare slug
    candidates.append(OUTPUT_ROOT / arg)

    for c in candidates:
        if c.is_file() and c.name == "index.md":
            return c
        if c.is_dir() and (c / "index.md").is_file():
            return c / "index.md"
        if c.is_file() and c.suffix == ".md":
            return c

    available = sorted(d.name for d in OUTPUT_ROOT.iterdir() if d.is_dir()) if OUTPUT_ROOT.is_dir() else []
    raise SystemExit(
        f"Could not resolve '{arg}' to a post under {OUTPUT_ROOT}.\n"
        f"Available slugs: {', '.join(available) if available else '(none found)'}"
    )


def split_frontmatter(text: str):
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        raise SystemExit("File does not start with a '---' frontmatter block.")
    lines = text.splitlines(keepends=True)
    close_idx = None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n") == "---":
            close_idx = i
            break
    if close_idx is None:
        raise SystemExit("Could not find closing '---' for frontmatter block.")
    front_lines = lines[1:close_idx]
    body_lines = lines[close_idx + 1:]
    return front_lines, body_lines


def has_key(front_lines, key):
    return any(re.match(rf"^{re.escape(key)}:\s*", l) for l in front_lines)


def remove_key_block(front_lines, key):
    out = []
    i = 0
    removed = False
    while i < len(front_lines):
        line = front_lines[i]
        if re.match(rf"^{re.escape(key)}:\s*$", line) or re.match(rf"^{re.escape(key)}:\s*\[.*\]\s*$", line):
            removed = True
            i += 1
            while i < len(front_lines) and (front_lines[i].startswith(" ") or front_lines[i].startswith("\t") or front_lines[i].strip() == ""):
                if front_lines[i].strip() == "":
                    j = i + 1
                    while j < len(front_lines) and front_lines[j].strip() == "":
                        j += 1
                    if j < len(front_lines) and not (front_lines[j].startswith(" ") or front_lines[j].startswith("\t")):
                        break
                i += 1
            continue
        out.append(line)
        i += 1
    return out, removed


def find_existing_lead(body_lines):
    for i, line in enumerate(body_lines):
        if line.strip() == LEAD_OPEN:
            j = i + 1
            para_lines = []
            while j < len(body_lines) and body_lines[j].strip() != LEAD_CLOSE:
                para_lines.append(body_lines[j])
                j += 1
            return " ".join(l.strip() for l in para_lines if l.strip())
    return None


def extract_lead_paragraph(body_lines):
    i = 0
    n = len(body_lines)

    def is_blank(line):
        return line.strip() == ""

    while i < n and is_blank(body_lines[i]):
        i += 1

    if i < n and re.match(r"^#\s+\S", body_lines[i]):
        i += 1
        while i < n and is_blank(body_lines[i]):
            i += 1

    start = i
    while i < n and not is_blank(body_lines[i]):
        i += 1
    end = i

    if start >= end:
        raise SystemExit("Could not find a first body paragraph to use as the executive summary.")

    para_lines = body_lines[start:end]
    para_text = " ".join(line.strip() for line in para_lines)
    return start, end, para_text


def yaml_quote(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def yaml_scalar(text: str) -> str:
    if re.search(r'[:#"\[\]{}]|^[\s\-\'>|*&!%@`]|\s$', text) or text == "":
        return yaml_quote(text)
    return text


def parse_tags(raw: str):
    tags = [t.strip() for t in raw.split(",")]
    tags = [t for t in tags if t]
    if len(tags) > 5:
        raise SystemExit(f"--tags gave {len(tags)} tags, max is 5: {tags}")
    return tags


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    parser.add_argument("--tags", default=None, help="Comma-separated tag values (max 5)")
    args = parser.parse_args()

    path = resolve_path(args.target)
    text = path.read_text(encoding="utf-8")
    front_lines, body_lines = split_frontmatter(text)

    report = []

    front_lines, removed_sources = remove_key_block(front_lines, "sources")
    report.append(f"sources removed: {removed_sources}")

    existing_lead_text = find_existing_lead(body_lines)
    already_wrapped = existing_lead_text is not None

    if already_wrapped:
        para_text = existing_lead_text
        new_body = body_lines
        report.append("lead wrap: already present")
    else:
        start, end, para_text = extract_lead_paragraph(body_lines)
        new_body = (
            body_lines[:start]
            + [f"{LEAD_OPEN}\n", "".join(body_lines[start:end]), f"{LEAD_CLOSE}\n"]
            + body_lines[end:]
        )
        report.append("lead wrap: added")

    if has_key(front_lines, "description"):
        report.append("description: already present")
    else:
        front_lines.append(f"description: {yaml_quote(para_text)}\n")
        report.append(f"description: added ({len(para_text)} chars)")

    if has_key(front_lines, "tags"):
        report.append("tags: already present")
    elif args.tags:
        tags = parse_tags(args.tags)
        if not tags:
            report.append("tags: --tags given but empty after parsing, skipped")
        else:
            front_lines.append("tags:\n")
            for t in tags:
                front_lines.append(f"  - {yaml_scalar(t)}\n")
            report.append(f"tags: added ({', '.join(tags)})")
    else:
        report.append("tags: not provided, skipped")

    if has_key(front_lines, "draft"):
        report.append("draft: already present")
    else:
        front_lines.append("draft: true\n")
        report.append("draft: added (true)")

    new_text = "---\n" + "".join(front_lines) + "---\n" + "".join(new_body)

    if new_text == text:
        print(f"Already fully adapted — no changes made: {path}")
        return

    path.write_text(new_text, encoding="utf-8")

    print(f"Adapted: {path}")
    for line in report:
        print(f"  {line}")


if __name__ == "__main__":
    main()
