import { createEvidenceUI } from './evidence.js';

const paths = {
  search: 'm21 21-4.5-4.5 M19 10.5a8.5 8.5 0 1 1-17 0 8.5 8.5 0 0 1 17 0',
  grid: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  clock: 'M12 8v5l3 2 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
  folder: 'M3 7V5h6l2 3h10v12H3z',
  layers: 'm12 3 10 6-10 6L2 9z M2 13l10 6 10-6 M2 17l10 6 10-6',
  plus: 'M12 5v14 M5 12h14',
  chevron: 'm9 5 7 7-7 7',
  down: 'm6 9 6 6 6-6',
  shield: 'm12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6z m-4 9 3 3 5-6',
  lock: 'M5 10h14v11H5z M8 10V6a4 4 0 0 1 8 0v4',
  monitor: 'M3 4h18v13H3z M8 21h8 M12 17v4',
  file: 'M5 2h9l5 5v15H5z M14 2v6h5 M8 12h8 M8 16h6',
  mic: 'M9 4a3 3 0 0 1 6 0v8a3 3 0 0 1-6 0z M5 10v2a7 7 0 0 0 14 0v-2 M12 19v4 M8 23h8',
  code: 'm8 6-6 6 6 6 m8-12 6 6-6 6 m-3-15-2 18',
  bookmark: 'M6 3h12v19l-6-4-6 4z',
  settings: 'M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1z M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0',
  arrow: 'M5 12h14 m-6-6 6 6-6 6',
  list: 'M8 5h13 M8 12h13 M8 19h13 M3 5h.01 M3 12h.01 M3 19h.01',
  calendar: 'M3 5h18v16H3z M3 10h18 M7 2v6 M17 2v6',
  close: 'm6 6 12 12 M6 18 18 6',
  external: 'M14 3h7v7 M21 3 10 14 M10 3H3v18h18v-7',
  check: 'm5 12 4 4L19 6',
  upload: 'M12 16V3 m-5 5 5-5 5 5 M3 15v6h18v-6',
  spark: 'm12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3z',
  menu: 'M3 6h18 M3 12h18 M3 18h18',
  play: 'm8 4 13 8-13 8z',
  trash: 'M4 6h16 M9 6V3h6v3 M6 6l1 15h10l1-15 M10 10v7 M14 10v7'
};

const icon = (name, cls = '') =>
  `<svg class="icon ${cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.file}"/></svg>`;

const esc = s =>
  String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const now = new Date();
const ago = (days, hours = 10) => {
  const d = new Date(now);
  d.setDate(d.getDate() - days);
  d.setHours(hours, 24, 0, 0);
  return d.toISOString();
};

const seeds = [
  { id: 'sample-1', title: 'The pricing table I was looking for', type: 'Documents', preview: 'pdf', source: 'Preview', origin: 'Acme — pricing.pdf', date: ago(0, 10), description: 'A side-by-side look at the Starter, Pro, and Enterprise plans. All the details, in one place.', tags: ['Pricing', 'Research'], collection: 'Work projects', text: 'Acme pricing overview\nStarter: $19/month. 3 projects, basic analytics, community support.\nPro: $49/month. Unlimited projects, advanced analytics, priority support.\nEnterprise: Custom pricing. SSO, dedicated support, custom integrations.\nReviewed during Tuesday’s product meeting.', sample: true },
  { id: 'sample-2', title: 'A calmer onboarding experience', type: 'Browser', preview: 'design', source: 'Chrome', origin: 'Figma · Onboarding explorations', date: ago(0, 9), description: 'A little inspiration for making the first few moments feel more human.', tags: ['Design', 'Inspiration'], collection: 'Design inspiration', text: 'Onboarding explorations — A little room to grow. Welcome to your everyday space. A three-step onboarding flow with a gentle green palette, organic illustrations, and a clear Get started button.', sample: true },
  { id: 'sample-3', title: 'That useful React hook', type: 'Code', preview: 'code', source: 'VS Code', origin: 'useDebounce.ts', date: ago(0, 8), description: 'A clean debounce hook to keep search fast and unnecessary requests out of the way.', tags: ['React', 'Development'], collection: 'Work projects', text: 'import { useState, useEffect } from "react";\n\nexport function useDebounce<T>(value: T, delay = 300) {\n  const [debounced, setDebounced] = useState(value);\n  useEffect(() => {\n    const timer = setTimeout(() => setDebounced(value), delay);\n    return () => clearTimeout(timer);\n  }, [value, delay]);\n  return debounced;\n}', sample: true },
  { id: 'sample-4', title: 'Good ideas from the team sync', type: 'Audio', preview: 'audio', source: 'Voice memo', origin: 'Product team sync · transcript', date: ago(1, 15), description: 'The moment we talked about making capture feel effortless. Worth coming back to.', tags: ['Meeting', 'Product'], collection: 'Work projects', text: '[02:14] Maya: What if saving context was as simple as taking a screenshot?\n[02:31] Alex: The key is preserving where you were, not just what you saw.\n[03:06] Maya: Let’s prioritize on-demand capture, then make every snapshot searchable.\n[04:10] Alex: Agreed. We should keep everything local, with no cloud dependency.', sample: true },
  { id: 'sample-5', title: 'The bigger picture, in one chart', type: 'Browser', preview: 'chart', source: 'Chrome', origin: 'Analytics · Monthly overview', date: ago(1, 13), description: 'Weekly active users are trending in the right direction. A snapshot of the progress.', tags: ['Analytics', 'Growth'], collection: 'Work projects', text: 'Weekly active users — 24,892, up 18.6% this month.\nWeek 1: 14,200. Week 2: 16,800. Week 3: 15,900. Week 4: 19,600. Week 5: 21,100. Week 6: 24,892.\nThe growth chart shows increasing engagement following the onboarding update.', sample: true },
  { id: 'sample-6', title: 'Notes for a more focused day', type: 'Documents', preview: 'doc', source: 'Notion', origin: 'Personal workspace · Reading notes', date: ago(2, 11), description: 'A few thoughts on deep work, attention, and making space for what matters.', tags: ['Reading', 'Personal'], collection: 'Reading list', text: 'Make space for what matters\n1. Start the day with one clear intention.\n2. Give your attention to one thing at a time.\n3. Capture the thought, then come back to the task.\n4. Leave a little room to think.\nAttention is a finite resource. Spend it on purpose.', sample: true }
];

