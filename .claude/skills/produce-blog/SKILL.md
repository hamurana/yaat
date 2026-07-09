---
name: produce-blog
description: Turn a CSV manifest in blog-factory/ into one synthesized blog post drawn from the referenced Ark knowledge-base notes. Use whenever the user says "produce a blog", "make a blog from the csv", "run the blog factory", "write a blog from these notes", or points at a .csv in blog-factory/ — even if they don't say "blog post" explicitly. Also use when the user asks to repurpose Ark Learning notes into a publishable article.
---

# Produce Blog

Write one original, authoritative blog post whose *ideas* come from a batch of Ark Learning notes listed in a CSV manifest. The manifest curates which notes seed the piece; your job is to digest their views and argue them in your own voice — not to recap, critique, or retell the source videos.

## The core stance (read this first — it's the mistake to avoid)

The blog is **your own piece built on the digested views**, not a summary of what the creators said. Digest every note, condense them to a **core thesis**, then make that argument yourself and support it with your **own independent research**.

- **Strip all narration of the sources.** No "Dr. Alex says…", "the video claims…", "the creator argues…". The creators are the *seed* of the idea, not the *subject* of the writing. If a sentence's job is to report what a video said, cut or rewrite it.
- **Do your own research.** Use `WebSearch`/`WebFetch` to find real studies, data, and examples that back the thesis, and cite them inline as markdown links, with a "Sources & further reading" list at the end. Prefer primary/authoritative sources (journals, PubMed/PMC, recognised bodies).
- **This overrides the vault's "no outside claims" rule.** That rule governs Ark notes, not blogs. Here, importing well-sourced external material is the whole point. Where your research refines a figure from the notes, trust the researched figure (e.g. notes said glycine "~10g"; trials use 3g → write 3g).

## Inputs

1. **The manifest**: a `.csv` in `blog-factory/` with header `name,topic,title`.
   - `name` — an Ark note basename in `DD-MM-YYYY-N` form.
   - `topic` — the Ark category (Health, Investment, Style, …).
   - `title` — the original video title (context only; the notes are the source of truth).
   - If the user didn't name a CSV and `blog-factory/` holds more than one, ask which to use.
2. **The notes**: each `name` resolves to `Ark/Learning/<MM>/<name>.md`, where `<MM>` is the month segment of the `DD-MM-YYYY` date (e.g. `12-05-2026-5` → `Ark/Learning/05/12-05-2026-5.md`).

Resolve every row before writing anything. If a note is missing, report the gap and continue with what exists — never invent content for a missing row.

## Workflow

### 1. Read everything first

Read all referenced notes in full and absorb the substance. Only after absorbing the whole set, find the **thesis angle**: the claim or tension that connects the notes — one no single video states outright but the batch collectively points to. This becomes *your* argument. Don't default to "N tips from N videos", and don't organise the post around the videos as objects.

The formula that has worked on every run so far: **name the single upstream variable the whole batch shares, then argue that every technique in the notes is downstream of it.** Worked examples:
- *Health*: insulin resistance is the silent throughline — cheap daily movement beats the supplement economy.
- *Charisma*: charisma isn't performance, it's the absence of need ("want it, don't need it") — humor, small talk, listening, and gravitas techniques are all symptoms of that one state.

### 2. Research the thesis independently

Before writing, back the argument with your own material. Run `WebSearch`/`WebFetch` for real studies, data, and examples that support (or usefully complicate) the core claims — especially any specific mechanism, dose, or statistic you're going to assert. Prefer primary/authoritative sources (journals, PubMed/PMC, recognised bodies). Collect the URLs; you'll cite them inline and list them at the end. Where research refines a figure from the notes, use the researched figure.

The efficient shape of this step: **list the core claims the argument leans on, then run one targeted search per claim — ~6–8 searches total, issued in parallel batches of 2–3.** Aim each search at the **canonical named study** behind the technique, not a generic topic query (e.g. spotlight effect → Gilovich 2000; question-asking → Huang 2017; deep questions → Aron 1997's 36-questions study; listening → Itzchakov & Kluger; humor → McGraw & Warren's benign violation theory; vocal pitch → Klofstad 2012). Cite the journal/PDF link when reachable; a reputable secondary summary (e.g. BPS Research Digest) is acceptable when the paper is paywalled. Give each "Sources & further reading" entry authors + year + journal.

### 3. Match the writing style to the topic

The base rules are the Blog Post Generation Standards in `.claude/CLAUDE.md` (Section 2) — banned AI-fluff words, skimmer formatting, inverted pyramid, transition sentences. Write in your own authoritative voice; no narration of the sources. Layer topic-specific judgment on top:

- **Health / medical** — evidence-first. State mechanisms, doses, and statistics exactly, as researched fact with a citation, and keep honest hedges and safety caveats ("modest, consistent effect", "check with a doctor", kidney-disease exceptions).
- **Investment / Business** — numbers and frameworks carry the piece. Name companies, figures, and framework names verbatim; flag speculation as opinion.
- **Style / Charisma / self-improvement** — more personal, second-person, example-driven. Keep specific product/garment/technique names. Confirmed shape from the Charisma run: research citations woven into an opinionated argument (not an evidence review), and the closing "so what" written as a **numbered drill list** of small concrete reps ("give someone 10 minutes of full attention", "swap one *what* for one *why* per conversation") — one drill per section, mapping back to the argument.
- Anything else: infer the register from the subject matter.

### 4. Precision rules

- Keep every statistic, tool, book, brand, dose, and framework name specific — "magnesium glycinate, 200–400mg elemental", never "a magnesium supplement".
- A factual claim (statistic, dose, study result) needs a real cited source. Illustrative analogies and everyday scenarios don't — use them freely for clarity.
- Genuine conflicts in the evidence are content, not problems — surface them.
- Leaving a source's minor points out is fine; distorting the ones you keep is not.
- **Banned words stay banned even when a note uses one legitimately.** A note's "carrot and stick *leverage*" is a real concept, but "leverage" is on the Section-2 ban list — substitute a precise alternative ("options", "walk-away power", "bargaining position") rather than importing the banned word.

### 5. Write the post

- **Length**: under 3,000 words. No minimum — a tight, well-sourced ~1,800-word piece beats a padded one. Say what the argument supports and stop.
- **Lead** with the single most valuable or surprising insight (inverted pyramid).
- **Headers**: frequent `###` section headers a skimmer can navigate by.
- **Cite inline** as markdown links, and close the body with a **"Sources & further reading"** list.
- **End** each section with a sentence that pulls the reader into the next.
- **Close** with the "so what": the concrete actions a reader should take.

### 6. Save the output

Write the post to `blog-factory/<csv-basename>-blog.md` (e.g. `Health.csv` → `Health-blog.md`). Re-running with the same manifest overwrites this file — that's intended.

Start the file with YAML frontmatter for traceability, then the post:

```markdown
---
title: <the blog's own headline>
topic: <topic from the CSV>
date: <today, YYYY-MM-DD>
sources:
  - <name from CSV> — <origin link from the note>
---

# <Headline>
...
```

When done, report: the thesis angle you argued, the key sources you researched and cited, the word count, and any rows that failed to resolve.

To count body words (excluding frontmatter), don't strip the frontmatter with two sed `---` passes — line 1 *is* `---`, so that silently yields 0. Use:

```bash
awk 'c==2{print} /^---$/{c++}' blog-factory/<csv-basename>-blog.md | wc -w
```
