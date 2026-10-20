# Delegation log · goLocal poster extraction

### Entry 1 · Image extraction and uncertainty routing

- **Task:** Build an image-to-structured-event slice with evidence, a single Gemini call per image, 1024 px downscale, a pure decision function, and offline tests.
- **Delegated to:** AI coding agent, given the GoLocal specification, AGENTS.md, lecturer Lab 3 reference, five manually reviewed posters, and three additional phone photos.
- **Plan check:** The requester added the requirement that all five real posters be used. The implementation includes a five-image evaluator against `data/posters/posters.json`.
- **Came back wrong:** The first test run used a 10 MB byte string as an unnamed pytest parameter, causing an enormous failure report; the test now uses a short parameter ID. The environment's default pytest temporary folder was inaccessible, so verification uses the repository's ignored `tmp/` directory.
- **Caught by:** Running the focused offline tests and inspecting the supplied photos. The hand-written `??` date was not mislabeled as a clean test, and the book cover's real author name was not placed in the formal four-photo set.
- **Decision:** Fixed test setup and kept the three supplied photos as candidates pending compliant clean/ambiguous/nonposter photos and a controlled live run. No merge or course tag is claimed.
- **AGENTS.md change:** Added the rule that low-confidence poster fields must not be prefilled and that missing details stay null.
- **Cost:** One failed focused test run due to the long ID, two temp-path setup retries, then a passing focused run. No paid model calls were used for automated tests.

### Entry 2 · Source-grounded event RAG

- **Task:** Build local Markdown chunking, Gemini embeddings, a versioned file index, hybrid retrieval, cited JSON answers/refusals, CLI, offline tests and a live golden-set runner.
- **Delegated to:** AI coding agent, after the requester approved a file-based index and asked that teammates' existing files remain unchanged.
- **Plan check:** Kept the 13 real corpus documents, PostgreSQL migrations, Nino's files and Ana's tests untouched. Added new RAG modules and tests, with small edits only to Archil-authored provider and documentation files.
- **Came back wrong / caught by:** The initial embedding request used camel-case `outputDimensionality`; a check against Google's REST example showed `output_dimensionality`, which was corrected before testing. The focused offline suite then passed. No provider answer quality is inferred from those tests.
- **Decision:** Use the ignored local index for this slice; keep threshold `0.45` and `k=5` provisional until a live golden run permits one-setting tuning. Do not weaken or delete golden questions to improve the pass rate.
- **Cost:** 28 new offline RAG tests passed; the full repository suite passed 186 tests. No paid model calls were made by automated tests. The user performed one live index build and three live 10-question golden runs, scoring 3/10, 7/10 and 9/10 under the original scorer. The third run used bounded retries; a post-run audit found that one refusal passed due to model timeout, leaving 8/10 source-based passes. The scorer now rejects provider-failure refusals. Provider usage lines record available token counts and latency without prompt or key content.
