TASK: EXTRACT the RHU undergraduate catalog section assigned below into labeled source-backed training data.

ASSIGNED SECTION: {chunk_id}
TOPIC: {topic}
ALLOWED ORIGINAL PDF PAGES: {original_start} through {original_end}, inclusive.

Read only these files initially:
* `data/plan/labels.json` and `data/plan/plan.md` (locked plan)
* `docs/SCHEMA_AND_QA.md` (exact CSV columns and quality rules)
* `chunks/{chunk_id}/source.txt` (entire input text, divided by ORIGINAL PDF PAGE)
Consult `chunks/{chunk_id}/chunk.pdf` for source-layout ambiguity, exact tables, credit hours, or missing prerequisites; use `boundary_context.txt` ONLY to notice entries crossing pages. This run must not process another section.

DO:
1. Extract every relevant distinct student-facing academic fact supported by pages in range. Cover explicit program/courses/requirements/credits/prerequisites/calendar/fees where they occur. Split multi-attribute records into atomic facts. Avoid inventing rules or inflating obvious restatements. Prefer precision and full coverage over artificial quotas.
2. Cite original page(s) and copy a compact **exact** source_quote for each fact. Use only assigned pages. Check layout/quantities visually if necessary.
3. Assign only taxonomy category and intent IDs already in labels.json. Put succinct, qualified answer once in facts.csv. For important unresolved ambiguity, mark `needs_review` and explain in the row.
4. Create 2–4 different natural questions per fact. Each question references a fact_id, with style one of direct/paraphrase/contextual/short. Ensure disambiguating entity/context in every question. Vary wording meaningfully; never change the fact or assume a personal student status.
5. Record the important exceptions, uncertainty, visual checks and coverage in review.md.

WRITE EXACTLY:
* `data/sections/{chunk_id}/facts.csv`
* `data/sections/{chunk_id}/questions.csv`
* `data/sections/{chunk_id}/review.md`

Important: valid CSV quoting and exact headers. IDs like `{chunk_id}_F0001`, `{chunk_id}_Q0001`; no blank IDs. Do not create negative/out-of-scope examples here. Do not modify any other files. If files exist from an earlier failed section run, fix them rather than duplicating IDs. Conclude with a compact count and unresolved issues, without copying rows into the chat response.