let memories = [];
let api = false;
let settings = {};
let state = {
  page: 'Recall',
  filter: 'All memories',
  query: '',
  date: 'all',
  sort: 'newest',
  view: 'grid',
  collection: null,
  library: 'captures',
  session: ''
};
let toastTimer;
let searchResult = null;
let searchSequence = 0;
let searchTimer;
let previousFocus;

const app = document.querySelector('#app');
const overlay = document.querySelector('#overlay');

function toast(message) {
  const t = document.querySelector('#toast');
  t.textContent = message;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 3300);
}

async function request(path, opts = {}) {
  const r = await fetch('/api' + path, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!r.ok) {
    const e = await r.json().catch(() => ({ detail: 'Request failed' }));
    throw Error(e.detail || 'Request failed');
  }
  return r.json();
}

async function init() {
  try {
    settings = await request('/status');
    api = true;
    memories = await request('/memories');
  } catch {
    try {
      memories = JSON.parse(localStorage.getItem('contextos-memories') || 'null') || seeds;
    } catch {
      memories = seeds;
    }
  }
  render();
}

async function persist(memory) {
  if (api) {
    const saved = await request('/memories', { method: 'POST', body: JSON.stringify(memory) });
    memories = [saved, ...memories.filter(x => x.id !== saved.id)];
  } else {
    const updated = [memory, ...memories.filter(x => x.id !== memory.id)];
    localStorage.setItem('contextos-memories', JSON.stringify(updated));
    memories = updated;
  }
}

function nav(page, collection = null) {
  searchSequence++;
  clearTimeout(searchTimer);
  state.page = page;
  state.collection = collection;
  state.query = '';
  searchResult = null;
  state.filter = 'All memories';
  state.session = '';
  render();
}

function modeBadge() {
  if (settings.mode === 'HYBRID_SANITIZED') {
    const model = settings.remote_model ? settings.remote_model.split('/').pop() : 'review required';
    return `<span class="private-label hybrid" title="Originals stay local; outbound frames require explicit review">${icon('shield')}Hybrid · ${esc(model)}</span>`;
  }
  return `<span class="private-label">${icon('lock')}${settings.vision ? 'Vision connected locally' : 'Local-only recall'}</span>`;
}

