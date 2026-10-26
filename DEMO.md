> Baseline only: the supplied guide requires Meta model use and event-built contributions. This Gemini prototype/script is not yet an eligible final submission. Revise after real Meta testing and confirmation of the permitted build period.

# Three-minute demo — tested Gemini configuration

Start `python start_gemini.py`; open http://127.0.0.1:8003. Use Chrome or Edge for the screen-sharing picker. The prepared local demo library contains imported synthetic chart/layout fixtures processed by real OCR and Gemini. They are demonstration data, not customer captures. A fresh setup starts empty; import `evaluation/sources/visual-dip.png` and `visual-layout.png`, then review and approve each.

## 0:00–0:20 — Problem

“I remember the green line dipping and then shooting upward, but none of the words. ContextOS brings me back to the actual frame.” Show the chart source at `/demo/visual-dip.png`.

## 0:20–0:55 — Deliberate capture

Capture that tab using Capture a memory → Window or tab, or import the included image. Use session **Visual demo** and enter the source URL. Save and point out the durable acknowledgment and separate extraction/vision stages. Screen sharing ends after one frame.

“OCR and storage happen locally. Heavy vision runs later. Nothing goes to the provider until I review it.” Use a prepared frame if extraction is still running; explicitly say it was processed earlier. Never hide the wait as instant inference.

## 0:55–1:25 — Privacy review

On the fresh frame, open Review outbound frame after OCR finishes. Show the recipient, model, image and JSON payload. Demonstrate an optional mask outside the chart, update the preview, and approve. Explain that automatic redaction can miss details and the unredacted original stays local.

## 1:25–2:05 — Recall with evidence

Search **green line dips then rises steeply**. The expected chart was second in the three-image evaluation; inspect ranked candidates rather than claiming perfect top-1 accuracy. Open the matching chart, show its original and separately labeled OCR/model descriptions. OCR contains only the generic heading; Gemini supplies the visual trend. Show timestamp, session and inferred region highlights. Explain that estimated boxes can be inaccurate.

## 2:05–2:35 — Verify relationship

Choose Verify visual relationship. Ask **Where is the red circular indicator relative to the high point of the green line? Cite both regions.** Review the approved copy and sanitized question, then approve. Show the two supporting boxes. Say “This is a model interpretation checked against these pixels, not a guaranteed fact.”

## 2:35–3:00 — Return and limits

Use Reopen source. Search **purple elephant submarine** to show no match. Close with measured 75% top-1 / 100% top-3 on four positive development queries. State: “This demonstrated build uses Gemini; Meta integration is available but not live-validated.”

## Recording checklist

- Record the actual browser and narration using your preferred recorder. No final video has been produced automatically.
- Exclude .env, account screens and private windows.
- Use only public authored fixtures; do not pretend synthetic imports are third-party browser captures.
- Label wait-time edits and pre-indexed examples.
- Save the video and add its actual link to the form after checking the event's permitted format.
