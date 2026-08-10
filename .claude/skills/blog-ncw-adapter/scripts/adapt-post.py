#!/usr/bin/env python3
"""
adapt-post.py — mechanical NCW adaptation of produce-blog output posts.

Given a path/slug identifying a blog-factory/output/<slug>/index.md file — or a
FOLDER containing many such posts — this script, in place:
  1. Removes the `sources:` block from the frontmatter.
  2. Extracts the post's first body paragraph (the executive summary — skipping
     a leading H1 title line if present) and adds it as a new `description:`
     frontmatter field.
  3. Wraps that same paragraph in the body with {{< lead >}} / {{< /lead >}}.
  4. If tags are supplied, adds a `tags:` frontmatter field (a YAML list). Tag
     *selection* is a judgment call made by whoever invokes this script (read
     the whole post and its context, decide up to 5 representative tags) —
     this script only performs the mechanical frontmatter insertion.
  5. Sets `date:` to a date drawn from January–May of the current year, with
     weekday frequency decreasing from Monday to Sunday (see below).
  6. Adds `draft: false`, so an adapted post lands published.

Each step is independently idempotent: already-present pieces (an existing
description:, an existing {{< lead >}} wrap, an existing tags: field, an
existing draft: value, an absent sources: block) are left untouched and
reported as such. The script is therefore safe to re-run and safe for
backfilling a single missing piece.

Note that `draft:` and `date:` are PRESENCE-checked, not value-checked. Once a
post carries one, the script never rewrites it — so a deliberately held-back
`draft: true`, or a date you set by hand, both survive any number of re-runs.
Use --force-date / --force-draft to overwrite them anyway.

DATE DISTRIBUTION
  Dates are drawn from 1 January to 31 May of the current year, weighted so
  Monday is most common and Sunday least (weights 7,6,5,4,3,2,1).
    * FOLDER MODE allocates weekday counts deterministically across the batch
      (largest-remainder), so the Mon->Sun decrease is GUARANTEED to hold in
      the resulting posts rather than merely being likely.
    * SINGLE-POST MODE draws one weighted-random date. With n=1 no
      distribution can be guaranteed; running the script post-by-post over a
      batch will approximate the shape but may inconsistently invert in the
      tail. Prefer folder mode for batches.

FOLDER MODE
  If the target is a directory that does not itself contain an index.md, every
  immediate subdirectory containing an index.md is treated as a post.
  Because tags are a per-post judgment, --tags is rejected in folder mode.
  Supply --tags-file instead: a TSV of `slug<TAB>Tag One, Tag Two, ...`.
  Without it, folder mode applies everything except tags and reports which
  posts still need them.

Usage:
  python3 adapt-post.py <slug|folder|path/to/index.md> [--tags "A, B, C"]
  python3 adapt-post.py <folder-of-posts> [--tags-file tags.tsv] [--seed N]
"""
import argparse
import datetime
import random
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
OUTPUT_ROOT = REPO_ROOT / "blog-factory" / "output"
LEAD_OPEN = "{{< lead >}}"
LEAD_CLOSE = "{{< /lead >}}"

# Monday .. Sunday. Must be non-increasing for the required frequency shape.
WEEKDAY_WEIGHTS = [7, 6, 5, 4, 3, 2, 1]
DATE_MONTHS = (1, 5)  # January through May inclusive


# ---------------------------------------------------------------- resolution

def _is_post_dir(p: Path) -> bool:
    return p.is_dir() and (p / "index.md").is_file()


def resolve_target(arg: str):
    """Return (kind, value) where kind is 'post' (Path to index.md) or
    'batch' (sorted list of index.md Paths)."""
    p = Path(arg)
    candidates = []
    if p.is_absolute():
        candidates.append(p)
    else:
        candidates.append(REPO_ROOT / p)
        candidates.append(Path(arg))
    candidates.append(OUTPUT_ROOT / arg)  # allow bare slug

    for c in candidates:
        if c.is_file() and c.name == "index.md":
            return "post", c
        if _is_post_dir(c):
            return "post", c / "index.md"
        if c.is_dir():
            posts = sorted(d / "index.md" for d in c.iterdir() if _is_post_dir(d))
            if posts:
                return "batch", posts
        if c.is_file() and c.suffix == ".md":
            return "post", c

    available = sorted(d.name for d in OUTPUT_ROOT.iterdir() if d.is_dir()) if OUTPUT_ROOT.is_dir() else []
    raise SystemExit(
        f"Could not resolve '{arg}' to a post or folder of posts under {OUTPUT_ROOT}.\n"
        f"Available slugs: {', '.join(available) if available else '(none found)'}"
    )


# --------------------------------------------------------------- frontmatter

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
    return lines[1:close_idx], lines[close_idx + 1:]