function render() {
  const personalCount = memories.filter(m => !m.sample).length;
  app.innerHTML = `<aside class="sidebar">
    <a class="brand" href="#" aria-label="ContextOS home"><span class="brandmark"><i></i><i></i><i></i><i></i></span>ContextOS</a>
    <div class="workspace"><span class="avatar">P</span>Personal workspace${icon('down')}</div>
    <div class="nav-label">YOUR SECOND MEMORY</div>
    <nav class="nav">
      ${[['Recall', 'grid'], ['Timeline', 'clock'], ['Collections', 'folder'], ['Sources', 'layers']]
        .map(([n, i]) => `<button data-nav="${n}" class="${state.page === n && !state.collection ? 'active' : ''}">${icon(i)}${n}${n === 'Recall' ? `<span class="badge">${memories.length}</span>` : ''}</button>`)
        .join('')}
    </nav>
    <div class="nav-divider"></div>
    <div class="nav-label">COLLECTIONS</div>
    <nav class="nav">
      ${['Work projects', 'Design inspiration', 'Reading list']
        .map((n, i) => `<button data-collection="${n}" class="${state.collection === n ? 'active' : ''}"><span class="collection-dot ${['', 'blue', 'purple'][i]}"></span>${n}</button>`)
        .join('')}
      <button data-nav="Saved" class="${state.page === 'Saved' ? 'active' : ''}">${icon('bookmark')}Saved memories</button>
    </nav>
    <div class="sidebar-bottom">
      <div class="local-card">
        <strong>${icon('shield')}Your memory stays yours</strong>
        <p>Stored on this device.<br>Only captured when you choose.</p>
        <div class="storage-track"><i style="width:${Math.min(100, Math.max(12, personalCount * 8))}%"></i></div>
        <div class="storage-label"><span>${personalCount} personal ${personalCount === 1 ? 'memory' : 'memories'}</span><span>SQLite local</span></div>
      </div>
      <div class="profile">
        <span class="avatar">Y</span>
        <div><strong>Your workspace</strong><small>Just for you</small></div>
        <button data-settings aria-label="Open settings">${icon('settings')}</button>
      </div>
    </div>
  </aside>
  <main class="main">
    <header class="topbar">
      <div class="breadcrumbs">
        <button class="mobile-menu" aria-label="Toggle navigation">${icon('menu')}</button>
        <span>Your workspace</span>${icon('chevron')}<strong>${esc(state.collection || state.page)}</strong>
      </div>
      <div class="top-actions">
        ${modeBadge()}
        <button class="primary" data-capture>${icon('plus')}Capture a memory<kbd>Alt N</kbd></button>
      </div>
    </header>
    <div class="content">${pageContent()}</div>
  </main>`;
  bind();
}

function art() {
  return `<div class="memory-art" aria-hidden="true"><svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="1.25"><path d="M60 19C37 0 9 29 24 52C1 65 19 99 43 93C48 121 84 116 88 91C116 89 124 57 101 46C111 21 79 6 60 19Z"/><path d="M60 25C40 8 16 32 30 52C10 66 25 94 45 87C51 111 80 106 82 85C107 83 114 59 94 49C102 28 77 15 60 25Z M60 31C43 16 24 35 36 52C19 66 30 87 48 81C54 101 76 98 77 79C97 78 105 60 88 51C94 33 76 23 60 31Z M60 37C46 25 32 38 42 53C28 65 36 80 51 75C57 93 72 89 72 73C88 73 96 61 82 53C86 40 74 31 60 37Z M60 43C49 35 41 42 48 54C37 63 43 73 54 69C59 81 67 81 66 67C79 68 85 61 76 55C79 46 70 39 60 43Z M60 49C53 44 49 49 54 55C47 60 50 65 57 63C62 70 63 70 61 61C68 64 75 61 69 56C72 52 66 47 60 49Z"/></svg><span class="art-star">✧</span><span class="art-star small">✦</span></div>`;
}

