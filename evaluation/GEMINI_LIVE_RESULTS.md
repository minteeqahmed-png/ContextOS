# Gemini live smoke test — October 26, 2026

Model: `gemini-3.5-flash-lite`, Google OpenAI-compatible endpoint. Saved key loaded locally; no credentials logged. Only a generated 800×500 chart was transmitted. No personal captures were uploaded. Main library and running app configuration were unchanged.

Reproduce explicitly (makes remote requests): `python evaluation/test_gemini_live.py`.

Final run through the production `vision_privacy.payload`, `infer`, `Descriptor`, and `Grounding` functions:

| Stage | Observed latency | Result |
| --- | --- | --- |
| Visual description | 3,448 ms | Valid schema; correctly described green line dipping then rising steeply |
| Query-time grounding | 2,485 ms | Valid schema; identified red circle below and slightly right of green peak; two distinct supporting regions |

Artifacts: `output/gemini-live/synthetic-chart.png`, `report.json`, and raw response JSON files. Output is ignored by Git.

Initial attempts failed schema validation because the provider returned each box as `[[left, top, right, bottom]]`. Production validation now unwraps exactly one rectangle, while still rejecting ambiguous multiple boxes and invalid coordinates. Prompts also clarify the required flat format. Early responses included an inaccurate line bounding box; the final response enclosed the line. This demonstrates why schema validity alone cannot establish visual accuracy.

This is a single authored fixture, not a representative accuracy evaluation. Latency excludes capture, OCR, privacy review, indexing and retrieval. The descriptor exceeded the proposed three-second target. This script directly exercises the vision client with its known synthetic fixture; it does not demonstrate the interactive approval flow or end-to-end retrieval. No billing/free-quota assertion is made. Gemini does not demonstrate Meta model usage or establish hackathon eligibility.
