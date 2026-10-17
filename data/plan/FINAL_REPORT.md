# RHU QA dataset — final report (2026–2027 undergraduate catalog)

Source: `data/final/QUALITY_REPORT.json` (finalize run 2026-10-17).

## Totals
| Item | Count |
|---|---|
| PDF pages / chunks | 429 / 68 (all valid) |
| Atomic facts | 1,513 (1,439 draft, 74 needs_review) |
| QA rows (incl. 40 negatives) | 3,212 |
| Training-eligible QA | 3,059 |
| Split (eligible) | train 2,163 · validation 449 · test 447 (≈71/15/15) |
| Retrieval passages | 1,014 |

Splits are grouped by fact (intent + entity + attribute + answer), so paraphrases of one fact never cross splits. `needs_review` facts are excluded from training.

## Facts per category
courses 756 · programs 380 · university_info 88 · academic_policies 57 · admissions 57 · academic_calendar 41 · registration 37 · student_services 33 · coop_career 33 · fees_financial_aid 31 · out_of_scope 40 negative questions.

## Known weaknesses
1. **Class imbalance.** `course_description` alone is 639 facts (42%). Six intents have fewer than 10 facts: career_services 2, scholarship_aid 3, repeat_substitute_course 4, study_duration_level 5, application_process 6, non_degree_admission 7. The catalog really is that thin on these; more data cannot be extracted without inventing facts. Options: class weights, merging tiny intents at the classifier level, or adding human-written paraphrases of the existing facts.
2. **Intents missing from splits.** These intents have no examples in some splits, so they cannot be evaluated there:
   - missing from both test and validation: application_process, career_services, repeat_substitute_course, scholarship_aid, study_duration_level
   - missing from test only: course_credits, not_in_catalog

   Fix: do a stratified re-split for these intents only, or report per-intent metrics only where support exists.
3. **Paraphrases are machine-generated.** Quote matching was checked automatically, but paraphrase quality and answer correctness have not been reviewed by a person.
4. **Negative questions.** In `negative_questions.csv`, check the rows that mention a named staff member, CampusVue and Moodle. These come from general knowledge, not the catalog.

## Human review needed
- 74 `needs_review` facts: catalog contradictions such as BS credits 116 vs 118, co-op 5 vs 8 weeks, prerequisite and credit mismatches between tables and course descriptions, calendar overlaps, and course-code typos. Each is explained in its `review_note` and in `data/sections/Sxxx/review.md`.
- Sample about 10% of draft rows per category before marking any as `human_approved`.
