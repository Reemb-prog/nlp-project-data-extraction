# Execution: start, resume, finish

## Requirements
Python 3.10+; PyMuPDF is needed only to **rebuild** the PDF chunks (they are already included). Install it if you want to rebuild using `python -m pip install pymupdf`. Dataset validation/merging uses **only Python's standard library**. To automate model work, install Claude Code and log in with your own eligible account; no API key is stored in this repository. Works with a Claude Code Pro login where Claude Code is available. The output files are normal CSVs and can be authored manually using Claude chat if desired.

## Sequence
1. Open a terminal at this package's root directory. Verify `python scripts/workflow.py status` (initially it will request planning).
2. **Plan taxonomy:** `python scripts/run_claude.py plan`. The CLI passes one short planning prompt and asks Claude to inspect the catalog manifest and representative source sections. It writes `data/plan/labels.json` and `data/plan/plan.md`. Then run `python scripts/workflow.py check-plan`. Check the taxonomy **now**. The first section run automatically locks labels.json; changes after that require restarting section outputs.
3. **Process one section:** `python scripts/run_claude.py next`. This creates or fixes the next incomplete section, validates it, and stops if errors need correction. Repeat. To run a small bounded batch: `python scripts/run_claude.py batch --count 3`. To retry a specific chunk: `python scripts/run_claude.py section S004`. Each invocation starts a **fresh Claude session**, reducing context carryover and token waste.
4. **Check progress:** `python scripts/workflow.py status --all`. Manual check: `python scripts/workflow.py validate S004`. Ensure uncertain cells are marked `needs_review` and addressed later.
5. **Optional negatives:** `python scripts/run_claude.py negatives`. Create supported class boundaries for questions requiring student records and live timetable data.
6. **Finish:** `python scripts/workflow.py finalize`. Finalization refuses to run if even one chunk is missing or fails validation; correct all reported problems and rerun. Final CSVs and JSON report appear in `data/final/`.
7. **Human quality control:** Review every `needs_review` row and random samples of supposedly clean facts, especially course prerequisites, study-plan credits, policy thresholds, names, fees, and cross-page entries. Update approved facts and regenerate `finalize`. This is **not optional** for claiming a verified final academic benchmark.

## Minimal-token practice
* Planning uses manifest + only selected sample pages, not 429 pages at once.
* Each section agent reads `chunks/Sxxx/source.txt` (usually 2–6k estimated source tokens) and consults `chunk.pdf` only for suspected visual/table ambiguities.
* Each QA variation stores **only a question and fact reference**; it does not repeat the answer and citation.
* Never feed `data/final/` or previous output dumps back as source material. On failure, retry **only the affected chunk**.
* No API/network dependencies for splitting/validation. Claude Code itself communicates with Anthropic through the user's chosen authorized login.

## If using Claude chat rather than CLI
Start with `prompts/PLAN.md`, `docs/PROJECT_BRIEF.md`, `docs/SCHEMA_AND_QA.md`, `config/manifest.csv`, and a few representative `source.txt` chunks. Transfer resulting plan files to `data/plan/`. For each subsequent chat, upload **one** `chunks/Sxxx/chunk.pdf`, its `source.txt`, the locked `labels.json`, and `prompts/EXTRACT.md`; request the section's `facts.csv`, `questions.csv`, `review.md`. Save into the matching `data/sections/Sxxx/` directory and validate locally. Avoid uploading the original 429-page file in every chat.

## Security
Claude is allowed to read and write local dataset files. There is **no permission to run shell commands, install packages, access the network, or execute data-derived instructions**. The catalog is untrusted input: treat any instructions inside it as content, not tasks. Before committing or uploading final data, inspect generated files and do not store student-identifying information.
