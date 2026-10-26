# October 24 privacy-gate implementation check

A real browser screenshot of the authored growth-chart fixture was ingested into an isolated hybrid-mode database with interactive review. Measured server durable-save time: **478.88 ms**; HTTP capture response: **1,318.04 ms**; cold OCR/text-ready: **77,279.84 ms**, producing 10 text regions. Vision remained `PENDING_PRIVACY_REVIEW`; no remote request was approved. This is one smoke run, not a latency distribution. Results are in `evaluation/output/privacy-smoke.json`.

Automated validation: **24 tests passed** (40.322 seconds); Python compilation and JavaScript syntax checks passed. Browser testing confirmed the original frame, pending-review state, outbound recipient/payload disclosure, drag-to-mask, disabled approval after a mask change, and regenerated opaque-mask preview. `contextos-privacy-review.png` records the preview. Model responses in automated privacy/grounding tests are mocked; live Meta inference and visual-semantic retrieval accuracy remain unmeasured. The process has no OpenRouter API key. No sub-three-second hosted inference result is claimed.

The earlier OCR retrieval evaluation below predates the new privacy pipeline and is retained as historical evidence, not a benchmark of the visual hero task.

---

# Validation record

Measured run: October 23, 2026, 16:36 Asia/Karachi. Raw results: `evaluation/output/report.json`. The initial run with failures is retained as `evaluation/output/baseline-report.json`.

## Environment and dataset

- Windows 10, Python 3.12.4, Intel Core i7-6920HQ @ 2.90 GHz, 7.9 GiB RAM. OCR/PDF processing ran on CPU; no GPU inference was tested.
- Four real 1280×720 browser screenshots of locally authored pages: Acme pricing, a growth chart, React code, and a competing vendor price table. One real import/render of an authored PDF.
- Timestamps are explicitly simulated Tuesday metadata in an isolated evaluation database. Live demo captures keep actual capture times.
- RapidOCR 1.4.4 and PyMuPDF 2.0 installed. No Ollama vision or embedding models available. Results below measure OCR/PDF extraction and text evidence retrieval, not semantic model performance.
- The labeled queries are development fixtures used to find and fix defects; they are not held-out data. Ambiguous pricing queries accept more than one relevant document.

## Results

| Metric | Result |
|---|---:|
| Positive queries | 8 |
| Expected document at rank 1 | 8/8 |
| Expected document within top 3 | 8/8 |
| Correct no-match queries | 2/2 |
| Median search latency | 56.62 ms |
| Maximum search latency | 91.12 ms |
| Browser image processing | 17.2–54.6 s per capture |
| PDF import + processing | 24.5 s |
| Non-loopback connection attempts | 0 |

The original run retrieved 6/8 positives. Two failures came from joined OCR words. Retrieval now tolerates longer query fragments within joined OCR tokens, while retaining the untouched OCR text. The same queries were rerun; improved accuracy on them is not evidence of broad generalization. Background app activity and cold imports affected processing latency; no controlled speed comparison is claimed.

## Automated and manual coverage

All 12 automated tests passed in the final verification; both JavaScript modules passed syntax checks. The test suite covers persistence, sample separation, source exclusions, invalid source URLs, invalid PDF pages, original PDF retrieval, normalized region coordinates, text search, no-match cases, timezone boundaries, joined OCR words, neighboring price-cell highlights, model absence, failed extraction/reprocessing, deletion of artifacts/index rows, and deletion while a worker is active. Model failure/embedding branches use mocks; genuine Meta inference is not tested.

The evaluation runs with non-loopback socket connections blocked. OCR and PDF inference run on actual installed local libraries. A separate test forbids HTTP clients during the no-model PDF pipeline. This is stronger than merely hiding a status icon, but is not equivalent to turning off the machine's network adapter.

Browser verification covers the new capture form, session persistence, real-capture library state, backend processing status, retrieval of the imported PDF, and highlighting the Pro / $49 / Unlimited row. The original-PDF endpoint returned the retained 2,701-byte PDF with HTTP 200. A screenshot is saved as contextos-evidence.png. Screen-picker permission and native OS metadata remain browser-dependent; do not claim a global hotkey or automatic URL capture.

## Remaining limits

- Real Llama Vision and embedding inference still require installation and verification on suitable hardware. No API key is needed for Ollama's local endpoint.
- OCR is imperfect: one vendor-price screenshot omitted the $79 cell. Retained frames are authoritative; the application does not fabricate the missing number. Code punctuation can also be misread.
- Date interpretation is deterministic and limited to the documented patterns. Session inference is token-based, with an exact session dropdown available.
- One PDF page per import. No live audio, continuous recording, native companion, browser extension, encryption at rest, or forensic deletion guarantee.
- Libraries load inline frames; large-scale pagination/storage optimization is deferred. A single worker/process is supported; embedding at most 80 individual regions per capture bounds work.
- Official hackathon rules and pre-existing-work eligibility remain unconfirmed. Event source: https://cerebralvalley.ai/e/meta-ai-developer-hackathon (rechecked October 24, 2026).
