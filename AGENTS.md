# Working agreements

This repository holds Zooko's survey *Lessons from the history of attacks on secure hash functions*: a Markdown page (`history-of-hash-function-attacks.md`), its RST ancestor, and the script that migrated one to the other. The work is a document, so most of what follows is about writing; the rest is about keeping the few tools around it small. Name Zooko as "Zooko" alone, everywhere (his wish).

## The Simplicity Strategy

Simplicity is our first design goal, in prose, data, tables, and code. Prefer the simplest design that meets the need and performs well.

**Why.** Complexity is a cost paid every day it exists: every reader reads it, every run carries it, every later change works around it. Its benefit comes only when it acts, and only when it acts correctly. A simple design is one a reader can understand, predict, and check, and a result that can be checked is one people can trust.

**Three dimensions.**

- **Conceptual ease:** a reader understands and predicts the design from a few familiar concepts.
- **Less code and information:** fewer moving parts, less state, fewer facts to hold in working memory.
- **Fewer runtime cases:** fewer branches, special cases, tuning knobs, and operating regimes.

**How to practise it.**

1. **Every piece earns its place.** Each mechanism, script, option, check, table column, or paragraph stays while its demonstrated benefit exceeds its cost. An optional, partial, or unreliable piece carries its whole cost for a share of its benefit. Before adding, keeping, or rescuing a piece, estimate from the evidence in hand whether it pays; then improve it or remove it, and say which and why.
2. **One mechanism per problem.** When you start building a second solution to a problem an earlier one already addresses, stop. Make the first good enough or remove it, and say which before building.
3. **Choose the simpler of two equals.** When approaches perform similarly, take the simpler.
4. **Revisit complexity as you learn.** When new evidence shows a piece doing less than it was built for, weigh removing it.
5. **Trace causes before adding mechanisms.** An unexplained cause is an orange flag. Establish the cause first; a diagnostic earns its place by distinguishing possible causes.
6. **Reuse what exists.** Use the tools and formats already here (one Markdown source, one migration script). A need they leave unmet is a change to them, never a private copy beside them.
7. **Fewest new concepts.** A page, table, or interface succeeds when its reader learns the fewest new terms. Prefer the concepts the reader already holds.
8. **Contracts stay simple and explicit.** State and `assert` each assumption code relies on; when an input breaks it, fail stop with a clear message. Code accepts the current format only, and every caller and reader changes with it.

**These rules govern this file too.** When a rule fails, first look for something to remove or to move to where its subject lives; add only what nothing else can do.

## Writing

Every sentence costs the reader attention. Keep what pays its reader much more than it costs; cut the rest.

- **Write for a reader who holds only the page.** Introduce each term on the page or use common ones. Answer the questions the page itself raises, in the order the reader meets them. Describe things as they are now; how they got here belongs in commit messages and notes.
- **Serve three readers at once:** the newcomer who holds only the page, the regular who knows the subject, and the maintainer who knows its history. Material for one reader alone goes behind a door (an appendix, a footnote, a collapsed section, a notes file).
- **Show before you tell.** Tables, grouping, position, and colour carry meaning at a glance; words and numbers follow. A caption stays only when the figure can't say it.
- **Phrase positively or neutrally.** Avoid negations and "not this, but that" contrasts. Show the promising aspects of the recommended path; mention an alternative when its trade-offs deserve attention.
- **Prose craft:** cut filler; make the real actors the subjects and their actions the verbs; keep subjects near verbs and verbs near objects; open with the familiar and end with the new and important; keep subjects consistent across a passage; use passive voice deliberately; name who is responsible; trim metadiscourse.
- **Finish with a fresh reading.** After each change, reread the whole page as each of the three readers; the revision is done when the page reads as if written fresh.

## Claims and numbers

- **Honest claims.** State the tightest bound the cited work supports, with its scope and its limits. Distinguish a published attack, a practical demonstration, and a theoretical result; report each separately.
- **Exact arithmetic.** Attack costs count discrete things (compressions, operations, bytes), so write and compare them as exact powers and integers (`2^61`, `T^k <= 2^(k*b)`). Round once, where a person reads the value.
- **Cite the source.** Every attack named on the page points at the paper or announcement that established it.

## Working here

- The Markdown page `history-of-hash-function-attacks.md.html` is the one source. Its `.md.html` name is Markdeep's convention: a browser treats it as HTML, Markdeep (`markdeep.min.js`) renders the Markdown, and `viewer.js` draws Figures 1 and 2 as year-by-year coloured timelines from the transitions table. GitHub Pages serves it from the `johnservil/hash-function-survey` repository.
- `migrate_rst.py` was a one-time bridge from the RST. The page has been edited by hand since, so running the script again overwrites those edits; it goes once the RST does. Backup files (`*~`, `*.orig`, `*.FAILED.md`, `*-old.md`) are history, and history lives in git.
- **Ask before spending.** Large downloads, long computations, or anything that speaks publicly in Zooko's name costs real resources. Say what it will cost, and ask first.
