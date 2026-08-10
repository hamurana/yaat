---
name: blog-ncw-adapter
description: Adapt already-produced blog-factory posts (output of the produce-blog skill) for NCW publishing — strip the sources field from the frontmatter, add a description populated from the post's first paragraph, wrap that same paragraph in the body with {{< lead >}} tags, add a judgment-based tags field (up to 5 representative tags), set a publication date drawn from January–May of the current year with weekday frequency decreasing Monday to Sunday, and set draft to false so the post lands published. Accepts a single post OR a folder, in which case every post inside it is adapted. Invoke as "/blog-ncw-adapter <slug|folder|path>", e.g. "/blog-ncw-adapter less-clothes-more-elegant" or "/blog-ncw-adapter output". Use whenever the user says "adapt this blog for NCW", "run the ncw adapter", "prep this post for publishing", "tag this post", or points at a post or folder under blog-factory/output/ for this transform.
---

# Blog NCW Adapter

Takes one finished post produced by the `produce-blog` skill (`blog-factory/output/<slug>/index.md`)
and adapts its frontmatter and lead paragraph for NCW publishing. This is a pure
post-processing step on an existing post — it does not touch Ark notes or CSV
manifests, and it does not write new content beyond the tags it judges.

## Invocation

`/blog-ncw-adapter <slug|folder|path>` — one required parameter identifying
what to adapt:

- a bare slug, e.g. `less-clothes-more-elegant` (resolves to
  `blog-factory/output/less-clothes-more-elegant/index.md`)
- a post folder — one that directly contains an `index.md`
- a direct path to an `index.md`
- **a folder of posts** — a directory whose *subdirectories* contain
  `index.md` files. The command then applies to **every post inside it**.
  `/blog-ncw-adapter output` adapts all posts in `blog-factory/output/`.

If the parameter is missing, ask for it — unless every unadapted post is the
only thing present, in which case "adapt everything" and "adapt what needs it"
resolve to the same file set and you can just proceed, saying why.

## Step 1 — read and understand each post completely

Before touching anything, **read the full body** of every post you're about to
adapt — not just the first paragraph, and not a skim. You need to understand:

- **What it actually argues**, including the thesis it leads with.
- **Its context** — the topic it sits under, the batch it came from, and what
  its source material was about. A post's Ark note and origin video are fair
  context to consider even though the adapter never modifies them.
- **Where it pushes back.** Many posts add a caveat, correction, or objection
  to their source. That is frequently the most distinctive thing in the piece.
- **What sits near it.** If sibling posts cover adjacent ground, know that
  before tagging, so the tag sets don't collide.

This step is the whole job. The script is mechanical; the reading is not.

## Step 2 — choose tags (your judgment, not the script's)

Decide **up to 5 tags that genuinely represent the post** — what it argues,
not merely what it is about.

- **Prefer the specific mechanism over the category.** `Sequence of Returns
  Risk` over "Retirement". `Enclothed Cognition` over "Style". `Theory of
  Constraints` over "Productivity".
- **Reject the generic tier outright** — "Life", "Tips", "Advice", "Mindset",
  "Health", "Money" are filler and carry no information.
- **A tag may name the post's pushback** rather than its subject. Where the
  best section is the caveat the post adds, tag that: `Conversational Ethics`,
  `Morally Neutral Charisma`, `Climate Constraint`.
- **Fewer, sharper tags beat padding to five.** Four precise tags is a better
  outcome than four precise tags plus one vague one.
- **Give adjacent posts divergent tags.** Posts built on the same source, or
  covering neighbouring ground, must not end up with identical sets — they
  would surface as near-duplicates in a tag index. Split them on each post's
  actual emphasis.
- **Every tag must be defensible from the text.** If you could not point at
  the paragraph that earns it, it is the wrong tag.

The helper script has no opinion on tag content — it inserts whatever you give
it. Bad tags are therefore entirely a failure of Step 1.

## Step 3 — run the helper script

The script does the rest of the transform mechanically and in place:

**Single post:**

```bash
python3 .claude/skills/blog-ncw-adapter/scripts/adapt-post.py "<slug|path>" --tags "Tag One, Tag Two, Tag Three"
```