def has_key(front_lines, key):
    return any(re.match(rf"^{re.escape(key)}:\s*", l) for l in front_lines)


def set_key(front_lines, key, value):
    """Replace an existing top-level key's line, or append it. Returns True if
    an existing line was replaced."""
    for i, l in enumerate(front_lines):
        if re.match(rf"^{re.escape(key)}:\s*", l):
            front_lines[i] = f"{key}: {value}\n"
            return True
    front_lines.append(f"{key}: {value}\n")
    return False


def remove_key_block(front_lines, key):
    out, i, removed = [], 0, False
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


# ---------------------------------------------------------------------- body

def find_existing_lead(body_lines):
    for i, line in enumerate(body_lines):
        if line.strip() == LEAD_OPEN:
            j = i + 1
            para = []
            while j < len(body_lines) and body_lines[j].strip() != LEAD_CLOSE:
                para.append(body_lines[j])
                j += 1
            return " ".join(l.strip() for l in para if l.strip())
    return None


def extract_lead_paragraph(body_lines):
    i, n = 0, len(body_lines)
    blank = lambda l: l.strip() == ""
    while i < n and blank(body_lines[i]):
        i += 1
    if i < n and re.match(r"^#\s+\S", body_lines[i]):   # skip a leading H1
        i += 1
        while i < n and blank(body_lines[i]):
            i += 1
    start = i
    while i < n and not blank(body_lines[i]):
        i += 1
    end = i
    if start >= end:
        raise SystemExit("Could not find a first body paragraph to use as the executive summary.")
    return start, end, " ".join(l.strip() for l in body_lines[start:end])


# ---------------------------------------------------------------- YAML utils

def yaml_quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def yaml_scalar(text: str) -> str:
    if re.search(r'[:#"\[\]{}]|^[\s\-\'>|*&!%@`]|\s$', text) or text == "":
        return yaml_quote(text)
    return text


def parse_tags(raw: str):
    tags = [t.strip() for t in raw.split(",") if t.strip()]
    if len(tags) > 5:
        raise SystemExit(f"--tags gave {len(tags)} tags, max is 5: {tags}")
    return tags


# ---------------------------------------------------------------- date logic

def date_pool(year: int):
    start = datetime.date(year, DATE_MONTHS[0], 1)
    end_month = DATE_MONTHS[1]
    last = datetime.date(year, end_month, 31) if end_month in (1, 3, 5, 7, 8, 10, 12) else datetime.date(year, end_month, 30)
    days, d = [], start
    while d <= last:
        days.append(d)
        d += datetime.timedelta(days=1)
    return days


def allocate_weekday_counts(n: int):
    """Largest-remainder allocation of n posts across Mon..Sun in proportion to
    WEEKDAY_WEIGHTS. Guaranteed non-increasing Mon -> Sun."""
    total = sum(WEEKDAY_WEIGHTS)
    raw = [n * w / total for w in WEEKDAY_WEIGHTS]
    base = [int(r) for r in raw]
    for i in sorted(range(7), key=lambda i: -(raw[i] - base[i]))[: n - sum(base)]:
        base[i] += 1
    # Repair any ordering violation introduced by remainder rounding.
    for i in range(6):
        if base[i] < base[i + 1]:
            base[i], base[i + 1] = base[i + 1], base[i]
    return base


def pick_dates_batch(n: int, year: int, rng: random.Random):
    """Deterministic weekday allocation; distinct dates where the pool allows."""
    days = date_pool(year)
    by_wd = {i: [d for d in days if d.weekday() == i] for i in range(7)}
    picks = []
    for wd, count in enumerate(allocate_weekday_counts(n)):
        pool = by_wd[wd]
        if count <= len(pool):
            picks += rng.sample(pool, count)
        else:                                   # more posts than distinct dates
            picks += rng.sample(pool, len(pool)) + rng.choices(pool, k=count - len(pool))
    rng.shuffle(picks)
    return picks


def pick_date_single(year: int, rng: random.Random):
    days = date_pool(year)
    return rng.choices(days, weights=[WEEKDAY_WEIGHTS[d.weekday()] for d in days], k=1)[0]


def current_date(front_lines):
    """The frontmatter's existing date as a date object, or None."""
    for l in front_lines:
        m = re.match(r"^date:\s*(\S+)", l)
        if m:
            try:
                return datetime.date.fromisoformat(m.group(1).strip('"\''))
            except ValueError:
                return None
    return None


def in_date_window(d):
    """True if d already sits in Jan-May of the current year."""
    return d is not None and d.year == datetime.date.today().year and DATE_MONTHS[0] <= d.month <= DATE_MONTHS[1]


# ------------------------------------------------------------------ the work

