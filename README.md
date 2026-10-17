# RHU undergraduate catalog: Claude QA dataset harness

**Purpose:** A complete, restartable Claude workflow to **generate** a sourced knowledge base and labeled English question-classification dataset from the **RHU 2026–2027 429-page undergraduate catalog**. The package includes the source PDF, **68 independent PDF/text chunks**, planning prompts, strict CSV contracts, local validation/merge scripts, and tests.

**Start here:** `docs/RUNBOOK.md`. Context: `docs/PROJECT_BRIEF.md`. Rules Claude follows automatically: `CLAUDE.md`.

## Four essential commands

```bash
python scripts/run_claude.py plan
python scripts/run_claude.py next
python scripts/workflow.py status --all
python scripts/workflow.py finalize
```

Claude Code must be installed and authenticated by the user for the first two commands. For a bounded batch use `python scripts/run_claude.py batch --count 3`. No Anthropic API key is bundled. Section PDFs and source texts are **already generated**; PyMuPDF is needed only for rebuilding chunks.

## Expected generated data

`data/plan/labels.json`, `data/plan/plan.md` → `data/sections/S001..S068/{facts.csv,questions.csv,review.md}` → `data/final/{RHU_QA_ALL.csv,RHU_FACTS.csv,RHU_QA_TRAIN.csv,RHU_QA_VALIDATION.csv,RHU_QA_TEST.csv,RHU_RETRIEVAL_PASSAGES.csv,QUALITY_REPORT.json}`.

The final dataset is **not pre-generated**: Claude plans and fills the CSVs when you run the harness. All output directories are initially empty except for placeholder files. Any section can be retried without overwriting another section. Sentiment analysis is explicitly postponed.

**Caution:** Automatic validation verifies labels, quoted source anchors, pages, data shapes, duplicates and split grouping. It cannot guarantee semantic accuracy of AI-generated answers. Human review of policy, numerical and flagged rows is required before scientific benchmarking or deploying university guidance.
