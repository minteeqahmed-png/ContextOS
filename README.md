# ContextOS — evidence you can return to

A local recall workspace for browser/window frames, images, PDF pages, and notes. Search returns saved evidence with timestamps, session context, region highlights, and a source action. Visual relationship verification is available for a selected frame, with supporting regions and explicit outbound review in hybrid mode. See [PRIVACY_ARCHITECTURE.md](PRIVACY_ARCHITECTURE.md) for the new privacy gate, provider setup and limitations.

## Run on Windows

### Tested Gemini demo

Copy `.env.example` to `.env` only if you do not already have a `.env`, then put your Google AI Studio key after `CONTEXTOS_VISION_API_KEY=`. Do not commit or share that file.

Run `python start_gemini.py` and open http://127.0.0.1:8003. This explicitly enables Gemini `gemini-3.5-flash-lite` through Google's OpenAI-compatible API, with a separate `data/gemini-demo.sqlite3` library and interactive outbound review. Original frames, OCR and search stay local; approved sanitized copies and queries go to Google. This is not an entirely offline mode. Provider terms, quotas and billing settings apply.

The live demo uses Gemini; Meta/Ollama and OpenRouter integrations remain available but have not completed a live Meta acceptance test on this workstation. Local embeddings are unavailable in the measured demo: retrieval searches OCR and visual descriptions using local keyword/FTS ranking. Do not claim demonstrated dense semantic retrieval.

Run `python evaluation/full_demo.py` only when you intend to make live Google requests with its generated public fixtures. See `evaluation/GEMINI_LIVE_RESULTS.md` and `SUBMISSION_READINESS.md` for scope and measured results.