function pageContent() {
  if (state.page === 'Sources') return sourcesPage();
  if (state.page === 'Collections' && !state.collection) return collectionsPage();
  const home = state.page === 'Recall' && !state.collection;
  const personalCount = memories.filter(m => !m.sample).length;
  const sampleCount = memories.filter(m => m.sample).length;
  return `<section class="hero ${home ? '' : 'compact'}">
    <div>
      <div class="eyebrow"><span class="dot"></span>YOUR MIND HAS BETTER THINGS TO DO</div>
      <h1>${home ? 'A little less searching.<br><span>A lot more remembering.</span>' : esc(state.collection || (state.page === 'Saved' ? 'Keep the good things close.' : 'Your days, remembered.'))}</h1>
      <p>${home ? 'Find the chart trend, split-screen layout, or exact PDF row you remember seeing—grounded in your saved pixels.' : state.page === 'Timeline' ? 'A chronological trail of every frame and document you chose to keep.' : 'A thoughtful place for the evidence you want to return to.'}</p>
    </div>
    ${art()}
  </section>
  <section class="search-shell" aria-label="Search your memories">
    <form id="search-form" class="search-main">
      ${icon('search')}
      <input id="search" aria-label="Search memories" placeholder="What would you like to remember? Try a trend, layout, date, or session…" value="${esc(state.query)}" autocomplete="off">
      ${state.query ? '<button type="button" class="search-clear" id="search-clear" aria-label="Clear search">Clear</button>' : ''}
      <span class="search-key">Ctrl K</span>
      <button class="search-submit" aria-label="Search">${icon('arrow')}</button>
    </form>
    <div class="search-bottom">
      <span>Try asking</span>
      ${['Green line dipped then spiked', 'Three connected nodes on the right', 'Dark terminal beside browser preview']
        .map(q => `<button type="button" data-query="${q}">${q}${icon('arrow').replace('class="icon', 'style="width:10px;height:10px;margin-left:5px" class="icon')}</button>`)
        .join('')}
      <span class="local-search">${icon('spark')}${settings.mode === 'HYBRID_SANITIZED' ? 'OCR + reviewed vision recall' : 'Evidence-first local recall'}</span>
    </div>
  </section>
  <section class="library">
    <div class="section-heading">
      <div class="section-title">
        <h2>${state.query ? 'Search results' : state.collection || (state.page === 'Saved' ? 'Saved memories' : 'Recent memories')}</h2>
        <span class="count" id="result-count">${filtered().length}</span>
      </div>
      <span class="subtle"><i class="green-dot"></i>All memories on this device<span class="sample-label">${state.library === 'samples' ? 'Illustrative examples' : 'Your captures'}</span></span>
    </div>
    <div class="library-scope">
      <div>
        <button data-library="captures" class="${state.library === 'captures' ? 'active' : ''}">Your captures · ${personalCount}</button>
        <button data-library="samples" class="${state.library === 'samples' ? 'active' : ''}">Examples · ${sampleCount}</button>
      </div>
      <label>Session
        <select id="session-filter">
          <option value="">All sessions</option>
          ${[...new Set(memories.map(m => m.session).filter(Boolean))]
            .map(v => `<option value="${esc(v)}" ${state.session === v ? 'selected' : ''}>${esc(v)}</option>`)
            .join('')}
        </select>
      </label>
    </div>
    <div class="toolbar">
      <div class="filters">
        ${[['All memories', 'grid'], ['Browser', 'monitor'], ['Documents', 'file'], ['Screen', 'monitor'], ['Code', 'code']]
          .map(([f, i]) => `<button class="filter ${state.filter === f ? 'active' : ''}" data-filter="${f}">${icon(i)}${f}</button>`)
          .join('')}
      </div>
      <div class="view-tools">
        <label class="select-wrap" aria-label="Filter by date">${icon('calendar')}
          <select id="date-filter">
            <option value="all" ${state.date === 'all' ? 'selected' : ''}>Any time</option>
            <option value="today" ${state.date === 'today' ? 'selected' : ''}>Today</option>
            <option value="week" ${state.date === 'week' ? 'selected' : ''}>Past 7 days</option>
          </select>
        </label>
        <label class="select-wrap" aria-label="Sort memories">
          <select id="sort">
            <option value="newest" ${state.sort === 'newest' ? 'selected' : ''}>Newest first</option>
            <option value="oldest" ${state.sort === 'oldest' ? 'selected' : ''}>Oldest first</option>
          </select>
        </label>
        <div class="view-switch">
          <button data-view="grid" class="${state.view === 'grid' ? 'active' : ''}" aria-label="Grid view">${icon('grid')}</button>
          <button data-view="list" class="${state.view === 'list' ? 'active' : ''}" aria-label="List view">${icon('list')}</button>
        </div>
      </div>
    </div>
    <div id="results">${results()}</div>
  </section>
  <footer class="footer">
    <span>${icon('lock')}A private little corner of your digital life.</span>
    <button data-settings>${api ? 'Local backend connected' : 'Browser storage mode'}<i class="green-dot"></i>${icon('chevron')}</button>
  </footer>`;
}

function filtered() {
  const stop = new Set(['the', 'i', 'a', 'an', 'was', 'saw', 'what', 'that', 'from', 'had', 'in', 'my', 'for', 'of', 'to', 'it', 'during', 'open', 'looking', 'me', 'show']);
  const tokens = state.query.toLowerCase().match(/[\p{L}\p{N}]+/gu)?.filter(w => !stop.has(w)) || [];
  return memories
    .filter(m => (state.library === 'samples' ? m.sample : !m.sample) && (!state.session || m.session === state.session))
    .map(m => {
      const text = `${m.title} ${m.description} ${m.text} ${(m.tags || []).join(' ')} ${m.origin}`.toLowerCase();
      return { ...m, score: tokens.reduce((n, t) => n + (text.includes(t) ? 1 : 0), 0) };
    })
    .filter(m =>
      (state.filter === 'All memories' || m.type === state.filter) &&
      (!state.collection || m.collection === state.collection) &&
      (state.page !== 'Saved' || m.saved) &&
      (!tokens.length || (searchResult?.query === state.query ? searchResult.ids.includes(m.id) : m.score > 0)) &&
      (state.date === 'all' || (state.date === 'today' ? new Date(m.date).toDateString() === new Date().toDateString() : Date.now() - new Date(m.date).getTime() < 7 * 86400000))
    )
    .sort((a, b) =>
      (tokens.length ? (searchResult?.query === state.query ? searchResult.ids.indexOf(a.id) - searchResult.ids.indexOf(b.id) : b.score - a.score) : 0) ||
      (state.sort === 'oldest' ? new Date(a.date) - new Date(b.date) : new Date(b.date) - new Date(a.date))
    );
}