def adapt(path: Path, tags, new_date, force_date=False, force_draft=False):
    text = path.read_text(encoding="utf-8")
    front, body = split_frontmatter(text)
    report = []

    front, removed = remove_key_block(front, "sources")
    report.append(f"sources removed: {removed}")

    existing = find_existing_lead(body)
    if existing is not None:
        para, new_body = existing, body
        report.append("lead wrap: already present")
    else:
        s, e, para = extract_lead_paragraph(body)
        new_body = body[:s] + [f"{LEAD_OPEN}\n", "".join(body[s:e]), f"{LEAD_CLOSE}\n"] + body[e:]
        report.append("lead wrap: added")

    if has_key(front, "description"):
        report.append("description: already present")
    else:
        front.append(f"description: {yaml_quote(para)}\n")
        report.append(f"description: added ({len(para)} chars)")

    if has_key(front, "tags"):
        report.append("tags: already present")
    elif tags:
        front.append("tags:\n")
        for t in tags:
            front.append(f"  - {yaml_scalar(t)}\n")
        report.append(f"tags: added ({', '.join(tags)})")
    else:
        report.append("tags: NOT PROVIDED — still needs tagging")

    # `date:` is window-checked rather than presence-checked: produce-blog always
    # writes today's date, so a plain presence check would mean this never runs.
    # A date already inside the target window is left alone, which keeps re-runs
    # idempotent instead of churning dates on every invocation.
    if in_date_window(current_date(front)) and not force_date:
        report.append(f"date: already in window ({current_date(front)}), kept")
    else:
        set_key(front, "date", new_date.isoformat())
        report.append(f"date: set {new_date.isoformat()} ({new_date.strftime('%a')})")

    if has_key(front, "draft") and not force_draft:
        report.append("draft: already present (use --force-draft to overwrite)")
    else:
        set_key(front, "draft", "false")
        report.append("draft: set false")

    new_text = "---\n" + "".join(front) + "---\n" + "".join(new_body)
    if new_text == text:
        return None, report
    path.write_text(new_text, encoding="utf-8")
    return True, report


def load_tags_file(p: Path):
    mapping = {}
    for raw in p.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        if "\t" not in raw:
            raise SystemExit(f"--tags-file line is not slug<TAB>tags: {raw!r}")
        slug, tags = raw.split("\t", 1)
        mapping[slug.strip()] = parse_tags(tags)
    return mapping


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--tags", default=None, help="Comma-separated tags, max 5 (single-post mode only)")
    ap.add_argument("--tags-file", default=None, help="TSV of slug<TAB>tags (folder mode)")
    ap.add_argument("--seed", type=int, default=None, help="Seed the date draw for reproducibility")
    ap.add_argument("--force-date", action="store_true", help="Overwrite an existing date:")
    ap.add_argument("--force-draft", action="store_true", help="Overwrite an existing draft:")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    year = datetime.date.today().year
    kind, value = resolve_target(args.target)

    if kind == "post":
        if args.tags_file:
            raise SystemExit("--tags-file applies to folder mode; use --tags for a single post.")
        tags = parse_tags(args.tags) if args.tags else None
        changed, report = adapt(value, tags, pick_date_single(year, rng),
                                args.force_date, args.force_draft)
        print(f"{'Adapted' if changed else 'Already fully adapted — no changes made'}: {value}")
        for line in report:
            print(f"  {line}")
        return

    # ---- folder mode
    posts = value
    if args.tags:
        raise SystemExit(
            f"--tags would apply the same tags to all {len(posts)} posts, and tags are a "
            "per-post judgment. Use --tags-file (slug<TAB>tags) instead."
        )
    tag_map = load_tags_file(Path(args.tags_file)) if args.tags_file else {}
    dates = pick_dates_batch(len(posts), year, rng)

    print(f"Folder mode: {len(posts)} posts under {posts[0].parent.parent}")
    untagged, changed_n = [], 0
    for path, d in zip(posts, dates):
        slug = path.parent.name
        tags = tag_map.get(slug)
        if not tags:
            untagged.append(slug)
        changed, report = adapt(path, tags, d, args.force_date, args.force_draft)
        changed_n += 1 if changed else 0
        print(f"\n{slug}")
        for line in report:
            print(f"  {line}")

    counts = [0] * 7
    for d in dates:
        counts[d.weekday()] += 1
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    print(f"\n--- {changed_n}/{len(posts)} written ---")
    print("weekday spread: " + "  ".join(f"{names[i]} {counts[i]}" for i in range(7)))
    print("non-increasing Mon->Sun:", all(counts[i] >= counts[i + 1] for i in range(6)))
    if untagged:
        print(f"\nSTILL NEEDS TAGS ({len(untagged)}): {', '.join(untagged)}")


if __name__ == "__main__":
    main()
