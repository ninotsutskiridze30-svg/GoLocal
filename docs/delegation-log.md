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
