# RHU 2026–2027 undergraduate catalog QA dataset: plan

Taxonomy: 11 categories, 36 intents (`labels.json`). Labels are **frozen** once the first section is written.

## 1. Taxonomy decision boundaries
Classify by **what the student asks**, not by where the answer sits.

| Situation | Label |
|---|---|
| "What is COSC 333 about?" | courses / course_description |
| "How many credits is COSC 333?" / "Is it 3(3,0)?" | courses / course_credits |
| "What do I need before COSC 333?" incl. corequisites, junior/senior standing, CGPA conditions | courses / course_prerequisite |
| "Is CCEE 411 the same as COSC 333?" | courses / course_equivalency |
| "Is COSC 435 an elective in CS?" / "Which math courses are required in CS?" / gen-ed area lists | programs / program_requirements |
| "When do CS students take COSC 316?" / "What's in Year 2 Semester 1?" | programs / study_plan |
| "How many credits is the BS in CS?" / credit distribution tables / minor credit totals | programs / program_credits |
| Program mission, objectives, outcomes, ABET accreditation, careers, "currently frozen" | programs / program_overview |
| University-level mission/history/accreditation, campus | university_info / about_university |
| Office location/phone/email/responsibilities | university_info / office_contact |
| "Who is the chair of CMS?" | university_info / staff_faculty_role (faculty name lists: one fact per role, not per person biography) |
| Remedial courses demanded **for entry** by school track | admissions / admission_requirements |
| English entrance score, TOEFL/IELTS minimums, IELP placement | admissions / english_proficiency |
| Credits an IEP/IELP student may take | registration / course_load |
| Transfer conditions + transfer credit rules | admissions / transfer_admission |
| Application fee amount | fees_financial_aid / tuition_fees ; documents & where to apply → application_process |
| Drop/add, late registration, schedule modification | registration / registration_procedure |
| Repeat / substitute / graduate course for undergrad | academic_policies / repeat_substitute_course |
| Incomplete, grade appeal, change of grade, GPA computation | academic_policies / grading_gpa |
| Probation, dismissal, dean's list | academic_policies / academic_standing |
| Co-op weeks, timing, report, COSC 399 co-op rules in program text | coop_career / coop_training (the course-code prerequisite itself → course_prerequisite) |
| Specific dated event (2026–2027) | academic_calendar / calendar_date |
| Personal records, live schedules, balances | out_of_scope / live_data_needed |
| Anything the catalog does not document | out_of_scope / not_in_catalog |

## 2. Per-chunk extraction coverage
* Policy chunks (S001–S017): every student-actionable rule, threshold, deadline, fee, office contact and service. Skip boilerplate prose, generic mission adjectives beyond one fact per unit, and full personal biographies.
* Program chunks: degree awarded, total credits, credit distribution, frozen status, accreditation, mandatory/elective course lists (grouped by list, one fact per list or small sub-list), study-plan semester contents (one fact per semester), co-op/SLP rules, one compact overview fact (mission/outcomes/careers).
* Course descriptions: per course (a) `course_description` (title + compact topic summary), (b) `course_prerequisite` (including "Prerequisite: None", corequisites, standing), (c) `course_credits` (credit notation `3(3,0)` = 3 credits, 3 lecture hrs, 0 lab hrs), (d) `course_equivalency` only when stated. Table-only repetitions of a prerequisite already described in a course description in the same chunk are not re-extracted.
* Faculty lists: one fact for chairperson/dean per department; one fact listing full-time faculty by rank only if student-useful. Adjunct name lists skipped.

## 3. Atomic fact definition
One independently verifiable claim answering one intent about one entity, e.g. "COSC 421 prerequisites: COSC 215 and MATH 210." Conditions/qualifiers stay inside the same fact (e.g. "21 credits if CGPA ≥ 85 …"). A list that answers one question (required documents, TOEFL thresholds) can be one fact. Never mix unrelated claims.

## 4. Question variant strategy
* 2–4 questions per fact; 2 for routine course facts, 3–4 for policy/admission/fee facts with varied phrasing.
* Styles: `direct` (formal question), `paraphrase` (different wording/synonyms), `contextual` (student situation: "I'm a CS sophomore…" without asserting personal records), `short` (terse search-style: "COSC 214 credits?" ≥ 12 chars).
* Always include the disambiguating entity (course code, program name, "at RHU"). Questions must be globally unique: include the code/program and vary templates across chunks.

## 5. Exclusions
Sentiment/feedback data; graduate catalog content; adjunct name lists; biographies; decorative mission adjectives repeated per department; page headers/footers; any fact citing a page outside the assigned chunk.

## 6. Numeric/table verification and evidence
* `source_quote` = short exact substring of the cited page in `source.txt` (whitespace-insensitive, case-insensitive). Prefer a quote on a single extracted line or consecutive lines joined by one space; preserve hyphenation and curly apostrophes as extracted.
* For tables with scrambled column order (study plans, IEP table, multi-column credits), check `chunk.pdf`; if the extraction order makes a value uncertain, set `needs_review`.

## 7. Conflict policy
Program totals on p.28 vs program-section tables, study-plan prerequisites vs course-description prerequisites, internal contradictions (e.g. a maximum-load sentence that is grammatically ambiguous): record each claim as its own fact with its own page, mark `needs_review`, explain in `review_note` and `review.md`. Never silently correct.

## 8. Grouped evaluation strategy (70/15/15)
`workflow.py finalize` groups facts by (intent, entity, attribute, answer) and splits groups per intent ~70/15/15 using a deterministic hash, so all paraphrases of a fact land in one split (no leakage). Intents with < 7 groups stay in train (reported in `intent_split_gaps`). `needs_review` rows are excluded from training splits. Negative questions (optional) are hashed separately.

## 9. Minimal testing approach
1. `python scripts/workflow.py check-plan` → taxonomy valid.
2. `python scripts/workflow.py validate Sxxx` after each chunk (headers, IDs, page range, quote found, labels, duplicates, 2–4 questions).
3. `python scripts/workflow.py status --all`, then `finalize` (cross-chunk duplicate questions, split report).
4. Model sanity check later: TF-IDF + logistic regression on train, report macro-F1 on validation; per-intent confusion; human review of all `needs_review` facts and a random sample of drafts.
