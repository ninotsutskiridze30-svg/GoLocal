# Retrieval spec · GoLocal event documents

## Corpus and ownership

`data/corpus/events/` contains 13 manually compiled public-listing snapshots: 12 event-related pages and one pool/venue page. Each Markdown document stores its original `https://` source. The source page owner controls the live facts; GoLocal contributors own these local snapshots and must check them before updating. Events, entry rules, prices and availability can change at any time. The index is rebuilt after any corpus edit. These documents include real performer names, as requested for this project; the course's shareable-corpus guidance should be reviewed by the team before submission.

The corpus does not contain live seat availability, a ticket purchase flow, or all Georgian events. Never assert that a snapshot price or rule is current without checking its source. The pool page describes a venue, not a dated concert.

## Chunking and index

Split each Markdown document at `## ` headings. Prefix every chunk with its document title and section heading. Long sections use windows of at most 1,200 content characters with up to 180 characters of overlap; metadata in the prefix adds a few characters. Stable chunk IDs use `events/<filename>#<number>`. Reject a document without a title or valid HTTPS source URL.

Use Gemini `gemini-embedding-2` at 768 dimensions for both chunks and questions. `scripts/index_corpus.py` writes `logs/rag_index.json`, which is ignored by Git. It contains vectors, chunk metadata, model ID, dimension count and SHA-256 hashes of every corpus document. Loading refuses an altered corpus, model mismatch or tampered source mapping. PostgreSQL tables are unchanged.

## Retrieval and answer

Use hybrid ranking: 0.75 × nonnegative cosine similarity + 0.25 × normalized BM25, over Unicode word tokens. Return at most `k=5` chunks with score at least `0.45`. These settings remain provisional pending measured tuning. With no passing chunk, refuse before the generative model call. A question requires one query embedding call; a grounded answer normally makes one Gemini JSON completion call, with up to two retries for transient provider errors.

Gemini 3.1 Flash-Lite returns `{answer, citations, grounded}`. The service validates the shape, requires `grounded=true`, and requires every answer sentence to end with one or more `[n]` markers. Every marker must map to a retrieved chunk and exactly match the `citations` array. The application, not the model, attaches the source URL from the trusted corpus. An invalid marker, uncited sentence, malformed reply or explicit `grounded=false` produces a refusal. Source text is treated as data, never instructions. Citation validation proves provenance of a retrieved chunk; it does not independently prove every claim in model prose. Transient provider HTTP 429/500/502/503/504 or transport timeout may trigger up to two delayed retries; permanent errors and malformed content do not. One answer/refusal log line records the attempt count.

The refusal text is: “ამ კითხვაზე პასუხი ხელმისაწვდომი წყაროებით ვერ დავადასტურე. გადაამოწმეთ მითითებულ წყაროსთან ან დააზუსტეთ კითხვა.” A cited answer contains `[1]` in the text plus a citation object with the original title, section and URL. `logs/rag_answers.jsonl` writes one line for each answer/refusal with reason and retrieved IDs; it does not log the question, response body or key. Provider usage is written separately to `logs/rag_usage.jsonl`.

## Acceptance and evaluation

1. A supported question returns `answered` with only corpus-backed source URLs.
2. An unsupported question or a top score below `0.45` returns `refused`; the latter makes no generative model call.
3. Invented citations and uncited sentences are refused.
4. Every answer/refusal writes one structured log line.
5. `evals/golden.yaml` contains 10 preserved questions (factual, two-document reasoning, edge and refusal). `evals/run_golden.py` records a live run and requires at least 0.70 pass rate. Live runs on 2026-10-20 scored 3/10, 7/10 and 9/10 under the original scorer, with unchanged retrieval settings. The third used bounded retries and had one remaining HTTP 503 answer failure. One passing refusal came from provider timeout, so a source-based audit yields 8/10. The scorer now rejects provider failures as successful refusals. Retrieval settings remain provisional.

Automated tests use fake embeddings and model replies. No paid API calls or live ticket sites are required for pytest.