function results() {
  const ms = filtered();
  let last = '';
  return `${state.query ? `<p class="result-message">${ms.length} ${ms.length === 1 ? 'memory' : 'memories'} matching “${esc(state.query)}” · ${searchResult?.query === state.query && searchResult.mode === 'hybrid' ? 'Hybrid local search' : 'Local text search'}${searchResult?.constraints?.length ? ' · ' + esc(searchResult.constraints.join(' · ')) : ''}</p>` : ''}
  <div class="grid ${state.view === 'list' ? 'list' : ''}">
    ${ms.length
      ? ms.map((m, i) => {
          let label = '';
          if (state.page === 'Timeline') {
            const d = new Date(m.date).toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' });
            if (d !== last) {
              last = d;
              label = `<div class="timeline-label">${d}</div>`;
            }
          }
          return label + card(m, i);
        }).join('')
      : `<div class="empty">
          ${icon('search')}
          <h3>${state.page === 'Saved' ? 'Your favorites will feel at home here.' : 'No memories here just yet.'}</h3>
          <p>${state.query ? 'Try a different phrase or clear active filters.' : 'Capture a window, import an image, or drop in a PDF page to start. Switch to Examples to browse sample cards.'}</p>
          <button class="secondary" data-reset>${state.query ? 'Reset search & filters' : 'Show all memories'}</button>
        </div>`}
  </div>`;
}

