import { createPrivacyUI } from './privacy-ui.js';

export function createEvidenceUI(c) {
  const { esc, icon, request, modal, modalTitle, toast, closeModal } = c;
  let draft = null;
  let pendingStream = null;
  let generation = 0;
  const privacy = createPrivacyUI(c);

  const sourceLink = m =>
    m.has_original
      ? `/api/memories/${encodeURIComponent(m.id)}/original#page=${m.page || 1}`
      : /^https?:\/\//i.test(m.source_url || '')
        ? m.source_url
        : null;

  const isVisualRegion = r => ['meta-vision-inferred', 'vision-inferred'].includes(r.method);

  const stages = m =>
    Object.entries(m.stages || {})
      .map(([name, value]) => `<span class="stage ${esc(value)}">${esc(name)}: ${esc(value)}</span>`)
      .join('');

  const formatMs = ms => (ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${Math.round(ms)} ms`);

  function renderTelemetry(telemetry) {
    if (!telemetry || !Object.keys(telemetry).length) return '';
    const labels = {
      capture_ack_ms: 'Ack',
      text_ready_ms: 'Text ready',
      extraction_finished_ms: 'Extraction',
      vision_inference_ms: 'Vision model',
      vision_ready_ms: 'Total pipeline'
    };
    const entries = Object.entries(telemetry)
      .filter(([k]) => !(k === 'extraction_finished_ms' && telemetry.text_ready_ms))
      .map(([k, v]) => `<span class="telemetry-pill" title="${esc(k)}: ${v} ms">${esc(labels[k] || k)} · ${formatMs(Number(v))}</span>`);
    return `<div class="telemetry-strip">${entries.join('')}</div>`;
  }

  function renderRegionBox(r, label = '') {
    const cls = isVisualRegion(r) ? 'region-highlight is-visual' : 'region-highlight';
    return `<div class="${cls}" title="${esc(r.text)}" style="left:${r.box[0] * 100}%;top:${r.box[1] * 100}%;width:${(r.box[2] - r.box[0]) * 100}%;height:${(r.box[3] - r.box[1]) * 100}%">${label ? `<span class="region-pin-badge">${esc(label)}</span>` : ''}</div>`;
  }

  async function detail(id) {
    let m = c.getMemory(id);
    if (c.isApi()) {
      try {
        m = await request('/memories/' + encodeURIComponent(id));
      } catch (e) {
        toast(e.message);
        return;
      }
    }
    if (!m) return;

    const result = c.getEvidence(id);
    const matched = new Set(result?.region_ids || []);
    const link = sourceLink(m);
    const regions = [...(m.regions || []), ...(m.visual_regions || [])];
    const ocrRegions = regions.filter(r => !isVisualRegion(r));
    const visualRegions = m.visual_regions || [];

    const defaultOverlayHtml = () =>
      regions
        .filter(r => matched.has(r.id))
        .map(r => renderRegionBox(r))
        .join('');

    modal(
      `${modalTitle(m.title)}
      <div class="evidence-meta">
        <span class="tag">${m.sample ? 'Illustrative sample' : 'Original capture'}</span>
        <span class="meta-chip">${esc(new Date(m.date).toLocaleString())} · ${esc(Intl.DateTimeFormat().resolvedOptions().timeZone)}</span>
        ${m.session ? `<span class="meta-chip">Session: ${esc(m.session)}</span>` : ''}
        <span class="meta-chip">${esc(m.origin)}${m.page ? ` · page ${m.page}` : ''}</span>
        ${m.vision_provenance?.model ? `<span class="meta-chip provenance">Vision: ${esc(m.vision_provenance.model)}</span>` : ''}
      </div>
      ${result ? `<div class="match-explanation"><strong>${esc(result.label)}</strong> · ${esc(result.reason)}</div>` : ''}
      <div class="evidence-layout">
        <div>
          <div class="evidence-frame">
            ${m.image
              ? `<img src="${esc(m.image)}" alt="Original captured frame"><div class="region-layer">${defaultOverlayHtml()}</div>`
              : '<div class="notice">This memory has no original frame. Sample artwork is illustrative, not captured evidence.</div>'}
          </div>
          <div class="modal-actions source-actions">
            ${link
              ? `<a class="primary" href="${esc(link)}" target="_blank" rel="noopener noreferrer">${icon('external')}${m.has_original ? 'Open original PDF' : 'Reopen source'}</a>`
              : '<span class="subtle">No reopenable source URL recorded.</span>'}
            ${regions.length && m.image ? '<span class="subtle">Hover or click any region on the right to locate it on the frame</span>' : ''}
          </div>
          <div class="stage-list">${stages(m)}</div>
          ${renderTelemetry(m.telemetry)}
          ${m.near_duplicates?.length ? `<p class="subtle">${m.near_duplicates.length} visually similar capture(s) in this session; all originals preserved.</p>` : ''}
          ${(m.issues || []).map(issue => `<p class="notice warning">${esc(issue)}</p>`).join('')}
        </div>
        <div class="evidence-text">
          <div class="evidence-section">
            <div class="evidence-heading-row">
              <h3>Extracted evidence</h3>
              <span class="epistemic-badge">Verbatim · Local</span>
            </div>
            <p class="subtle">${m.regions?.length ? `${m.regions.length} regions · ${esc(m.regions[0].method)} · verify critical numbers against frame` : 'No text regions extracted.'}</p>
            ${ocrRegions.length
              ? `<div class="region-transcript">${ocrRegions
                  .map((r, idx) => `<button class="region-text ${matched.has(r.id) ? 'matched' : ''}" data-region="${esc(r.id)}"><span class="region-idx">#${idx + 1}</span><span>${esc(r.text)}</span></button>`)
                  .join('')}</div>`
              : ''}
          </div>
          ${m.text
            ? `<div class="evidence-section">
                <div class="evidence-heading-row">
                  <h3>${m.sample ? 'Sample text' : m.stages ? 'Your annotation' : 'Legacy context · provenance unverified'}</h3>
                </div>
                <div class="detail-text" style="margin-top:8px">${esc(m.text)}</div>
              </div>`
            : ''}
          ${visualRegions.length
            ? `<div class="evidence-section">
                <div class="evidence-heading-row">
                  <h3>Model-inferred visual regions</h3>
                  <span class="epistemic-badge ai">AI Estimated Boxes</span>
                </div>
                <p class="subtle">Spatial interpretations separate from OCR.</p>
                <div class="region-transcript">${visualRegions
                  .map((r, idx) => `<button class="region-text visual-region ${matched.has(r.id) ? 'matched' : ''}" data-region="${esc(r.id)}"><span class="region-idx">V${idx + 1}</span><span>${esc(r.text)}</span></button>`)
                  .join('')}</div>
              </div>`
            : ''}
          ${m.visual_description
            ? `<div class="evidence-section">
                <div class="evidence-heading-row">
                  <h3>Vision model description</h3>
                  <span class="epistemic-badge ai">AI Interpretation</span>
                </div>
                <p class="subtle">${esc(m.vision_provenance?.model || 'Model provenance unavailable')} · not a verbatim transcription.</p>
                <div class="detail-text">${esc(m.visual_description)}</div>
              </div>`
            : ''}
        </div>
      </div>
      <div class="modal-actions">
        <button class="secondary danger" id="delete-memory">Delete</button>
        <button class="secondary" id="copy-evidence">Copy evidence</button>
        ${m.stages?.vision === 'PENDING_PRIVACY_REVIEW' ? '<button class="primary" id="review-privacy">Review outbound frame</button>' : ''}
        ${m.image && !m.sample ? '<button class="secondary" id="ground-visual">Verify visual relationship</button>' : ''}
        ${!m.sample && c.isApi() ? '<button class="secondary" id="retry-processing">Reprocess locally</button>' : ''}
        <button class="primary" id="detail-save">${icon('bookmark')}${m.saved ? 'Unsave' : 'Save memory'}</button>
      </div>`,
      true
    );

    let pinnedId = null;
    const layer = document.querySelector('.region-layer');
    const regionButtons = [...document.querySelectorAll('[data-region]')];

    function syncOverlay(activeId) {
      if (!layer) return;
      if (!activeId) {
        layer.innerHTML = defaultOverlayHtml();
        regionButtons.forEach(x => x.classList.toggle('matched', matched.has(x.dataset.region)));
        return;
      }
      const region = regions.find(r => r.id === activeId);
      if (!region) return;
      const label = isVisualRegion(region) ? 'AI region' : 'OCR region';
      layer.innerHTML = renderRegionBox(region, label);
      regionButtons.forEach(x => x.classList.toggle('matched', x.dataset.region === activeId));
    }

    regionButtons.forEach(b => {
      b.onmouseenter = () => {
        if (!pinnedId) syncOverlay(b.dataset.region);
      };
      b.onmouseleave = () => {
        if (!pinnedId) syncOverlay(null);
      };
      b.onclick = () => {
        pinnedId = pinnedId === b.dataset.region ? null : b.dataset.region;
        syncOverlay(pinnedId);
      };
    });

    document.querySelector('#review-privacy')?.addEventListener('click', () => privacy.review(id));
    document.querySelector('#ground-visual')?.addEventListener('click', () => privacy.ground(id));
    document.querySelector('#copy-evidence').onclick = async () => {
      try {
        await navigator.clipboard.writeText(m.ocr_text || m.text || '');
        toast('Evidence copied');
      } catch {
        toast('Select the text to copy it manually.');
      }
    };
    document.querySelector('#detail-save').onclick = async () => {
      try {
        await c.save({ ...m, saved: !m.saved });
        await c.refresh();
        await detail(id);
      } catch (e) {
        toast(e.message);
      }
    };
    document.querySelector('#retry-processing')?.addEventListener('click', async () => {
      try {
        await request('/memories/' + encodeURIComponent(id) + '/reprocess', { method: 'POST' });
        closeModal();
        await c.refresh();
        toast('Queued for local reprocessing');
      } catch (e) {
        toast(e.message);
      }
    });
    document.querySelector('#delete-memory').onclick = () => {
      modal(
        `${modalTitle('Delete this memory?')}<p>This permanently removes its original document/frame, extracted text, visual descriptions, privacy review records, and embeddings from your local SQLite library. Exported JSON copies are unaffected.</p><div class="modal-actions"><button class="secondary" data-close>Keep memory</button><button class="primary" id="confirm-delete">Delete memory</button></div>`
      );
      document.querySelector('#confirm-delete').onclick = async () => {
        try {
          if (!c.isApi()) throw Error('Start the local backend to manage evidence.');
          await request('/memories/' + encodeURIComponent(id), { method: 'DELETE' });
          closeModal();
          await c.refresh();
          toast('Memory and its derived evidence deleted');
        } catch (e) {
          toast(e.message);
        }
      };
    };
  }

  function cancelCapture() {
    generation++;
    pendingStream?.getTracks().forEach(t => t.stop());
    pendingStream = null;
    draft = null;
  }

  function capture(type = 'screen') {
    cancelCapture();
    draft = { kind: type, image: null, pdf: null, filename: '', source: '', token: generation };
    if (!c.isApi()) {
      modal(`${modalTitle('Start your local backend')}<p>Evidence capture needs FastAPI and SQLite. Run <code>python server.py</code> (or <code>python start_gemini.py</code>), then reload this page.</p>`);
      return;
    }
    modal(
      `${modalTitle('Keep the moment.')}<p>One deliberate frame, its source, and enough session context to find your way back.</p>
      <div class="capture-tabs">
        ${[['screen', 'Window or tab'], ['upload', 'PDF or image'], ['note', 'Text note']]
          .map(([v, t]) => `<button type="button" data-capture-type="${v}" class="${type === v ? 'active' : ''}">${t}</button>`)
          .join('')}
      </div>
      <form id="capture-form">
        ${type === 'screen'
          ? `<div class="upload-box"><button type="button" class="secondary" id="choose-screen">${icon('monitor')} Choose a window or tab</button><p id="capture-state">Exactly one frame is captured; screen sharing stops immediately.</p></div>`
          : type === 'upload'
            ? `<div class="upload-box"><input type="file" id="capture-file" aria-label="Choose a local file" accept="application/pdf,image/png,image/jpeg,image/webp,.txt,.md"><p id="capture-state">PDF, PNG, JPEG, WebP, or text · maximum 8 MB</p></div><div id="pdf-options" hidden><label for="pdf-page">PDF page to capture</label><input id="pdf-page" type="number" min="1" max="10000" value="1"></div>`
            : ''}
        <label for="capture-session">Work session</label>
        <input id="capture-session" maxlength="120" list="known-sessions" placeholder="e.g. Product meeting" value="${esc(localStorage.getItem('contextos-session') || '')}">
        <datalist id="known-sessions">${c.sessions().map(s => `<option value="${esc(s)}">`).join('')}</datalist>
        <label for="capture-title">Title <span class="subtle">optional</span></label>
        <input id="capture-title" maxlength="160" placeholder="Taken from your file or shared surface when available">
        <label for="capture-url">Source URL <span class="subtle">optional</span></label>
        <input id="capture-url" type="url" maxlength="2000" placeholder="https://…">
        <label for="capture-text">${type === 'note' ? 'Text note' : 'Annotation · optional'}</label>
        <textarea id="capture-text" ${type === 'note' ? 'required' : ''} placeholder="A detail you want to remember…"></textarea>
        <div class="notice">${type === 'upload' ? 'PDFs retain an original local copy so you can reopen the exact page.' : 'The browser does not expose the original URL or verified app identity for a shared window. Add a URL if you want to reopen it.'} Captured text and model descriptions are stored separately.</div>
        <div class="modal-actions">
          <button type="button" class="secondary" data-close>Cancel</button>
          <button class="primary" id="save-capture">Capture & index locally</button>
        </div>
      </form>`
    );

    document.querySelectorAll('[data-capture-type]').forEach(b => (b.onclick = () => capture(b.dataset.captureType)));
    document.querySelector('#choose-screen')?.addEventListener('click', async () => {
      const current = draft;
      if (!navigator.mediaDevices?.getDisplayMedia) {
        toast('Screen sharing is unavailable here. Import an image instead.');
        return;
      }
      let stream;
      try {
        stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
        pendingStream = stream;
        if (current !== draft) {
          stream.getTracks().forEach(t => t.stop());
          return;
        }
        const video = document.createElement('video');
        video.srcObject = stream;
        await video.play();
        if (current !== draft) return;
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        if (canvas.width * canvas.height > 24_000_000) throw Error('This display exceeds 24 megapixels. Share a smaller window.');
        canvas.getContext('2d').drawImage(video, 0, 0);
        current.image = canvas.toDataURL('image/png');
        current.source = stream.getVideoTracks()[0].label || 'Shared surface';
        current.surface = stream.getVideoTracks()[0].getSettings().displaySurface;
        stream.getTracks().forEach(t => t.stop());
        document.querySelector('#capture-state').textContent = 'Frame captured. Screen sharing has stopped.';
        document.querySelector('#capture-title').value = current.source.slice(0, 160);
      } catch (e) {
        toast(e.name === 'NotAllowedError' ? 'Capture cancelled. Nothing saved.' : e.message);
      } finally {
        stream?.getTracks().forEach(t => t.stop());
        pendingStream = null;
      }
    });

    document.querySelector('#capture-file')?.addEventListener('change', async e => {
      const file = e.target.files[0];
      const current = draft;
      if (!file) return;
      current.image = null;
      current.pdf = null;
      current.filename = '';
      if (file.size > 8 * 1024 * 1024) {
        e.target.value = '';
        toast('Please choose a file smaller than 8 MB.');
        return;
      }
      const button = document.querySelector('#save-capture');
      button.disabled = true;
      try {
        current.filename = file.name;
        document.querySelector('#capture-title').value = file.name.slice(0, 160);
        const isPDF = file.name.toLowerCase().endsWith('.pdf');
        document.querySelector('#pdf-options').hidden = !isPDF;
        if (isPDF || /^image\/(png|jpeg|webp)$/.test(file.type)) {
          const encoded = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
          });
          if (current !== draft) return;
          if (isPDF) current.pdf = encoded;
          else current.image = encoded;
        } else if (/\.(txt|md)$/i.test(file.name)) {
          document.querySelector('#capture-text').value = await file.text();
        } else {
          throw Error('Choose a PDF, PNG, JPEG, WebP, text, or Markdown file.');
        }
        document.querySelector('#capture-state').textContent = file.name + ' is ready to capture.';
      } catch (e) {
        current.filename = '';
        toast(e.message || 'Unable to read file');
      } finally {
        if (current === draft) button.disabled = false;
      }
    });

    document.querySelector('#capture-form').onsubmit = async e => {
      e.preventDefault();
      const current = draft;
      const button = document.querySelector('#save-capture');
      const text = document.querySelector('#capture-text').value.trim();
      const session = document.querySelector('#capture-session').value.trim();
      const source_url = document.querySelector('#capture-url').value.trim();
      if (!current?.image && !current?.pdf && !text) {
        toast('Choose a source or add a text note.');
        return;
      }
      button.disabled = true;
      button.textContent = 'Saving original…';
      try {
        if (current.pdf) {
          await request('/import/pdf', {
            method: 'POST',
            body: JSON.stringify({
              data: current.pdf,
              filename: current.filename,
              page: Number(document.querySelector('#pdf-page').value),
              session,
              source_url,
              text
            })
          });
        } else {
          await c.save({
            id: crypto.randomUUID(),
            title: document.querySelector('#capture-title').value.trim() || current.filename || 'Capture ' + new Date().toLocaleString(),
            text,
            description: text.slice(0, 180),
            type: type === 'screen' ? (current.surface === 'browser' ? 'Browser' : 'Screen') : 'Documents',
            preview: 'doc',
            source: current.source || (type === 'upload' ? 'Local file' : 'Personal capture'),
            origin: current.filename || source_url || current.source || 'Personal note',
            source_path: current.filename,
            source_url,
            source_kind: type === 'screen' ? (current.surface === 'browser' ? 'browser' : 'window') : current.image ? 'image' : 'note',
            session,
            tags: ['Captured'],
            collection: 'Work projects',
            date: new Date().toISOString(),
            image: current.image,
            sample: false
          });
        }
        localStorage.setItem('contextos-session', session);
        closeModal();
        c.showCaptured();
        await c.refresh();
        toast('Original saved. Local extraction is queued.');
      } catch (e) {
        toast(e.message);
        button.disabled = false;
        button.textContent = 'Capture & index locally';
      }
    };
  }

  async function settings() {
    let status = {};
    let prefs = { exclusions: [] };
    try {
      [status, prefs] = await Promise.all([request('/status'), request('/preferences')]);
    } catch {
      toast('Local backend unavailable');
    }
    modal(
      `${modalTitle('Your private workspace')}
      <div class="status-row">Local OCR<span>${status.ocr ? 'Installed · offline' : 'Not installed'}</span></div>
      <div class="status-row">PDF extraction<span>${status.pdf ? 'Installed · offline' : 'Not installed'}</span></div>
      <div class="status-row">Vision model<span>${esc(status.mode === 'HYBRID_SANITIZED' ? status.remote_model : status.local_model || 'Local model')} · ${status.mode === 'HYBRID_SANITIZED' ? (status.remote_configured ? 'Remote configured · review gated' : 'Remote key not configured') : status.vision ? 'Available locally' : 'Not connected'}</span></div>
      <div class="status-row">Search<span>${status.embeddings ? 'Local embeddings + FTS5' : 'Local FTS5 + evidence ranking'}</span></div>
      <div class="notice">${status.mode === 'HYBRID_SANITIZED' ? 'Hybrid mode: only explicitly reviewed, flattened copies and approved queries leave this device. Remote configuration does not prove live connectivity.' : 'Local-only mode: zero cloud inference.'} No background capture. Storage is local SQLite and is not encrypted at rest. Inspect per-capture stage pills for actual processing outcomes.</div>
      <label for="exclusions">Excluded source names or URL fragments · one per line</label>
      <textarea id="exclusions" placeholder="private.example.com\nConfidential">${esc(prefs.exclusions.join('\n'))}</textarea>
      <p>Matched against supplied titles, filenames, and URLs before persistence. Browser captures cannot identify applications the OS/browser does not disclose. Exclusions do not delete existing memories.</p>
      <div class="modal-actions">
        <button class="secondary" id="export-data">Export library JSON</button>
        <button class="primary" id="save-preferences">Save exclusions</button>
      </div>`
    );
    document.querySelector('#save-preferences').onclick = async () => {
      try {
        await request('/preferences', {
          method: 'PUT',
          body: JSON.stringify({
            exclusions: document.querySelector('#exclusions').value.split('\n').map(x => x.trim()).filter(Boolean)
          })
        });
        toast('Source exclusions saved');
        closeModal();
      } catch (e) {
        toast(e.message);
      }
    };
    document.querySelector('#export-data').onclick = async () => {
      try {
        const data = await request('/memories');
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'contextos-evidence.json';
        a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000);
        toast('JSON exported. Original PDF binaries are not included.');
      } catch (e) {
        toast(e.message);
      }
    };
  }

  return { detail, capture, settings, cancelCapture };
}
