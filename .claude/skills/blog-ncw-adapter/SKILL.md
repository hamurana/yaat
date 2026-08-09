---
name: blog-ncw-adapter
description: Adapt one already-produced blog-factory post (output of the produce-blog skill) for NCW publishing — strip the sources field from its frontmatter, add a description field populated from the post's first paragraph, wrap that same first paragraph in the body with {{< lead >}} tags, add a judgment-based tags field (up to 5 tags) summarizing the post's main points, and set draft to true so the post lands unpublished. Invoke as "/blog-ncw-adapter <slug|path>", e.g. "/blog-ncw-adapter less-clothes-more-elegant". Use whenever the user says "adapt this blog for NCW", "run the ncw adapter", "prep this post for publishing", "tag this post", or points at a post under blog-factory/output/ for this transform.
---

# Blog NCW Adapter

Takes one finished post produced by the `produce-blog` skill (`blog-factory/output/<slug>/index.md`)
and adapts its frontmatter and lead paragraph for NCW publishing. This is a pure
post-processing step on an existing post — it does not touch Ark notes or CSV
manifests, and it does not write new content beyond the tags it judges.

## Invocation

`/blog-ncw-adapter <slug|path>` — one required parameter identifying the post:

- a bare slug, e.g. `less-clothes-more-elegant` (resolves to
  `blog-factory/output/less-clothes-more-elegant/index.md`)
- a folder path (resolves to `<folder>/index.md`)
- a direct path to an `index.md`

If the parameter is missing, ask for it rather than guessing which post was meant.

## Step 1 — read and understand the post

Before touching anything, **read the full body** of the resolved `index.md` —
not just the first paragraph. You need to actually understand what the post
argues and its main points, because the next step depends on that
understanding.

## Step 2 — choose tags (your judgment, not the script's)

Decide **up to 5 tags** that are genuinely representative of the post's
content and main points — not generic filler (avoid vague tags like "Life" or
"Tips"; prefer specific ones tied to the actual subject and argument, e.g.
"Insulin Resistance", "Decision Fatigue", "Discipline" over "Health",
"Advice", "Mindset"). Fewer, sharper tags beat padding out to 5. This is a
judgment call you make from having read the post in Step 1 — the helper
script has no opinion on tag content, it only inserts whatever you give it.

## Step 3 — run the helper script

The script does the rest of the transform mechanically and in place:

```bash
python3 .claude/skills/blog-ncw-adapter/scripts/adapt-post.py "<slug|path>" --tags "Tag One, Tag Two, Tag Three"
```

`--tags` is a comma-separated list of the tags chosen in Step 2 (max 5 — the
script errors out if you pass more). Omit `--tags` only if you're deliberately
backfilling some other field on a post you're not tagging right now.

For the resolved `index.md`, the script:

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
5. **Adds `tags:`** to the frontmatter as a YAML list, from the `--tags` values.
6. **Adds `draft: true`** to the frontmatter (an unquoted YAML boolean), so an
   adapted post always lands unpublished and has to be promoted deliberately.
   An existing `draft:` value of either kind is left alone — see Idempotency.

The file is edited in place — no new file or folder is created, and the rest
of the body is untouched.

## Idempotency

Each of the five fields above is checked and applied independently, so the
script is safe to re-run and safe to use for backfilling just one missing
piece — e.g. running it with `--tags` on a post that was already adapted
before tagging existed only adds the `tags:` field and leaves
`sources`/`description`/the lead wrap untouched. If every field is already in
place, it reports "already fully adapted" and makes no changes.

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
