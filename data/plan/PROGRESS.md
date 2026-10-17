# Resume state (checkpoint)

**STATUS 2026-10-17: FINALIZED.** All 68 chunks valid; outputs in `data/final/`; summary in `data/plan/FINAL_REPORT.md`. Remaining work is human review and optional split-gap fixes (see report). The checklist below is historical.

* Plan files: `data/plan/labels.json`, `data/plan/plan.md` — labels frozen; do not edit.
* **All 68 section folders written** (S001–S068: facts.csv, questions.csv, review.md). S068 is intentionally header-only (faculty biographies).
* `data/plan/negative_questions.csv` written (40 rows: 20 live_data_needed, 20 not_in_catalog).
* Approx. totals: ~1,290 facts, ~2,730 questions; ~70 facts marked `needs_review` (listed per chunk in each review.md).

## Not yet done (Bash is denied in `.claude/settings.json`, so run these yourself)
1. `python scripts/workflow.py check-plan`
2. `python scripts/workflow.py status --all`
3. For any INVALID chunk: `python scripts/workflow.py validate Sxxx` — most likely error is a `source_quote` that does not exactly match the page text; copy a substring from `chunks/Sxxx/source.txt` (whitespace/case insensitive).
4. `python scripts/workflow.py finalize` — if it reports duplicate question strings across chunks, reword the listed question in the later chunk and rerun.
5. Human review of all `needs_review` rows and a sample of drafts.

## To resume with Claude
"Read data/plan/PROGRESS.md and fix the errors from this validation output: <paste output>" — Claude should edit only the reported rows.
