TASK: PLAN the RHU undergraduate catalog QA classification dataset. DO NOT write facts.csv or questions.csv yet.

Read `docs/PROJECT_BRIEF.md`, `docs/SCHEMA_AND_QA.md`, `config/manifest.csv`, and only these representative source files to learn the coverage:
* `chunks/S005/source.txt` (admission requirements)
* `chunks/S010/source.txt` (academic regulations)
* `chunks/S023/source.txt` (computer science courses and programs)
* `chunks/S043/source.txt` (civil engineering program)

Write exactly:
1. `data/plan/labels.json` as valid JSON according to the contract, with a manageable broad category and intent hierarchy. Choose a taxonomy useful for single-question category/intent classification. Reserve `out_of_scope` with `not_in_catalog`, `live_data_needed`. Avoid label explosion or labels tied to a specific individual course code.
2. `data/plan/plan.md`: taxonomy boundaries, intended per-chunk extraction coverage, QA variant strategy, what counts as atomic fact, exclusions, numeric/table verification, evidence handling, conflict policy, 70/15/15 grouped evaluation strategy, and a minimal testing approach.

Ensure there is exactly one category for each intent, category/intent names are not ambiguous, and all major content areas in the section manifest are covered. Do not scan all chunk text during planning. No external web sources. Keep both planning files concise and operational. Do not edit configs, source files, scripts, or prompts.