function timeLabel(date) {
  const d = new Date(date);
  const diff = Math.floor((new Date().setHours(0, 0, 0, 0) - new Date(d).setHours(0, 0, 0, 0)) / 86400000);
  return diff === 0
    ? d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
    : diff === 1
      ? 'Yesterday'
      : d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function cardStageBadge(m) {
  if (m.stages?.vision === 'PENDING_PRIVACY_REVIEW') {
    return '<span class="stage PENDING_PRIVACY_REVIEW">review outbound</span>';
  }
  if (m.stages?.vision === 'ready') {
    return '<span class="stage vision-ready">vision indexed</span>';
  }
  if (m.stages?.vision === 'running' || m.stages?.vision === 'queued') {
    return `<span class="stage ${esc(m.stages.vision)}">vision ${esc(m.stages.vision)}</span>`;
  }
  return m.status ? `<span class="stage ${esc(m.status)}">${esc(m.status)}</span>` : '';
}

function card(m, i) {
  const match = searchResult?.query === state.query && searchResult?.results?.find(r => r.id === m.id);
  return `<article class="memory-card" style="animation-delay:${Math.min(i, 10) * 35}ms">
    <button class="card-open" data-open="${esc(m.id)}" aria-label="Open ${esc(m.title)}">
      ${preview(m)}
      <div class="card-body">
        <div class="source-line">
          <span class="source-icon">${m.source === 'Chrome' ? '◉' : m.source === 'Notion' ? '▣' : m.type === 'Audio' ? '≋' : m.type === 'Code' ? '⌘' : '▧'}</span>
          ${esc(m.source)}<span>·</span><span>${esc(m.type === 'Documents' ? 'Document' : m.type === 'Audio' ? 'Transcript' : m.type === 'Code' ? 'Code snippet' : m.type === 'Screen' ? 'Screen frame' : 'Web page')}</span>
          <time datetime="${m.date}">${timeLabel(m.date)}</time>
        </div>
        <h3>${esc(m.title)}</h3>
        <p class="card-description">${esc(m.description)}</p>
        ${m.session ? `<div class="session-label">${esc(m.session)}</div>` : ''}
        ${match ? `<div class="card-match">${esc(match.reason)}</div>` : ''}
      </div>
    </button>
    <div class="card-footer">
      ${cardStageBadge(m)}
      ${(m.tags || []).slice(0, 1).map(t => `<span class="tag">${esc(t)}</span>`).join('')}
      <button class="save ${m.saved ? 'saved' : ''}" data-save="${esc(m.id)}" aria-label="${m.saved ? 'Unsave' : 'Save'} ${esc(m.title)}" aria-pressed="${!!m.saved}">${icon('bookmark')}</button>
    </div>
  </article>`;
}

function preview(m) {
  if (m.image) {
    const label = m.page ? `PDF · page ${m.page}` : m.type === 'Browser' ? 'Browser frame' : 'Captured frame';
    return `<div class="preview has-image">
      <img class="image-preview" src="${esc(m.image)}" alt="Captured frame for ${esc(m.title)}">
      <span class="preview-badge">${icon(m.page ? 'file' : 'monitor')}${esc(label)}</span>
      <span class="preview-inspect">Inspect evidence →</span>
    </div>`;
  }
  const badge = `<span class="preview-badge">${icon(m.type === 'Audio' ? 'mic' : m.type === 'Code' ? 'code' : 'monitor')}${m.sample ? 'Sample snapshot' : 'Captured memory'}</span>`;
  let inner = '';
  switch (m.preview) {
    case 'pdf':
      inner = `<div class="mini-browser"><div class="mini-top"><i></i><i></i><i></i><span>acme / pricing overview</span></div><div class="mini-title">Good work. The right plan.</div><div class="mini-subtitle">Simple, transparent pricing that grows with you.</div><div class="pricing">${['Starter', 'Pro', 'Enterprise'].map((p, i) => `<div class="price-col ${i === 1 ? 'selected' : ''}">${p}<strong>${['$19', '$49', 'Custom'][i]}${i < 2 ? '<small> / mo</small>' : ''}</strong><b>${i === 2 ? 'Let’s talk' : 'Get started'}</b><div class="line"></div><div class="line short"></div><div class="line"></div></div>`).join('')}</div></div>`;
      break;
    case 'design':
      inner = `<div class="figma-top"><span class="figma-logo">◒</span>Onboarding explorations <span style="margin-left:auto">100%</span></div><div class="design-board"><div class="design-phone"><div class="tiny-label">EVERYDAY SPACE</div><strong>A little room<br>to grow.</strong><div class="plant">♧</div><div class="pill"></div></div><div class="design-phone"><div class="tiny-label">MAKE IT YOURS</div><strong>Good things<br>start here.</strong><div class="line"></div><div class="line short"></div><div class="plant" style="height:34px;background:#e9dfcd">✳</div></div></div>`;
      break;
    case 'code':
      inner = `<div class="code-top"><span>TS</span> useDebounce.ts <span style="float:right">•••</span></div><pre><em>import</em> { useState, useEffect } <em>from</em> <b>'react'</b>;

<em>export function</em> <b>useDebounce</b>(value, delay) {
  <em>const</em> [debounced, setDebounced] =
    useState(value);

  useEffect(() =&gt; {
    <em>const</em> timer = setTimeout(() =&gt; {
      setDebounced(value);
    }, delay);</pre>`;
      break;
    case 'audio':
      inner = `<div class="audio-header"><span class="audio-symbol">${icon('mic')}</span><div>Product team sync<small>A few good ideas, captured.</small></div></div><div class="waveform">${Array.from({ length: 48 }, (_, i) => `<i style="height:${8 + Math.abs(Math.sin(i * 2.9) * Math.cos(i * 0.6)) * 35}px"></i>`).join('')}</div><div class="audio-times"><span>02:14</span><span>12:48</span></div>`;
      break;
    case 'chart':
      inner = `<div class="chart-paper"><div class="tiny-label">PRODUCT OVERVIEW</div><div class="mini-title" style="margin-top:7px">Weekly active users <span style="float:right;color:#5f8248;font-size:7px">↗ 18.6%</span></div><div style="font-size:16px;margin-top:5px;color:#344a2a;font-weight:600">24,892 <span style="font-size:6px;color:#8c9580;font-weight:400">this month</span></div><svg viewBox="0 0 250 90" preserveAspectRatio="none"><defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#a8c090" stop-opacity=".5"/><stop offset="1" stop-color="#a8c090" stop-opacity="0"/></linearGradient></defs><path d="M0 20h250 M0 45h250 M0 70h250" stroke="#edf0e6" stroke-width=".6"/><path d="M0 75 14 71 28 74 43 54 59 62 74 51 91 58 106 40 121 43 135 28 149 35 165 21 179 29 195 19 211 28 226 11 240 15 250 5V90H0Z" fill="url(#area)"/><path d="M0 75 14 71 28 74 43 54 59 62 74 51 91 58 106 40 121 43 135 28 149 35 165 21 179 29 195 19 211 28 226 11 240 15 250 5" fill="none" stroke="#6f9053" stroke-width="1.9"/></svg></div>`;
      break;
    default:
      inner = `<div class="document"><div class="tiny-label">${m.sample ? '☀ PERSONAL NOTES' : 'CAPTURED CONTEXT'}</div><div class="mini-title">${m.sample ? 'Make space for what matters' : esc(m.title)}</div>${(m.sample ? ['Start the day with one clear intention.', 'Give your attention to one thing at a time.', 'Capture the thought. Come back to the task.'] : (m.text || '').split('\n').slice(0, 3)).map(t => `<div class="doc-row"><span>✓</span>${esc(t.slice(0, 90))}</div>`).join('')}<div class="doc-callout">${m.sample ? 'Attention is a finite resource. Spend it on purpose.' : esc(m.description)}</div><div class="line"></div><div class="line short"></div></div>`;
  }
  return `<div class="preview ${m.preview || 'doc'}">${inner}${badge}</div>`;
}

function bind() {
  document.querySelector('.brand').onclick = e => { e.preventDefault(); nav('Recall'); };
  document.querySelectorAll('[data-nav]').forEach(b => (b.onclick = () => nav(b.dataset.nav)));
  document.querySelectorAll('[data-collection]').forEach(b => (b.onclick = () => nav('Collections', b.dataset.collection)));
  document.querySelectorAll('[data-capture]').forEach(b => (b.onclick = () => capture()));
  document.querySelectorAll('[data-settings]').forEach(b => (b.onclick = () => showSettings()));
  document.querySelector('.mobile-menu').onclick = () => document.querySelector('.sidebar').classList.toggle('open');
  document.querySelectorAll('[data-query]').forEach(b => {
    b.onclick = () => {
      state.query = b.dataset.query;
      searchResult = null;
      render();
      runSearch();
    };
  });
  document.querySelectorAll('[data-filter]').forEach(b => {
    b.onclick = () => {
      state.filter = b.dataset.filter;
      render();
    };
  });
  document.querySelectorAll('[data-view]').forEach(b => {
    b.onclick = () => {
      state.view = b.dataset.view;
      render();
    };
  });
  const form = document.querySelector('#search-form');
  if (form) {
    form.onsubmit = e => {
      e.preventDefault();
      clearTimeout(searchTimer);
      state.query = document.querySelector('#search').value.trim();
      runSearch();
    };
    document.querySelector('#search').oninput = e => {
      state.query = e.target.value;
      searchResult = null;
      searchSequence++;
      clearTimeout(searchTimer);
      searchTimer = setTimeout(runSearch, 320);
      document.querySelector('#results').innerHTML = results();
      document.querySelector('#result-count').textContent = filtered().length;
      bindCards();
    };
    document.querySelector('#search-clear')?.addEventListener('click', () => {
      state.query = '';
      searchResult = null;
      searchSequence++;
      clearTimeout(searchTimer);
      render();
      document.querySelector('#search')?.focus();
    });
    document.querySelector('#date-filter').onchange = e => { state.date = e.target.value; render(); };
    document.querySelector('#sort').onchange = e => { state.sort = e.target.value; render(); };
  }
  document.querySelectorAll('[data-library]').forEach(b => {
    b.onclick = () => {
      searchSequence++;
      state.library = b.dataset.library;
      searchResult = null;
      render();
      if (state.query) runSearch();
    };
  });
  document.querySelector('#session-filter')?.addEventListener('change', e => {
    searchSequence++;
    state.session = e.target.value;
    searchResult = null;
    render();
    if (state.query) runSearch();
  });
  bindCards();
}

function bindCards() {
  document.querySelectorAll('[data-open]').forEach(b => (b.onclick = () => detail(b.dataset.open)));
  document.querySelectorAll('[data-save]').forEach(b => {
    b.onclick = async () => {
      const m = memories.find(x => x.id === b.dataset.save);
      try {
        await persist({ ...m, saved: !m.saved });
        render();
        toast(m.saved ? 'Removed from saved memories' : 'Saved for another day');
      } catch (e) {
        toast(e.message);
      }
    };
  });
  document.querySelector('[data-reset]')?.addEventListener('click', () => {
    state = { ...state, page: 'Recall', collection: null, query: '', filter: 'All memories', date: 'all', session: '' };
    searchResult = null;
    render();
  });
}

function sourcesPage() {
  return `<section class="hero compact">
    <div>
      <div class="eyebrow"><span class="dot"></span>A PLACE FOR EVERY KIND OF CONTEXT</div>
      <h1>Your sources, <span>connected.</span></h1>
      <p>Capture what matters deliberately—one frame or PDF page at a time.</p>
    </div>
    ${art()}
  </section>
  <div class="source-grid">
    ${[
      ['monitor', 'Screen & browser', 'Capture a single PNG frame from any window, tab, or display you explicitly pick.', 'screen'],
      ['file', 'Images & PDF pages', 'Import a screenshot, rendered PDF page with word coordinates, or Markdown note.', 'upload'],
      ['mic', 'Audio transcripts', 'Paste or import a transcript from your local transcription workflow.', 'note'],
      ['spark', 'Vision & privacy gate', 'Inspect local OCR, Ollama status, or reviewed hybrid vision settings.', 'settings']
    ].map(([i, t, d, a]) => `<div class="source-tile">${icon(i)}<h3>${t}</h3><p>${d}</p><button class="secondary" onclick="window.sourceAction('${a}')">${a === 'settings' ? 'View connection' : 'Capture a memory'} →</button></div>`).join('')}
  </div>
  <div class="notice" style="margin-top:22px">ContextOS only captures when you ask—never continuously in the background. PDF import retains the original document so you can reopen the exact page. Window capture cannot automatically discover browser URLs; supply a URL if you want one-click reopening.</div>`;
}

window.sourceAction = t => (t === 'settings' ? showSettings() : capture(t));

function collectionsPage() {
  return `<section class="hero compact">
    <div>
      <div class="eyebrow"><span class="dot"></span>A LITTLE ORDER, A LOT OF POSSIBILITIES</div>
      <h1>Make room for <span>your ideas.</span></h1>
      <p>Related moments, thoughtfully kept together.</p>
    </div>
    ${art()}
  </section>
  <div class="grid">
    ${['Work projects', 'Design inspiration', 'Reading list']
      .map(n => `<button class="collection-card" data-collection="${n}"><div class="folder-art">${icon('folder').replace('class="icon "', 'class="icon" style="width:42px;height:42px" ')}</div><h3>${n}</h3><p>${memories.filter(m => m.collection === n).length} memories</p></button>`)
      .join('')}
  </div>`;
}

function modal(html, wide = false) {
  previousFocus = document.activeElement;
  overlay.innerHTML = `<div class="modal-backdrop"><section class="modal ${wide ? 'wide' : ''}" role="dialog" aria-modal="true" aria-labelledby="modal-title">${html}</section></div>`;
  overlay.querySelector('.modal-backdrop').onclick = e => {
    if (e.target.classList.contains('modal-backdrop')) closeModal();
  };
  overlay.querySelectorAll('[data-close]').forEach(b => (b.onclick = closeModal));
  setTimeout(() => overlay.querySelector('input,button,textarea')?.focus(), 0);
}

function closeModal() {
  evidence.cancelCapture();
  overlay.innerHTML = '';
  previousFocus?.focus();
}

const modalTitle = t => `<div class="modal-heading"><h2 id="modal-title">${esc(t)}</h2><button class="close" data-close aria-label="Close dialog">${icon('close')}</button></div>`;

function detail(id) { return evidence.detail(id); }
function capture(type = 'screen') { return evidence.capture(type); }
function showSettings() { return evidence.settings(); }

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    if (!document.querySelector('#search')) nav('Recall');
    document.querySelector('#search')?.focus();
  }
  if (e.altKey && e.key.toLowerCase() === 'n') {
    e.preventDefault();
    capture();
  }
  if (e.key === 'Tab' && overlay.firstChild) {
    const focusable = [...overlay.querySelectorAll('button,input,select,textarea,a[href],canvas[tabindex]')].filter(x => !x.disabled);
    const first = focusable[0];
    const last = focusable.at(-1);
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last?.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first?.focus();
    }
  }
});

