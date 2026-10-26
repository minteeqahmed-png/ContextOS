# Submission readiness — October 26, 2026 (Asia/Karachi)

**Working Gemini prototype prepared; current Gemini-only build does not satisfy the supplied participant guide’s mandatory Meta-model requirement.**

## Verified this session

- Gemini launcher on port 8003, separate local demo database and interactive privacy gate.
- Real local OCR, approval digest, remote vision indexing, local retrieval, query-time grounding, source endpoints, SQLite persistence and cascade deletion exercised through production API routes.
- Three generated image imports: a dip/spike chart, a rising chart, and a terminal/browser layout. These are authored development fixtures, not actual browser-window captures.
- Four positive queries: top-1 3/4, top-3 4/4. One no-match query correctly empty. Median search 17.56 ms.
- Durable capture 164–294 ms; local OCR/text readiness 10.9–30.9 s; vision inference 9.4–16.5 s; total vision readiness 33.1–51.2 s including OCR/review. Grounding 8.12 s.
- Grounding correctly located a red circle relative to a green peak, with two valid boxes.
- Initial schema failures preserved in the local before-region-recovery report. Invalid model regions are now omitted with visible warnings; summaries and valid regions survive. No boxes are fabricated to repair errors.
- 27/27 regression tests passed in 64.249 s. JavaScript syntax checks passed. Browser UI verified search, original frame, highlights, Gemini provenance and source link; screenshot saved in submission/contextos-evidence.png. The prepared app library has two remaining fixtures because the rising-chart record was deleted during the deletion test; the four-query benchmark used all three.
- No live local embeddings; measured retrieval is keyword/FTS over OCR and generated visual descriptions, not demonstrated dense semantic search.

See evaluation/ACCEPTANCE_RESULTS.json for exact measurements and queries. Earlier one-image timings are not representative of this fuller run. Authored sources and reproducible test scripts are included in the source package.

## Submission materials

- SUBMISSION_DRAFT.md: truthful project description.
- DEMO.md: three-minute recording script and instructions.
- README.md and .env.example: local setup and Gemini configuration.
- package_submission.py: explicit source-only ZIP builder with saved-key leakage check.
- submission/ContextOS-source.zip and manifest.json: generated package. Local secrets, databases and runtime are excluded.

## Confirmed participant-guide requirements

The accepted participant supplied the guide on October 26, 2026. It explicitly requires incorporation of Meta models. Stage One checks reasonable use of Meta Model API and/or Meta open-weight models. Gemini alone is insufficient; provider scaffolding or a configured model name is not demonstrated model use.

- Public repository required.
- Accessible three-minute demo video required, highlighting only features/code/functionality built during the Hackathon.
- New work only. Existing-product extensions are explicitly permitted for startups when new contributions are identified. Do not assume the same exception applies to an indie entrant.
- Maximum four team members; list all contributors and designate a representative.
- Submit through https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit .
- Deadline November 4 at 9 PM ET = November 5 at 7 AM Pakistan time.

## Remaining work and eligibility questions

1. Obtain a region-accessible Meta provider and perform real indexing and grounding tests. Keep Gemini as a development fallback only.
2. Establish an honest pre-event baseline. Preserve existing code and reports; never backdate commits or describe pre-event functionality as new. Guide lists an October 26 kickoff but October 27–November 4 building period: ask organizers whether October 26 changes count and whether an indie entrant may build on this prototype.
3. Record and publish the actual video and public source repository after separating eligible contributions. No video or public repository has been published by this assistant.
4. Avoid presenting ContextOS as a basic RAG app/simple image analyzer, both listed as anti-projects. Demonstrate substantial event-built visual recall, evidence verification and privacy behavior; positioning alone does not guarantee acceptance.

## Available credits (participant guide)

Accepted participants can apply individually for $150 Meta Model API credits; the guide requires a valid payment card and mentions a temporary authorization charge. A spend-limit notification is not stated to be a hard spending cap. The assistant has not applied for credits or entered payment details.

Baseten offers selected participants $100 credits; use the event-specific model ID `meta-models/muse-spark-open-1026`. Modal offers $100 to the first 1,000 participants; Fireworks offers selected teams $25. Regional eligibility, account/payment requirements and actual access still need confirmation.

Source: participant-supplied guide at https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details . Rubric/prize tables were omitted from the supplied text; their contents are unknown.
