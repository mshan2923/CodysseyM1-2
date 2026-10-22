const API_BASE_URL = 'https://codysseym1-2-dvg7.onrender.com';
const state = { conversations: [], conversationId: null, rows: [], summary: null, currentFilter: 'all', isSending: false };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function renderMetrics() {
  const summary = state.summary || { counts: {}, metrics: {}, period: '데이터 없음' };
  const metrics = [
    ['플레이어 데이터', summary.counts.player_rows || 0, summary.period],
    ['패치 이벤트', summary.counts.patch_events || 0, `${summary.counts.patch_days || 0}개 패치일`],
    ['최대 변화율', summary.metrics.patch_change_max_pct == null ? '-' : `+${summary.metrics.patch_change_max_pct}%`, 'Firestore 계산값'],
    ['허브 팔로워', summary.metrics.latest_hub_followers == null ? '-' : Number(summary.metrics.latest_hub_followers).toLocaleString(), `${summary.counts.hub_days || 0}일 데이터`],
  ];
  $('#metric-grid').innerHTML = metrics.map(([label, value, foot]) => `<article class="metric-card"><div class="metric-label"><span>${label}</span><span>↗</span></div><div class="metric-value">${value}</div><div class="metric-foot">${foot}</div></article>`).join('');
}

function renderChart() {
  const width = 760; const height = 190; const pad = 12;
  const values = state.rows.filter((row) => row.type === 'players').map((row) => Number(row['Average Players'] ?? row.value)).filter(Number.isFinite).slice(-30);
  if (values.length < 2) { $('#player-chart').innerHTML = '<div class="empty-state"><h3>플레이어 데이터가 없습니다</h3><p>Firestore에 데이터를 추가하면 추세가 표시됩니다.</p></div>'; return; }
  const max = Math.max(...values); const min = Math.min(...values);
  const points = values.map((value, index) => {
    const x = pad + index * ((width - pad * 2) / (values.length - 1));
    const y = height - pad - ((value - min) / (max - min)) * (height - pad * 2);
    return [x, y];
  });
  const line = points.map(([x, y]) => `${x},${y}`).join(' ');
  const area = `${pad},${height - pad} ${line} ${width - pad},${height - pad}`;
  const dots = [Math.floor(values.length / 2), values.length - 1].map((index) => `<circle cx="${points[index][0]}" cy="${points[index][1]}" r="4" fill="#a896ff" stroke="#141923" stroke-width="3"/>`).join('');
  $('#player-chart').innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="플레이어 추세 차트"><defs><linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#b5f36c" stop-opacity=".23"/><stop offset="1" stop-color="#b5f36c" stop-opacity="0"/></linearGradient></defs><line x1="${pad}" y1="45" x2="${width - pad}" y2="45" stroke="#283040"/><line x1="${pad}" y1="95" x2="${width - pad}" y2="95" stroke="#283040"/><line x1="${pad}" y1="145" x2="${width - pad}" y2="145" stroke="#283040"/><polygon points="${area}" fill="url(#chartFill)"/><polyline points="${line}" fill="none" stroke="#b5f36c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>${dots}</svg>`;
}

function renderInsights() { $('#insight-list').innerHTML = '<div class="insight-item"><div class="insight-icon">↗</div><div><strong>Firestore 기반 요약</strong><p>대시보드 수치는 현재 Firestore에 저장된 데이터만 사용합니다.</p></div></div><div class="insight-item"><div class="insight-icon">◷</div><div><strong>AI 분석 준비</strong><p>데이터를 추가하면 AI가 최신 DB 컨텍스트로 분석합니다.</p></div></div>'; }
function renderPatches() { const rows = state.rows.filter((row) => row.type === 'patches').slice(-5).reverse(); $('#patch-table').innerHTML = rows.length ? rows.map((patch) => `<tr><td><strong>${escapeHtml(patch.version || patch.item || patch.memo || '-')}</strong></td><td>${escapeHtml(patch.date || '-')}</td><td class="change-positive">${patch.change_pct_7d == null ? escapeHtml(patch.value ?? '-') : `+${patch.change_pct_7d}%`}</td><td><span class="tag overlap">Firestore</span></td></tr>`).join('') : '<tr><td colspan="4">Firestore에 패치 데이터가 없습니다.</td></tr>'; }
function renderSources() { const counts = state.summary?.counts || {}; const sources = [['P', 'Players', counts.player_rows], ['$', 'Price', counts.price_snapshots], ['◆', 'Patch', counts.patch_days], ['H', 'Hub', counts.hub_days]]; $('#source-list').innerHTML = sources.map(([icon, name, count]) => `<div class="source-item"><div class="source-icon">${icon}</div><div><strong>${name}</strong><small>${count || 0} records · Firestore</small></div></div>`).join(''); }