const evidence = createEvidenceUI({
  esc,
  icon,
  request,
  modal,
  modalTitle,
  toast,
  closeModal,
  isApi: () => api,
  getMemory: id => memories.find(m => m.id === id),
  getEvidence: id => searchResult?.results?.find(r => r.id === id),
  save: persist,
  refresh: refreshMemories,
  sessions: () => [...new Set(memories.map(m => m.session).filter(Boolean))],
  showCaptured: () => {
    state.library = 'captures';
    state.query = '';
    searchResult = null;
  }
});

async function refreshMemories() {
  [settings, memories] = await Promise.all([request('/status').catch(() => settings), request('/memories')]);
  render();
}

async function runSearch() {
  const seq = ++searchSequence;
  const query = state.query;
  if (!api) return;
  try {
    const result = await request('/search?' + new URLSearchParams({
      q: query,
      tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
      library: state.library,
      session: state.session
    }));
    if (seq !== searchSequence) return;
    searchResult = { ...result, query };
    const el = document.querySelector('#results');
    if (el) {
      el.innerHTML = results();
      document.querySelector('#result-count').textContent = filtered().length;
      bindCards();
    }
  } catch (e) {
    if (seq === searchSequence) toast('Evidence search unavailable: ' + e.message);
  }
}

setInterval(async () => {
  if (!api || overlay.firstChild || !memories.some(m => ['captured', 'extracting', 'indexing'].includes(m.status) || ['queued', 'running'].includes(m.stages?.vision))) return;
  try {
    memories = await request('/memories');
    const el = document.querySelector('#results');
    if (el) {
      el.innerHTML = results();
      document.querySelector('#result-count').textContent = filtered().length;
      bindCards();
    }
  } catch {}
}, 1500);

init();
