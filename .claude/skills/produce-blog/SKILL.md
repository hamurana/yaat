---
name: produce-blog
description: Turn a CSV manifest in blog-factory/ into one synthesized blog post drawn from the referenced Ark knowledge-base notes, written according to a named blog profile. Invoke as "/produce-blog <profile> <csv>", e.g. "/produce-blog s1 health-batch.csv". Use whenever the user says "produce a blog", "make a blog from the csv", "run the blog factory", "write a blog from these notes", or points at a .csv in blog-factory/ — even if they don't say "blog post" explicitly, or name a profile like "s1". Also use when the user asks to repurpose Ark Learning notes into a publishable article.
---

# Produce Blog

Write one original, authoritative blog post whose *ideas* come from a batch of Ark Learning notes listed in a CSV manifest, produced according to a named **blog profile** that defines the style, stance, and requirements to write to.

## Invocation

This skill takes two required positional parameters: `/produce-blog <profile> <csv>`.

- `<profile>` — the name of a blog profile, e.g. `s1`. A profile is a file at `.claude/skills/produce-blog/profiles/<profile>.md` that defines *how* the post gets written: stance, research approach, register, structure, precision rules, output naming, and sign-off.
- `<csv>` — the name of the CSV manifest in `blog-factory/`, e.g. `health-batch.csv` (the `.csv` extension may be omitted).

**Both parameters are required — do not guess either on the user's behalf.** If the user's request doesn't specify both (e.g. they just say "produce a blog" or point at a CSV without naming a profile), stop and report the missing parameter(s), then ask them to re-invoke with both, for example:

> `/produce-blog s1 health-batch.csv`

Do not fall back to a default profile and do not proceed with only one parameter resolved.

## Resolving the profile

Look for `.claude/skills/produce-blog/profiles/<profile>.md`.

- If it exists, read it in full. It is the authority on the rest of the workflow — follow its instructions to write and save the post.
- If it doesn't exist, list the profiles actually present in `.claude/skills/produce-blog/profiles/` and ask the user which they meant. Don't silently substitute a different profile.

### Available profiles

- **s1** (`profiles/s1.md`) — the original blog-factory behavior: own-the-ideas stance, independent research, three-part macro structure, topic-matched register, 3,000-word cap. The full-rigor baseline (100%).
- **s2** (`profiles/s2.md`) — a lighter, faster-turnaround profile at roughly 75% of s1's research depth and formal polish: same own-the-ideas stance and three-part structure, but research scoped to only the 2–4 headline claims, more forgiving sourcing standards, a more conversational register, and a shorter 1,200–1,800 word target.
- **s3** (`profiles/s3.md`) — a minimal, low-key profile at roughly 50% of s1's scale: no independent research at all (notes only), softspoken tone, bullet-heavy, everyday vocabulary, no macro-structure requirement, under 800 words.

## Resolving the CSV

- The manifest is a `.csv` in `blog-factory/` with header `name,topic,title`.
  - `name` — an Ark note basename in `DD-MM-YYYY-N` form.
  - `topic` — the Ark category (Health, Investment, Style, …).
  - `title` — the original video title (context only; the notes are the source of truth).
- Resolve `<csv>` to `blog-factory/<csv>`, appending `.csv` if the user omitted it. If that file doesn't exist, report the miss (and, if helpful, list the `.csv` files actually present in `blog-factory/`) and stop — don't guess which manifest was meant.
- Each row's `name` resolves to `Ark/Learning/<MM>/<name>.md`, where `<MM>` is the month segment of the `DD-MM-YYYY` date (e.g. `12-05-2026-5` → `Ark/Learning/05/12-05-2026-5.md`).
- Resolve every row before writing anything. If a note is missing, report the gap and continue with what exists — never invent content for a missing row.

Once the profile is loaded and the CSV rows are resolved to notes, follow the loaded profile's instructions for the rest of the task (reading the notes, finding the thesis, researching, writing, and saving the output).
