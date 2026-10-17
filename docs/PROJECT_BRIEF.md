# Project brief for Claude

## Goal
A university-student chatbot for Rafik Hariri University (RHU), developed as a **6–8 week NLP course project**. The eventual student interaction is: wake-word/voice trigger (optional interface) -> speech-to-text -> question preprocessing and **supervised question classification** -> knowledge retrieval within relevant category -> accurate answer with citation. Text-first chatbot is sufficient for the NLP core. A **separate later stage** will analyze student feedback with aspect-based sentiment (for example, one comment could praise registration and criticize advising). **Do not generate sentiment data in this phase.**

## This package's deliverable
Prepare a reliable **training, validation, and test dataset** for broad category and fine-grained intent classification, plus a structured catalog knowledge base for answer retrieval. Claude must (1) plan a small coherent taxonomy and coverage strategy, (2) read 68 self-contained chunks, (3) extract verifiable information, (4) write labeled student question variants, (5) mark problems, and (6) leave merging/splitting/validation to deterministic local Python scripts.

## Scope boundaries
* Authority: `source/RHU_Undergraduate_Catalog_2026-2027.pdf`, 429 pages. RHU policies can change and the document applies to 2026–2027. Include this scope in final assistant answers when relevant.
* Keep undergraduate degree, course descriptions, credit counts, program plans, prerequisite chains, transfer rules, calendar dates, fees, services, and university offices.
* Include degree status qualifiers such as currently frozen, prerequisite conditions, program/degree distinctions, and exceptions.
* No financial/account information for real students, personal grades or GPA, real-time class availability, 2027–2028 claims, external deadlines, or unsupported eligibility judgments. Teach classifier `out_of_scope` for these.
* No web scraping, OCR bulk processing, external model/API calls, audio model training, university integrations, or full chatbot implementation.
* No promise that generated paraphrases are genuine student questions. They are **synthetic training examples**; reserve the held-out tests and eventual student-collected examples for honest performance evaluation.

## Later model architecture
For the course project, start with TF-IDF + logistic regression/SVM for category and intent classification; optionally compare sentence embeddings. Retrieve from `RHU_RETRIEVAL_PASSAGES.csv` or fact records, with source page citations. Return an abstention or referral when the catalog cannot justify the answer. Classifier data and answer facts are **different assets**, even though they are linked.

## Source rules
Original PDF page numbering is **1 through 429** and matches the chunk page markers. The PDF occasionally has tables and text-order problems; cross-check the individual chunk PDF when needed. A quoted text match is NOT proof that the generated answer is semantically correct; flagged examples require review.