function renderDataTable() {
  const rows = state.currentFilter === 'all' ? state.rows : state.rows.filter((row) => row.type === `${state.currentFilter}s` || (state.currentFilter === 'hub' && row.type === 'hub'));
  $('#record-count').textContent = `${rows.length}개 표시 중`;
  $('#data-table').innerHTML = rows.map((row) => `<tr><td>${escapeHtml(row.type)}</td><td>${escapeHtml(row.date || '-')}</td><td>${escapeHtml(row.item || row.version || row.name || '-')}</td><td>${escapeHtml(row.value ?? row['Average Players'] ?? row.Followers ?? row.change_pct_7d ?? '-')}</td><td>${escapeHtml(row.memo || row.description || '')}</td><td>${row.id ? `<button class="text-button delete-data" data-id="${escapeHtml(row.id)}">삭제</button>` : ''}</td></tr>`).join('');
  $$('.delete-data').forEach((button) => button.addEventListener('click', async () => { if (!window.confirm('이 Firestore 데이터를 삭제할까요?')) return; const response = await fetch(`${API_BASE_URL}/api/data/${button.dataset.id}`, { method: 'DELETE' }); if (response.ok) loadDashboardData(); }));
}

function showView(viewName) {
  $$('.view').forEach((view) => view.classList.toggle('active', view.id === `${viewName}-view`));
  $$('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === viewName));
  const titles = { overview: '세피리아 분석 대시보드', chat: 'AI 분석 대화', data: '데이터 탐색', history: '대화 기록' };
  $('#page-title').textContent = titles[viewName];
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function loadDashboardData() {
  try {
    const [summaryResponse, dataResponse] = await Promise.all([
      fetch(`${API_BASE_URL}/api/data/summary`),
      fetch(`${API_BASE_URL}/api/data?limit=5000`),
    ]);
    if (!summaryResponse.ok || !dataResponse.ok) throw new Error('Firestore 데이터를 불러오지 못했습니다.');
    state.summary = await summaryResponse.json();
    const body = await dataResponse.json();
    state.rows = (body.items || []).map((row) => ({ ...row, type: row.source || row.type || 'data' }));
    renderMetrics(); renderChart(); renderInsights(); renderPatches(); renderSources(); renderDataTable();
  } catch (error) {
    state.summary = { counts: {}, metrics: {}, period: '연결 실패' };
    $('#metric-grid').innerHTML = '<article class="metric-card"><div class="metric-label">Firestore</div><div class="metric-value">연결 실패</div><div class="metric-foot">백엔드와 Firebase 설정을 확인하세요</div></article>';
    $('#data-table').innerHTML = `<tr><td colspan="5">${escapeHtml(error.message)}</td></tr>`;
  }
}

async function sendMessage(question) {
  if (!question.trim()) return;
  if (state.isSending) return;
  state.isSending = true;
  const messages = $('#chat-messages');
  messages.insertAdjacentHTML('beforeend', `<div class="message user"><div class="avatar">ME</div><div><span class="message-label">YOU</span><p>${escapeHtml(question)}</p></div></div>`);
  $('#chat-input').value = '';

  const loadingId = `loading-${Date.now()}`;
  messages.insertAdjacentHTML('beforeend', `<div class="message assistant" id="${loadingId}"><div class="avatar">✦</div><div><span class="message-label">SEPHIRIA AI</span><p class="loading-message">분석 중<span>.</span><span>.</span><span>.</span></p></div></div>`);
  messages.lastElementChild.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  const conversation = state.conversations.flatMap((item) => [
    { role: 'user', content: item.question },
    { role: 'assistant', content: item.answer },
  ]).slice(-20);

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: question, conversation }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || `백엔드 응답 오류 (${response.status})`);

    const answer = body.answer || 'AI 응답이 비어 있습니다.';
    document.getElementById(loadingId).outerHTML = `<div class="message assistant"><div class="avatar">✦</div><div><span class="message-label">SEPHIRIA AI · ${escapeHtml(body.model || 'CUSTOM PROVIDER')}</span><p>${escapeHtml(answer)}</p></div></div>`;
    state.conversations.push({ question, answer, date: new Date().toLocaleString('ko-KR') });
    renderHistory();
    await saveConversation();
  } catch (error) {
    document.getElementById(loadingId).outerHTML = `<div class="message assistant error-message"><div class="avatar">!</div><div><span class="message-label">BACKEND ERROR</span><p>${escapeHtml(error.message)}<br><small>백엔드 주소, CORS, Render 환경변수를 확인하세요.</small></p></div></div>`;
  } finally {
    state.isSending = false;
  }
}

