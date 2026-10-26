export function createPrivacyUI(c) {
  const {request,modal,modalTitle,esc,toast,closeModal}=c;
  const payloadView=p=>`<p>Recipient: ${esc(p.target.mode==='LOCAL_ONLY'?p.target.local:p.target.base_url)} · ${esc(p.target.mode==='LOCAL_ONLY'?p.target.local_model:p.target.model)}${p.target.upstream?' · '+esc(p.target.upstream):''}</p><details><summary>Exact outbound JSON (includes image bytes; excludes authentication)</summary><pre class="outbound-payload">${esc(JSON.stringify(p.payload,null,2))}</pre></details>`;
  async function review(id) {
    let masks=[], proposal, start=null, image;
    async function prepare() {
      proposal=await request(`/memories/${encodeURIComponent(id)}/privacy/prepare`,{method:'POST',body:JSON.stringify({masks})});
      drawUI();
    }
    function drawUI() {
      modal(`${modalTitle('Review before sending')}<p>The original stays local. Drag on this copy to add opaque masks. Automatic detection can miss sensitive details; inspect the entire image and payload.</p>${proposal.warnings.map(w=>`<p class="notice">${esc(w)}</p>`).join('')}<canvas id="privacy-canvas" aria-label="Drag to mask sensitive regions" tabindex="0"></canvas><p id="mask-state">Preview is current. ${proposal.masks.length} mask(s).</p><div class="mask-controls"><label>Left <input id="mask-x0" type="number" min="0" max="1" step=".01" value="0"></label><label>Top <input id="mask-y0" type="number" min="0" max="1" step=".01" value="0"></label><label>Right <input id="mask-x1" type="number" min="0" max="1" step=".01" value="1"></label><label>Bottom <input id="mask-y1" type="number" min="0" max="1" step=".01" value="1"></label><button class="secondary" id="numeric-mask">Add mask</button></div><p class="subtle">Coordinates above are fractions of the image (0–1); use them as a keyboard alternative to dragging.</p>${payloadView(proposal)}<div class="modal-actions"><button class="secondary" id="keep-local">Keep Local Only</button><button class="secondary" id="update-preview">Update preview & payload</button><button class="primary" id="approve-enrich">Approve & Enrich</button></div>`,true);
      const canvas=document.querySelector('#privacy-canvas'),ctx=canvas.getContext('2d');
      image=new Image();image.onload=()=>{canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;ctx.drawImage(image,0,0)};image.src=proposal.image;
      const point=e=>{const r=canvas.getBoundingClientRect();return [Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))]};
      function add(box){if(!box.every(Number.isFinite)||box.some(v=>v<0||v>1)||box[2]<=box[0]||box[3]<=box[1]){toast('Use a nonempty rectangle within 0–1.');return}masks.push(box);ctx.fillStyle='black';ctx.fillRect(box[0]*canvas.width,box[1]*canvas.height,(box[2]-box[0])*canvas.width,(box[3]-box[1])*canvas.height);document.querySelector('#approve-enrich').disabled=true;document.querySelector('#mask-state').textContent='Mask added. Update the preview and exact payload before approving.'}
      canvas.onpointerdown=e=>{start=point(e);canvas.setPointerCapture(e.pointerId)};
      canvas.onpointerup=e=>{if(!start)return;const end=point(e);add([Math.min(start[0],end[0]),Math.min(start[1],end[1]),Math.max(start[0],end[0]),Math.max(start[1],end[1])]);start=null};
      canvas.onpointercancel=()=>{start=null};
      document.querySelector('#numeric-mask').onclick=()=>add(['x0','y0','x1','y1'].map(k=>Number(document.querySelector('#mask-'+k).value)));
      document.querySelector('#update-preview').onclick=async e=>{e.target.disabled=true;try{await prepare()}catch(err){toast(err.message);e.target.disabled=false}};
      document.querySelector('#keep-local').onclick=async()=>{try{await request(`/memories/${encodeURIComponent(id)}/privacy/local-only`,{method:'POST'});closeModal();await c.refresh();toast('Frame kept local. Remote enrichment skipped.')}catch(err){toast(err.message)}};
      document.querySelector('#approve-enrich').onclick=async e=>{e.target.disabled=true;try{await request(`/memories/${encodeURIComponent(id)}/privacy/approve`,{method:'POST',body:JSON.stringify({digest:proposal.digest})});closeModal();await c.refresh();toast('Approved copy queued for vision enrichment.')}catch(err){toast(err.message);e.target.disabled=false}};
    }
    try{await prepare()}catch(e){toast(e.message)}
  }
  function ground(id) {
    modal(`${modalTitle('Verify a visual relationship')}<p>Ask about two visible elements in this frame. Remote verification uses only its approved sanitized copy.</p><form id="ground-form"><label for="ground-query">Question</label><textarea id="ground-query" required maxlength="2000" placeholder="Which highlighted row corresponds to the red status indicator?"></textarea><div class="modal-actions"><button class="primary">Review verification request</button></div></form>`);
    document.querySelector('#ground-form').onsubmit=async e=>{
      e.preventDefault();const button=e.target.querySelector('button');button.disabled=true;
      try {
        const p=await request(`/memories/${encodeURIComponent(id)}/grounding/prepare`,{method:'POST',body:JSON.stringify({query:document.querySelector('#ground-query').value})});
        modal(`${modalTitle('Review visual verification')}<p>Sanitized question: ${esc(p.query)}</p><p>Check for sensitive text the detector missed. Cancel and edit your question if needed.</p><img class="privacy-preview" src="${esc(p.image)}" alt="Exact image to send for verification">${payloadView(p)}<div class="modal-actions"><button class="secondary" data-close>Cancel</button><button class="primary" id="verify-send">Approve & Verify</button></div>`,true);
        document.querySelector('#verify-send').onclick=async e=>{e.target.disabled=true;e.target.textContent='Inspecting pixels…';try{
          const r=await request(`/grounding/${p.id}/approve`,{method:'POST',body:JSON.stringify({digest:p.digest})});
          modal(`${modalTitle(r.supported?'Visual interpretation with supporting regions':'Insufficient visual evidence')}<p>${esc(r.answer)}</p><div class="evidence-frame"><img src="${esc(r.image)}" alt="Frame used for visual verification"><div class="region-layer">${r.citations.map((x,i)=>`<div class="region-highlight" title="${esc(x.description)}" style="left:${x.box[0]*100}%;top:${x.box[1]*100}%;width:${(x.box[2]-x.box[0])*100}%;height:${(x.box[3]-x.box[1])*100}%">${i+1}</div>`).join('')}</div></div><ol>${r.citations.map(x=>`<li>${esc(x.description)}</li>`).join('')}</ol><p class="notice">${esc(r.interpretation)}</p><p>${r.latency_ms} ms · model inference and validation</p>`,true);
        }catch(err){toast(err.message);e.target.disabled=false;e.target.textContent='Request failed; close and review again'}};
      }catch(err){toast(err.message);button.disabled=false}
    };
  }
  return {review,ground};
}
