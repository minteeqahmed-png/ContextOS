# Visual recall and the outbound review gate

Implemented October 24, 2026. Default: `LOCAL_ONLY`. `REMOTE_FAST` is intentionally not enabled.

## Run hybrid mode

The server and launcher load literal settings from local `.env`; existing process environment takes precedence. `.env` is git-ignored but stored unencrypted on disk. `.env.example` documents the complete configuration. In the PowerShell terminal that will start the server:

```powershell
$env:CONTEXTOS_MODE='HYBRID_SANITIZED'
$env:CONTEXTOS_REVIEW_POLICY='interactive'
$env:CONTEXTOS_VISION_PROVIDER='openrouter'
$env:CONTEXTOS_VISION_BASE_URL='https://openrouter.ai/api/v1'
$env:CONTEXTOS_VISION_MODEL='meta-llama/llama-4-maverick'
$env:CONTEXTOS_OPENROUTER_PROVIDER='digitalocean'
$secret = Read-Host 'OpenRouter API key' -AsSecureString
$env:OPENROUTER_API_KEY=[System.Net.NetworkCredential]::new('', $secret).Password
python server.py
```

The OpenRouter endpoint catalog listed `digitalocean` for this model when checked October 24. This is a configurable recipient, not a guarantee of availability, retention policy, or speed. Requests pin that upstream, disallow fallback and request `data_collection: deny`. If that route is unavailable or incompatible, inference fails locally; the app never relaxes the routing policy. See https://openrouter.ai/api/v1/models/meta-llama/llama-4-maverick/endpoints . An OpenRouter key is sufficient; no OpenAI key is needed.

For another hosted Meta endpoint, use `CONTEXTOS_VISION_PROVIDER=openai_compatible`, its HTTPS `/v1` base URL, model identifier, and `CONTEXTOS_VISION_API_KEY`. Its retention policy must be checked separately. Local Ollama always uses a loopback HTTP endpoint; embeddings never use the hosted provider. Configuration is server-side and is not accepted from browser requests. Remote configuration is not proof of a successful connection.

## Capture, review, enrichment

1. Commit the original image/PDF, searchable metadata and SQLite work record together. Acknowledge without waiting for OCR, PDF rendering or vision. A PDF with an invalid page or parser error is retained with failed processing, rather than rejected after slow parsing.
2. One CPU worker renders PDFs and runs OCR in a subprocess with a 90-second default deadline. Timeout terminates the child. Text and original OCR coordinates remain local. PDF native text is retained; hybrid PDF processing also OCRs the rendered pixels to detect tokens in embedded graphics.
3. Compute a DCT perceptual hash and flag close frames within the same session. Never merge or discard originals.
4. Hybrid frames enter the vision stage `PENDING_PRIVACY_REVIEW`. The detail view opens the proposed flattened PNG and exact JSON payload. Regex rules mask detected emails, common API-key forms, labeled secrets and long account-like digit strings. Entire detected OCR rectangles are covered with padded opaque black masks. No NER model is currently implemented; regex/OCR detection is incomplete and is never described as anonymization.
5. Drag additional masks, or enter normalized coordinates using keyboard controls. Updating a mask disables approval until the server generates a new preview/payload. A digest binds approval to the revision, exact image, prompt, model, endpoint and upstream. Reprocessing revokes approval. `Keep Local Only` removes pending approval and skips remote inference. No background auto-upload occurs in product mode, even when detection reports no secrets.
6. Approve & Enrich persists the approved copy and durable vision job. A separate worker requests structured visual entities, chart trends, layout and relationships from the Meta model. Strict response validation rejects invalid regions or malformed JSON. Descriptions stay separate from literal OCR; retrieval marks descriptor-only matches as possible visual matches. Existing local SQLite vector/BM25 retrieval is retained; ChromaDB migration has not been implemented.
7. From a retrieved frame, choose Verify visual relationship. Query text is sanitized locally and the user reviews the exact new payload. Hybrid verification reuses only the approved image. No original, raw OCR, filename, session or URL is implicitly appended. A supported response must contain two distinct valid region boxes. These are model-inferred citations, not proof of correctness; the displayed image lets the user verify them. Unsupported/invalid responses produce no asserted answer. The MVP verifies one selected retrieved frame at a time.

Privacy review is a mandatory product step, not a claim that OCR detected every secret. Human review remains necessary. Once a request has already been transmitted, deleting the local memory cannot recall it from a provider. Local deletion removes original, derived data, work records and review/grounding records. Storage is not encrypted at rest. No external analytics or assets were added.

## Timing and recovery

`capture_ack_ms` measures server work through the first durable artifact/job commit, excluding browser capture/upload and response transport. `text_ready_ms` measures elapsed time from capture acceptance to completion of extraction when actual OCR/annotation text exists. `extraction_finished_ms` is recorded even when no text is recovered. `vision_ready_ms` includes queue/review wait, inference and embedding enrichment; `vision_inference_ms` isolates the model request and response validation. Missing metrics mean the corresponding stage has not succeeded, not zero latency. Reprocess measures from the original capture time in this MVP. A sub-three-second model call is a target to measure, not a guarantee.

SQLite jobs resume after restart; OCR and vision queues are independent. Run a single application process per database. A crash during an outbound request can cause an approved job to be retried at restart (at-least-once delivery, potentially another billable inference). Failed vision preserves local searchable evidence. Use Reprocess locally to revoke old approval and retry from a new review. Session/date filters and all retrieval still execute locally.

## Test-only bypass

Default `CONTEXTOS_REVIEW_POLICY=interactive`. The alternate `auto_approve_sanitized` policy is accepted only with all of:

- `CONTEXTOS_TEST_RUN=1`;
- explicit `CONTEXTOS_DB` and `CONTEXTOS_FIXTURE_MANIFEST` paths;
- an image whose raw SHA-256 appears in the manifest's `image_sha256` array;
- successful OCR and no high-risk/uncertain-box warnings.

Ordinary captures cannot declare themselves fixtures via the API. A missing hash or detection warning leaves the frame pending. Use an isolated disposable DB; never enable this policy for the personal library. The flag approves ingestion only; query grounding still needs an explicit proposal approval. A benchmark runner may approve that proposal for its known fixture query.

## Validation status

Tests cover blocked OCR acknowledgment, durable work records, no upload before approval, automatic/manual masking, unchanged originals, failed OCR, stale/provider-changed approvals, local-only rejection, duplicate preservation, cascade deletion, query sanitization, exact approved-image reuse and malformed citations. Model responses in those tests are mocked. Live Meta inference, zero-keyword retrieval accuracy and hosted latency remain unverified without credentials and an actual run. Existing text-retrieval numbers must not be presented as vision performance.