Python 3.12 is tested. From this directory:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python server.py
```

Open http://127.0.0.1:8000. In this workspace, dependencies are already installed in `.runtime`, so `python server.py` also works. `.runtime` takes precedence over the environment; for a clean deployment omit that folder and use the virtual environment. Install-time dependency downloads require internet. The installed OCR package includes local ONNX model files; inference does not fetch models.

## Capture and recall

- Choose **Capture a memory** (Alt+N while the app is focused). Capture one shared surface, import a PDF page/image, or save a note. Ctrl+K focuses recall. These shortcuts are app-local, not global OS shortcuts.
- Name a work session, such as **Product meeting**. Titles come from the imported filename or browser-provided surface label when available. Annotations are optional for images/PDFs.
- For PDFs, enter a one-based page number. The original PDF is retained in SQLite, the selected page is rendered, and native text coordinates are extracted. Scanned pages use offline OCR. One page per import, 8 MB upload limit, 24-megapixel image limit; encrypted PDFs remain saved with a processing error.
- Windows/tabs use the browser permission picker. Exactly one original PNG frame is captured and the stream is stopped in a finally block, including cancellation/error paths. The capture itself remains in memory until you save it.
- The browser cannot reliably expose an application's identity, original URL, or local file path. Surface labels are not represented as verified application names. Supply a URL manually to reopen it. Imported PDFs reopen the retained original at the selected page; arbitrary local files are never launched by the server.
- **Your captures** and **Examples** are separate. The six original sample cards are illustrative and excluded from real-capture queries. The included `Demo - Acme pricing.pdf`, if present, is a real import of an authored evaluation document, not a private user document.
- Search recognizes today, yesterday, recent weekdays, last/past week (rolling seven local days), and ISO dates. An unqualified weekday means its most recent occurrence, including today; “last Tuesday” on a Tuesday means seven days earlier. The browser sends its IANA timezone. A named session is inferred when all its content words occur in the query; use the explicit session dropdown for an exact filter.
- Click a result to see the original frame and extracted evidence. Clicking a text region highlights its source coordinates. Adjacent cells on a matching row are included. OCR can misread or join words; always verify critical numbers against the frame. Substring matching for query terms of four or more characters tolerates joined OCR words and can introduce loose matches, labeled as possible matches when coverage is low.

## Local models and Meta's role

Ollama is optional and is **not installed on the tested machine**. On a machine capable of running the vision model, install Ollama and explicitly download:

```powershell
ollama pull llama3.2-vision
ollama pull nomic-embed-text
```

In default `LOCAL_ONLY` mode, ContextOS connects only to loopback Ollama, disables environment proxies, and never invokes a remote model. Opt-in `HYBRID_SANITIZED` supports reviewed image copies through a configured Meta endpoint; see PRIVACY_ARCHITECTURE.md. No API key is needed for this local endpoint. Verify installed models in Settings, then use **Reprocess locally** on existing captures.

Meta Llama Vision supplies a structured visual description and inferred regions: layout, charts, colors, trends and spatial relationships. Query-time visual verification rechecks pixels and requires two supporting regions for a cross-element answer. It never replaces OCR or native PDF text. OCR uses RapidOCR's bundled ONNX models, not Meta. Nomic supplies local embeddings, also not Meta. New indexed captures contain whole-memory and up to 80 region embeddings. Search combines keyword coverage, SQLite FTS5 BM25 ranking, region evidence, and reciprocal-rank contributions from cosine similarity; vector-only hits are labeled possible matches. Without embeddings, the same interface searches text evidence.

A local model's presence is not proof that inference succeeded. Each capture shows extraction, vision, and embedding stages. Metadata/status checks report model availability; per-capture stages report actual outcomes. Real Llama/embedding inference remains unverified on this machine. No claim is made that Llama Vision fits or runs acceptably in its 8 GB RAM.

## Persistence, recovery, privacy

- `data/memories.sqlite3` stores frames, selected-page text regions, annotations, visual descriptions, vectors, and original PDF bytes. Existing captures/bookmarks are preserved. Legacy text is labeled as context with unverified provenance, not retroactively claimed to be OCR.
- Captures are saved before background OCR/model processing. Independent local-extraction and vision workers report their stages. Hybrid vision pauses at PENDING_PRIVACY_REVIEW while local text remains searchable. Missing optional models produce unavailable stage labels while text search remains usable. Failures keep the original and any available evidence. Reprocess retries after setup/recovery. Pending jobs resume on application startup. Run one server process against this database.
- Captures are immutable; bookmarking preserves derived evidence. To change an annotation or source, create a new capture. Reprocessing rebuilds extraction/descriptions/embeddings from the retained frame.
- Settings supports source exclusions matched against supplied titles, filenames, and URL fragments before persistence. It cannot identify or block apps whose identity the browser does not reveal. Exclusions do not retroactively delete saved memories. A native companion or browser extension would be required for reliably automatic active-tab URLs/global shortcuts/app-level policies; neither is installed or represented as implemented.
- Delete removes the memory, original PDF, OCR, descriptions, vectors, and FTS rows in a transaction. A concurrent worker cannot restore a deleted record. SQLite secure_delete is enabled; this is logical deletion, not a guarantee of forensic erasure from backups/storage hardware.
- No encryption at rest, account authentication, background recording, external analytics, or cloud sync. Processing latency metrics are stored locally. Approved sanitized copies and reviewed queries leave the device only in opt-in hybrid mode. Protect the local OS account. Localhost host/origin/fetch-site checks block ordinary cross-site browser access; they do not defend against malicious software already on the device.
- JSON export includes images and derived evidence, but not the original PDF binary. Open/download the PDF separately if needed. Exported copies are not affected by library deletion.
- PDF originals and jobs are committed before asynchronous rendering; invalid page/parser errors are recorded on the retained capture. Large/OCR jobs are serialized and may take tens of seconds on older CPUs. Original images are stored inline and returned in the library response; this MVP is intended for small libraries rather than thousands of captures.

## Validation and demo

```powershell
python -m unittest discover -s tests
node --check app.js
node --check evidence.js
node --check privacy-ui.js
python evaluation/create_sources.py
python evaluation/run.py
```

The evaluation uses four actual browser screenshots of local authored fixture pages and one imported PDF. Captures live in `evaluation/captures`; their HTML/PDF sources are in `evaluation/sources`. The evaluation database is isolated and deleted afterwards. Tuesday timestamps are explicitly simulated metadata for date tests. No private customer data is used.

`evaluation/output/report.json` records measurements, raw query results, hardware, extraction timings, and model availability. `baseline-report.json` preserves the first run, including failures. The tiny development fixture set is not a general accuracy benchmark or held-out evaluation. Non-loopback sockets are blocked during the run; no outbound attempts were observed. This tests network-independent processing, not an OS-level disconnected-network demonstration.

See DEMO.md for the three-minute script and VALIDATION.md for measured results and limitations.

## API summary

- GET `/api/status`: local dependency/model availability; GET `/api/memories`: library.
- POST `/api/memories`: image/text capture, optional session, source URL/reference, source kind, capture timestamp. Returns persisted captured state; poll GET `/api/memories/{id}` for processing stages.
- POST `/api/import/pdf`: base64 PDF, filename, page, session, optional source URL/annotation. Preserves original bytes and renders the chosen page.
- GET `/api/search?q=...&tz=Asia/Karachi&library=captures&session=...`: ranked IDs, evidence region IDs and exact quotes, match explanations, applied constraints, and actual search mode. `library` is captures/samples/all.
- POST `/api/memories/{id}/reprocess`; DELETE `/api/memories/{id}`; GET `/api/memories/{id}/original` for original PDF bytes.
- GET/PUT `/api/preferences`: source exclusion list. No filesystem paths or arbitrary inference URLs are accepted for execution.

## Hackathon readiness

Rechecked on October 24, 2026: https://cerebralvalley.ai/e/meta-ai-developer-hackathon explicitly mentions running Meta open-weight models, but says official rules will be published before October 26. The application waiver was not readable through the web fetch. No authoritative published provision confirming eligibility of pre-existing code was found. This is a working development MVP, **not confirmed submission-ready**. Recheck the published rules for allowed models, pre-event work, licensing, deliverables, and eligibility before submitting. Do not describe mock-tested model integration as demonstrated Meta inference.
