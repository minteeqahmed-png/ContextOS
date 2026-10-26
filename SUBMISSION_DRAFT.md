> Baseline only: the supplied guide requires Meta model use and event-built contributions. This Gemini prototype/script is not yet an eligible final submission. Revise after real Meta testing and confirmation of the permitted build period.

# ContextOS

**Return to the thing you remember seeing—even when you cannot remember its words.**

ContextOS is a local-first visual recall prototype for screenshots and PDF pages. Capture a frame explicitly, give it an optional session, and later search by a remembered chart trend or screen layout. Results return the original evidence, extracted text, timestamp, source link and estimated visual regions rather than an unsupported chatbot answer.

The demonstrated configuration uses Gemini 3.5 Flash-Lite for structured visual descriptions and query-time pixel verification. Local RapidOCR preserves extracted text separately. SQLite FTS and keyword ranking search OCR, descriptions and metadata. Optional local embeddings and Meta Llama providers are implemented but were not active in this demonstration.

Originals and search remain local. A mandatory review shows the sanitized image and outbound prompt. Users can add opaque masks, approve that copy or keep the frame local. Relationship verification reuses the approved copy and requires two valid supporting regions. Captures persist before asynchronous extraction; a failed model never discards the original.

On three authored synthetic image imports, four positive queries achieved 75% top-1 and 100% top-3 retrieval; one no-match case passed. Median local search latency was 17.56 ms. Capture persistence took 164–294 ms; OCR readiness took 10.9–30.9 seconds. Vision inference took 9.4–16.5 seconds. A grounded relationship answer took 8.12 seconds. These are small development-set measurements, not production benchmarks. All 27 automated regression tests passed.

Limitations: no verified live Meta inference, no active dense embeddings, imperfect estimated boxes, slow CPU OCR, manual source URLs for screen captures, and no encryption at rest. Remote mode sends approved data to Google and depends on internet access. Audio and background recording are intentionally deferred.

## Before pasting into the event form

- Confirm the organizers allow the Gemini-based implementation and pre-event code. Do not claim Meta powers this demonstrated build.
- Add actual source/repository and recorded demo URLs when available.
- Match fields and required deliverables to the accepted-participant event details.
- This is an accurate project draft, not a claim of competition eligibility.