**Folder of posts** — tags are per-post, so `--tags` is *rejected* here (it
would stamp the same tags on everything). Pass a TSV of `slug<TAB>tags`:

```bash
python3 .claude/skills/blog-ncw-adapter/scripts/adapt-post.py "<folder>" --tags-file tags.tsv
```

Without `--tags-file`, folder mode still applies every other field and then
lists which posts still need tagging, so nothing is silently left untagged.

Other flags: `--seed N` makes the date draw reproducible; `--force-date` and
`--force-draft` overwrite values the script would otherwise preserve.

For each resolved `index.md`, the script:

1. **Removes the `sources:` block** from the frontmatter entirely (handles both
   the `- name: ... / origin: ...` structured form and the older flat
   `- name — origin` form seen in earlier runs).
2. **Extracts the executive summary** — the post's first body paragraph. If the
   body opens with an `# H1` title line, that's skipped first; the paragraph
   is whatever contiguous text immediately follows. (If the paragraph is
   already wrapped in `{{< lead >}}` from a prior run, it reuses that text
   instead of re-deriving it.)
3. **Adds `description:`** to the frontmatter, set to that paragraph text
   verbatim (YAML-double-quoted, with internal `"` and `\` escaped).
4. **Wraps that same paragraph in the body** with:
   ```
   {{< lead >}}
   <paragraph text>
   {{< /lead >}}
   ```
5. **Adds `tags:`** to the frontmatter as a YAML list, from the supplied values.
6. **Sets `date:`** to a date in **January–May of the current year**, weighted
   so weekday frequency decreases Monday → Sunday (see below).
7. **Sets `draft: false`** (an unquoted YAML boolean), so an adapted post lands
   published. An existing `draft:` of either value is left alone — see
   Idempotency.

The file is edited in place — no new file or folder is created, and the rest
of the body is untouched.

## The date distribution

Dates come from 1 January to 31 May of the current year, with weekday weights
7,6,5,4,3,2,1 for Monday through Sunday.

**Folder mode allocates weekday counts deterministically across the batch**
(largest-remainder), so the Monday→Sunday decrease is *guaranteed* in the
result rather than merely likely, and dates are distinct where the pool
allows. **Single-post mode draws one weighted-random date** — with n=1 no
distribution can be guaranteed, and adapting a batch one post at a time will
approximate the shape but can invert in the tail. Prefer folder mode for
batches; the script prints the resulting spread and whether it is
non-increasing.

## Idempotency

Each field is checked and applied independently, so the script is safe to
re-run and safe for backfilling a single missing piece — running it with tags
on a post adapted before tagging existed adds only `tags:` and leaves the rest
untouched. If nothing changes, it reports "already fully adapted".

Two fields are deliberately protected:

- **`draft:` is presence-checked, not value-checked.** Once a post carries a
  `draft:` line the script never rewrites it, so a post you have deliberately
  held back at `draft: true` — or promoted by hand — survives any number of
  re-runs. Use `--force-draft` to overwrite, or delete the line and re-run.
- **`date:` is window-checked.** A date already inside January–May of the
  current year is kept; anything else (including the `produce-blog` default of
  today's date) is replaced. A plain presence check would mean the date step
  never ran at all, since `produce-blog` always writes one — and this way
  re-running does not churn dates that are already correct. Use `--force-date`
  to redraw.

**`draft:` is presence-checked, not value-checked.** Once a post carries a
`draft:` line the script never rewrites it, so promoting a post by hand to
`draft: false` survives any number of re-runs — the adapter will not
un-publish something you have already published. To force a post back to
draft, delete its `draft:` line and re-run (or just edit the value directly).

## Reporting

The script prints what it did for each field — whether `sources` was found
and removed, whether the lead wrap/description/tags were added or were
already present. Relay that back, and always state the tags chosen and the
one-line reasoning for them (so it's clear they came from actually reading
the post, not a generic guess).

If the slug/path doesn't resolve, the script lists the slugs actually present
under `blog-factory/output/` — surface that list rather than guessing.
