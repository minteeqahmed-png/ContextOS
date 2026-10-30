export function createPrivacyUI(c) {
  const { request, modal, modalTitle, esc, toast, closeModal } = c;

  const recipientLabel = t =>
    t.mode === 'LOCAL_ONLY'
      ? `${t.local_model} · ${t.local}`
      : `${t.model}${t.upstream ? ' (' + t.upstream + ')' : ''} · ${t.base_url}`;

  const payloadView = p => `
    <details class="payload-details">
      <summary>Inspect exact outbound JSON payload (${esc(recipientLabel(p.target))})</summary>
      <pre class="outbound-payload">${esc(JSON.stringify(p.payload, null, 2))}</pre>
    </details>`;

  async function review(id) {
    let masks = [];
    let syncedCount = 0;
    let proposal;
    let start = null;
    let image;

    async function prepare() {
      proposal = await request(`/memories/${encodeURIComponent(id)}/privacy/prepare`, {
        method: 'POST',
        body: JSON.stringify({ masks })
      });
      syncedCount = masks.length;
      drawUI();
    }

    function drawUI() {
      const host = (() => {
        try {
          return new URL(proposal.target.mode === 'LOCAL_ONLY' ? proposal.target.local : proposal.target.base_url).host;
        } catch {
          return proposal.target.base_url;
        }
      })();
      const modelName = proposal.target.mode === 'LOCAL_ONLY' ? proposal.target.local_model : proposal.target.model;

      modal(
        `${modalTitle('Review before sending')}
        <div class="privacy-boundary-strip">
          <div class="boundary-step"><small>1 · Original artifact</small><strong>Kept local in SQLite</strong></div>
          <div class="boundary-step"><small>2 · Outbound copy</small><strong>Flattened PNG · ${proposal.masks.length} mask(s)</strong></div>
          <div class="boundary-step"><small>3 · Explicit recipient</small><strong title="${esc(modelName + ' @ ' + host)}">${esc(modelName)} · ${esc(host)}</strong></div>
        </div>
        <p style="margin-top:0">Drag anywhere on the image below to add opaque black redaction masks. Automatic OCR/regex masking can miss sensitive details—inspect the entire frame and payload before approving.</p>
        ${proposal.warnings.map(w => `<p class="notice warning">${esc(w)}</p>`).join('')}
        <div class="canvas-stage">
          <canvas id="privacy-canvas" aria-label="Drag to mask sensitive regions" tabindex="0"></canvas>
        </div>
        <div class="mask-toolbar">
          <p id="mask-state">Preview is current · ${proposal.masks.length} total mask(s) (${masks.length} manual).</p>
          <div class="mask-quick-actions">
            <button type="button" class="secondary" id="undo-mask" ${masks.length ? '' : 'disabled'}>Undo manual mask</button>
            <button type="button" class="secondary" id="clear-masks" ${masks.length ? '' : 'disabled'}>Clear manual</button>
          </div>
        </div>
        <div class="mask-controls">
          <label>Left <input id="mask-x0" type="number" min="0" max="1" step=".01" value="0"></label>
          <label>Top <input id="mask-y0" type="number" min="0" max="1" step=".01" value="0"></label>
          <label>Right <input id="mask-x1" type="number" min="0" max="1" step=".01" value="1"></label>
          <label>Bottom <input id="mask-y1" type="number" min="0" max="1" step=".01" value="1"></label>
          <button type="button" class="secondary" id="numeric-mask">Add coordinate mask</button>
        </div>
        <p class="subtle" style="margin:6px 0 0">Normalized coordinates (0–1) provide a keyboard alternative to pointer dragging.</p>
        ${payloadView(proposal)}
        <div class="modal-actions">
          <button class="secondary" id="keep-local">Keep Local Only</button>
          <button class="secondary" id="update-preview">Update preview & payload</button>
          <button class="primary" id="approve-enrich">Approve & Enrich</button>
        </div>`,
        true
      );

      const canvas = document.querySelector('#privacy-canvas');
      const ctx = canvas.getContext('2d');
      const approveBtn = document.querySelector('#approve-enrich');
      const undoBtn = document.querySelector('#undo-mask');
      const clearBtn = document.querySelector('#clear-masks');
      const stateEl = document.querySelector('#mask-state');

      function renderCanvas(draftBox = null) {
        if (!image || !image.complete) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(image, 0, 0);
        // Draw any newly added unsynced manual masks immediately over the server preview
        for (const box of masks.slice(syncedCount)) {
          ctx.fillStyle = '#000000';
          ctx.fillRect(
            box[0] * canvas.width,
            box[1] * canvas.height,
            (box[2] - box[0]) * canvas.width,
            (box[3] - box[1]) * canvas.height
          );
          ctx.strokeStyle = '#e5a93c';
          ctx.lineWidth = Math.max(1.5, canvas.width / 450);
          ctx.strokeRect(
            box[0] * canvas.width,
            box[1] * canvas.height,
            (box[2] - box[0]) * canvas.width,
            (box[3] - box[1]) * canvas.height
          );
        }
        // Live rubber-band selection preview while dragging
        if (draftBox) {
          const x = draftBox[0] * canvas.width;
          const y = draftBox[1] * canvas.height;
          const w = (draftBox[2] - draftBox[0]) * canvas.width;
          const h = (draftBox[3] - draftBox[1]) * canvas.height;
          ctx.fillStyle = 'rgba(0, 0, 0, 0.58)';
          ctx.fillRect(x, y, w, h);
          ctx.save();
          ctx.setLineDash([6, 4]);
          ctx.strokeStyle = '#f2b84b';
          ctx.lineWidth = Math.max(2, canvas.width / 400);
          ctx.strokeRect(x, y, w, h);
          ctx.restore();
        }
      }

      function markDirty(message) {
        approveBtn.disabled = true;
        undoBtn.disabled = masks.length === 0;
        clearBtn.disabled = masks.length === 0;
        stateEl.textContent = message;
      }

      image = new Image();
      image.onload = () => {
        canvas.width = image.naturalWidth;
        canvas.height = image.naturalHeight;
        renderCanvas();
      };
      image.src = proposal.image;

      const point = e => {
        const r = canvas.getBoundingClientRect();
        return [
          Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)),
          Math.max(0, Math.min(1, (e.clientY - r.top) / r.height))
        ];
      };

      function add(box) {
        if (!box.every(Number.isFinite) || box.some(v => v < 0 || v > 1) || box[2] <= box[0] || box[3] <= box[1]) {
          toast('Drag or enter a nonempty rectangle within 0–1.');
          renderCanvas();
          return;
        }
        masks.push(box);
        renderCanvas();
        markDirty('Mask changed. Click “Update preview & payload” to regenerate the outbound digest before approving.');
      }

      canvas.onpointerdown = e => {
        start = point(e);
        canvas.setPointerCapture(e.pointerId);
      };
      canvas.onpointermove = e => {
        if (!start) return;
        const cur = point(e);
        const draftBox = [
          Math.min(start[0], cur[0]),
          Math.min(start[1], cur[1]),
          Math.max(start[0], cur[0]),
          Math.max(start[1], cur[1])
        ];
        renderCanvas(draftBox);
      };
      canvas.onpointerup = e => {
        if (!start) return;
        const end = point(e);
        const box = [
          Math.min(start[0], end[0]),
          Math.min(start[1], end[1]),
          Math.max(start[0], end[0]),
          Math.max(start[1], end[1])
        ];
        start = null;
        if (box[2] - box[0] < 0.005 || box[3] - box[1] < 0.005) {
          renderCanvas();
          return;
        }
        add(box);
      };
      canvas.onpointercancel = () => {
        start = null;
        renderCanvas();
      };

      undoBtn.onclick = async () => {
        if (!masks.length) return;
        masks.pop();
        if (masks.length < syncedCount) {
          undoBtn.disabled = true;
          try { await prepare(); } catch (err) { toast(err.message); }
        } else {
          renderCanvas();
          if (masks.length === syncedCount) {
            approveBtn.disabled = false;
            undoBtn.disabled = masks.length === 0;
            clearBtn.disabled = masks.length === 0;
            stateEl.textContent = `Preview is current · ${proposal.masks.length} total mask(s) (${masks.length} manual).`;
          } else {
            markDirty('Mask undone. Click “Update preview & payload” before approving.');
          }
        }
      };

      clearBtn.onclick = async () => {
        if (!masks.length) return;
        masks = [];
        clearBtn.disabled = true;
        try { await prepare(); } catch (err) { toast(err.message); }
      };

      document.querySelector('#numeric-mask').onclick = () =>
        add(['x0', 'y0', 'x1', 'y1'].map(k => Number(document.querySelector('#mask-' + k).value)));

      document.querySelector('#update-preview').onclick = async e => {
        e.target.disabled = true;
        try {
          await prepare();
        } catch (err) {
          toast(err.message);
          e.target.disabled = false;
        }
      };

      document.querySelector('#keep-local').onclick = async () => {
        try {
          await request(`/memories/${encodeURIComponent(id)}/privacy/local-only`, { method: 'POST' });
          closeModal();
          await c.refresh();
          toast('Frame kept local. Remote enrichment skipped.');
        } catch (err) {
          toast(err.message);
        }
      };

      approveBtn.onclick = async e => {
        e.target.disabled = true;
        try {
          await request(`/memories/${encodeURIComponent(id)}/privacy/approve`, {
            method: 'POST',
            body: JSON.stringify({ digest: proposal.digest })
          });
          closeModal();
          await c.refresh();
          toast('Approved copy queued for vision enrichment.');
        } catch (err) {
          toast(err.message);
          e.target.disabled = false;
        }
      };
    }

    try {
      await prepare();
    } catch (e) {
      toast(e.message);
    }
  }

  function ground(id) {
    modal(
      `${modalTitle('Verify a visual relationship')}
      <p>Ask about the spatial or visual relationship between two elements in this frame. In hybrid mode, verification reuses only the previously approved sanitized image and requires at least two supporting bounding boxes.</p>
      <form id="ground-form">
        <label for="ground-query">Visual question</label>
        <textarea id="ground-query" required maxlength="2000" placeholder="Where is the red circular indicator relative to the high point of the green line? Cite both regions."></textarea>
        <div class="modal-actions">
          <button type="button" class="secondary" data-close>Cancel</button>
          <button class="primary">Review verification request</button>
        </div>
      </form>`
    );

    document.querySelector('#ground-form').onsubmit = async e => {
      e.preventDefault();
      const button = e.target.querySelector('button.primary');
      button.disabled = true;
      try {
        const p = await request(`/memories/${encodeURIComponent(id)}/grounding/prepare`, {
          method: 'POST',
          body: JSON.stringify({ query: document.querySelector('#ground-query').value })
        });
        modal(
          `${modalTitle('Review visual verification')}
          <div class="notice"><strong>Sanitized question:</strong> ${esc(p.query)}<br><span class="subtle">Check for any sensitive context the local regex detector missed before sending.</span></div>
          <div class="canvas-stage"><img class="privacy-preview" src="${esc(p.image)}" alt="Exact image to send for verification"></div>
          ${payloadView(p)}
          <div class="modal-actions">
            <button class="secondary" data-close>Cancel</button>
            <button class="primary" id="verify-send">Approve & Verify</button>
          </div>`,
          true
        );

        document.querySelector('#verify-send').onclick = async ev => {
          ev.target.disabled = true;
          ev.target.textContent = 'Inspecting pixels…';
          try {
            const r = await request(`/grounding/${p.id}/approve`, {
              method: 'POST',
              body: JSON.stringify({ digest: p.digest })
            });
            modal(
              `${modalTitle(r.supported ? 'Visual interpretation with supporting regions' : 'Insufficient visual evidence')}
              <div class="match-explanation" style="${r.supported ? '' : 'background:var(--amber-bg);border-color:var(--amber-line);color:var(--amber-ink)'}">
                <strong>${r.supported ? 'Supported by 2+ regions' : 'Unverified / Unsupported'}</strong> · ${esc(r.answer)}
              </div>
              <div class="evidence-layout">
                <div class="evidence-frame">
                  <img src="${esc(r.image)}" alt="Frame used for visual verification">
                  <div class="region-layer">
                    ${r.citations
                      .map(
                        (x, i) =>
                          `<div class="region-highlight" data-cite-box="${i}" title="${esc(x.description)}" style="left:${x.box[0] * 100}%;top:${x.box[1] * 100}%;width:${(x.box[2] - x.box[0]) * 100}%;height:${(x.box[3] - x.box[1]) * 100}%"><span class="region-pin-badge">#${i + 1}</span></div>`
                      )
                      .join('')}
                  </div>
                </div>
                <div class="evidence-text">
                  <div class="evidence-heading-row">
                    <h3>Supporting pixel citations</h3>
                    <span class="epistemic-badge ai">${r.citations.length} cited region(s)</span>
                  </div>
                  <ol class="citation-list">
                    ${r.citations.map(x => `<li>${esc(x.description)}</li>`).join('')}
                  </ol>
                  <p class="notice">${esc(r.interpretation)}</p>
                  <div class="telemetry-strip"><span class="telemetry-pill">Verification · ${(r.latency_ms / 1000).toFixed(2)} s (${r.latency_ms} ms)</span></div>
                </div>
              </div>
              <div class="modal-actions">
                <button class="primary" data-close>Done</button>
              </div>`,
              true
            );
          } catch (err) {
            toast(err.message);
            ev.target.disabled = false;
            ev.target.textContent = 'Request failed; close and review again';
          }
        };
      } catch (err) {
        toast(err.message);
        button.disabled = false;
      }
    };
  }

  return { review, ground };
}
