# Locked output contracts and quality rules

## Phase 1: taxonomy and plan
`data/plan/labels.json` must be a JSON object with two arrays:

```json
{
  "categories": [{"id":"academics","description":"Academic policies and study requirements"},{"id":"out_of_scope","description":"Not answered by this catalog"}],
  "intents": [{"id":"course_prerequisite","category":"academics","description":"Ask what must be taken before a course"},{"id":"not_in_catalog","category":"out_of_scope","description":"No documented answer"},{"id":"live_data_needed","category":"out_of_scope","description":"Requires current or personal records"}]
}
```

This is an **illustration, not an exhaustive approved taxonomy**. Claude plans a useful stable taxonomy (typically 10–20 broad categories; intents should be recognizable from a question without looking up its answer). Every intent belongs to exactly one category. The `out_of_scope` category and the two shown reserved intents are mandatory. Use lower snake_case IDs; describe decision boundaries and tricky examples in `data/plan/plan.md`.

## Phase 2: each chunk's facts.csv
Write `data/sections/Sxxx/facts.csv`. **Exact header and order:**

```csv
fact_id,chunk_id,source_pages,source_quote,category,intent,entity,attribute,answer,review_status,review_note
```

* `fact_id`: `S001_F0001`, `S001_F0002`, etc. Each fact is **one independently supported claim**, not a paragraph dump.
* `chunk_id`: assigned section, such as `S001`.
* `source_pages`: original absolute PDF page(s), e.g. `145` or `144;145`; **each must lie within the assigned chunk**. Pages separated by semicolons inside one cell.
* `source_quote`: short EXACT excerpt (10 to 420 characters) found in at least one cited source page text. Use a compact local anchor rather than the entire answer. If page text garbled, quote another verifiable substring and mark for review as appropriate.
* `category`, `intent`: locked IDs from plan; one intent maps to its category.
* `entity`: specific named course/program/office/policy (e.g. `COSC 333`), otherwise `RHU`.
* `attribute`: what the user asks (e.g. `prerequisite`, `course_credits`, `transfer_threshold`).
* `answer`: exact, concise student-facing answer based only on source. Preserve any stated thresholds, conditions, equivalencies and academic-year scope. Avoid mixing multiple unrelated claims or duplicating boilerplate across every course.
* `review_status`: `draft` or `needs_review`; do not claim `human_approved` yourself.
* `review_note`: blank for `draft`; clear reason if `needs_review`.

## Phase 2: each chunk's questions.csv
Write `data/sections/Sxxx/questions.csv` with exact header:

```csv
qa_id,fact_id,question,question_style
```

* IDs: `S001_Q0001` etc. Reference an existing fact from this chunk.
* Generate **2–4 varied English questions per meaningful fact**. Styles: `direct`, `paraphrase`, `contextual`, `short`. They should sound like questions from real students, not near-identical permutations.
* Keep the entity or course code in the question if needed to disambiguate. Do not assert things unsupported by the answer. No duplicate questions.
* Generate no answers here: the merger copies the answer and source reference from the fact. Avoid wasting context/tokens by repeating them.
* If a section has genuinely no useful information, write header-only CSV files and explain in `review.md`.

## Phase 2: review.md
Write `data/sections/Sxxx/review.md` briefly, recording the original PDF page range, coverage, uncertain page/table layouts, skipped non-student-useful material, apparent conflicts, and any manually unresolved sources. **Do not mislabel extraction as human-reviewed.**

## Optional phase 3: negative questions
`data/plan/negative_questions.csv` header:

```csv
question,category,intent,answerability,reason
```

Use `category=out_of_scope`; use either `intent=not_in_catalog` with `answerability=not_in_catalog`, or `intent=live_data_needed` with `answerability=live_data_needed`. Provide 30–60 **clearly unsupported or real-time/private** student queries. `reason` explains why the catalog cannot answer. Do not fabricate refusal answers or sources.

## Mechanical rules and known risks
* Check catalog text not general RHU web claims. Page 28 lists program degree credit totals; a later program table may differ. Mark conflict if encountered, do not overwrite one with the other.
* Facts repeated across different chunks are grouped by normalized intent, entity, attribute and answer to reduce cross-chunk train/test leakage; semantic near-duplicates still need review.
* A course can have a lecture/lab credit notation like `3(3,0)`. Preserve it and distinguish official credit total from weekly hours if both matter.
* Do not invent a prerequisite when absent. Distinguish prerequisite vs corequisite vs equivalent course.
* Preserve study-plan year/semester and college/program context for courses with repeated codes.
* If a course description continues to the next original page (especially across chunk boundaries), consult `boundary_context.txt` and PDF, but do **not** include facts citing out-of-range pages. Flag incomplete entries for the neighbor chunk's review; do not duplicate facts.
* Page/table extraction order is sometimes scrambled, so validate quantitative claims against the visual PDF. Source quotations must match the extracted text.
* Specific deadlines in the academic calendar are for **2026–2027**. Do not answer an open-ended current scheduling question as if those dates are always current.
* `training_eligible=yes` in merged output means only that the row has passed scripted source-anchor and structural checks, not human factual verification.