async function saveConversation() {
  const messages = state.conversations.flatMap((item) => [
    { role: 'user', content: item.question },
    { role: 'assistant', content: item.answer },
  ]);
  const url = state.conversationId ? `${API_BASE_URL}/api/conversations/${state.conversationId}` : `${API_BASE_URL}/api/conversations`;
  const response = await fetch(url, { method: state.conversationId ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(state.conversationId ? { messages } : { title: state.conversations[0]?.question || '분석 대화', messages }) });
  if (response.ok && !state.conversationId) state.conversationId = (await response.json()).id;
}

async function loadConversations() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/conversations?limit=20`);
    if (!response.ok) return;
    const body = await response.json();
    const latest = body.items?.[0];
    if (latest?.messages) {
      state.conversations = latest.messages.reduce((items, message, index, messages) => {
        if (message.role === 'user' && messages[index + 1]?.role === 'assistant') items.push({ question: message.content, answer: messages[index + 1].content, date: '' });
        return items;
      }, []);
      state.conversationId = latest.id;
      renderHistory();
    }
  } catch (_) { /* 대화 기록이 없어도 대시보드는 동작한다. */ }
}

function renderHistory() {
  if (!state.conversations.length) return;
  $('#history-list').innerHTML = state.conversations.slice().reverse().map((item) => `<div class="history-row"><div class="history-icon">✦</div><div><strong>${escapeHtml(item.question)}</strong><p>${item.date}</p></div><button class="text-button" data-go-view="chat">열기 →</button></div>`).join('');
  $$('#history-list [data-go-view]').forEach((button) => button.addEventListener('click', () => showView(button.dataset.goView)));
}

function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char])); }

async function init() {
  renderMetrics(); renderChart(); renderInsights(); renderPatches(); renderSources(); renderDataTable();
  $$('.nav-item').forEach((button) => button.addEventListener('click', () => showView(button.dataset.view)));
  $$('[data-go-view]').forEach((button) => button.addEventListener('click', () => showView(button.dataset.goView)));
  $$('.segmented-control button').forEach((button) => button.addEventListener('click', () => { $$('.segmented-control button').forEach((item) => item.classList.remove('active')); button.classList.add('active'); state.currentFilter = button.dataset.filter; renderDataTable(); }));
  $$('.suggestion-list button').forEach((button) => button.addEventListener('click', () => { showView('chat'); sendMessage(button.dataset.question); }));
  $('#chat-form').addEventListener('submit', (event) => { event.preventDefault(); sendMessage($('#chat-input').value); });
  $('#data-form').addEventListener('submit', async (event) => { event.preventDefault(); const valueText = $('#data-value').value.trim(); const numericValue = Number(valueText); const payload = { type: $('#data-type').value.trim(), date: $('#data-date').value, value: Number.isNaN(numericValue) ? valueText : numericValue, memo: $('#data-memo').value.trim() }; const response = await fetch(`${API_BASE_URL}/api/data`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }); if (!response.ok) { window.alert('Firestore 데이터 추가에 실패했습니다.'); return; } event.currentTarget.reset(); await loadDashboardData(); });
  $('#refresh-button').addEventListener('click', (event) => { event.currentTarget.animate([{ transform: 'rotate(0)' }, { transform: 'rotate(360deg)' }], { duration: 500 }); loadDashboardData(); });
  await loadDashboardData();
  await loadConversations();
}

init();
