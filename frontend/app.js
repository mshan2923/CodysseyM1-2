const demo = {
  metrics: [
    { label: '분석 데이터', value: '551일', foot: '2025.04 — 2026.10' },
    { label: '패치 이벤트', value: '24개', foot: '73개 패치일을 그룹화' },
    { label: '최대 변화율', value: '+1,388%', foot: '1.0 정식 출시', positive: true },
    { label: '허브 팔로워', value: '24,567', foot: '2026.10.21 기준', positive: true },
  ],
  patches: [
    { title: '1.0', date: '2026-07-31', change: 1388, status: 'overlap', major: true },
    { title: '0.11.0', date: '2026-03-25', change: 199, status: 'overlap', major: true },
    { title: '0.10.0 (Chapter 4)', date: '2025-12-24', change: 161, status: 'overlap', major: true },
    { title: '0.8.3 (Chapter 3)', date: '2025-08-11', change: 144, status: 'overlap', major: true },
    { title: '0.8.12', date: '2025-09-12', change: 35, status: 'overlap', major: true },
  ],
  insights: [
    { title: '메이저 패치 5개 모두 증가', text: '패치 이후 7일 평균 플레이어 수가 이전 7일보다 높았습니다.' },
    { title: '4개 이벤트는 2주 뒤에도 유지', text: '0.8.12는 2주 안에 이전 수준으로 돌아갔습니다.' },
    { title: '인과관계는 아직 확인 불가', text: '1.0은 정식 출시와 패치가 겹쳐 효과를 분리할 수 없습니다.' },
  ],
  sources: [
    { icon: 'P', name: 'Players', detail: '2,108 rows · 일별 평균 플레이어 수' },
    { icon: '$', name: 'Price', detail: '21 snapshots · 가격 변경 시점' },
    { icon: '◆', name: 'Patch', detail: '73 patch days · 전후 변화 분석' },
    { icon: 'H', name: 'Hub', detail: '1,059 days · 팔로워 추이' },
  ],
  dataRows: [
    { type: '패치', filter: 'patch', date: '2026-07-31', item: '1.0 정식 출시', value: '+1,388%', memo: '플레이어 7일 변화율' },
    { type: '패치', filter: 'patch', date: '2026-03-25', item: '0.11.0', value: '+199%', memo: '메이저 패치' },
    { type: '패치', filter: 'patch', date: '2025-12-24', item: '0.10.0 Chapter 4', value: '+161%', memo: '메이저 패치' },
    { type: '가격', filter: 'price', date: '2026-07-31', item: 'Final price', value: '₩9,900', memo: '역대 최저가 갱신' },
    { type: '가격', filter: 'price', date: '2026-09-14', item: 'Final price', value: '₩19,000', memo: '정가 변경' },
    { type: '허브', filter: 'hub', date: '2026-10-21', item: 'Followers', value: '24,567명', memo: '최근 누적 팔로워' },
    { type: '허브', filter: 'hub', date: '2026-08-01', item: 'Followers', value: '18,644명', memo: '1.0 직후' },
  ],
  chart: [32, 34, 30, 37, 40, 38, 45, 42, 48, 57, 61, 66, 74, 70, 78, 91, 87, 98, 100, 92, 84, 77, 72, 69],
};

const API_BASE_URL = 'http://127.0.0.1:8001';
const state = { conversations: [], currentFilter: 'all', isSending: false };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function renderMetrics() {
  $('#metric-grid').innerHTML = demo.metrics.map((metric) => `<article class="metric-card"><div class="metric-label"><span>${metric.label}</span><span>↗</span></div><div class="metric-value">${metric.value}</div><div class="metric-foot ${metric.positive ? 'positive' : ''}">${metric.foot}</div></article>`).join('');
}

function renderChart() {
  const width = 760; const height = 190; const pad = 12;
  const max = Math.max(...demo.chart); const min = Math.min(...demo.chart);
  const points = demo.chart.map((value, index) => {
    const x = pad + index * ((width - pad * 2) / (demo.chart.length - 1));
    const y = height - pad - ((value - min) / (max - min)) * (height - pad * 2);
    return [x, y];
  });
  const line = points.map(([x, y]) => `${x},${y}`).join(' ');
  const area = `${pad},${height - pad} ${line} ${width - pad},${height - pad}`;
  const dots = [6, 15, 18].map((index) => `<circle cx="${points[index][0]}" cy="${points[index][1]}" r="4" fill="#a896ff" stroke="#141923" stroke-width="3"/>`).join('');
  $('#player-chart').innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="플레이어 추세 차트"><defs><linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#b5f36c" stop-opacity=".23"/><stop offset="1" stop-color="#b5f36c" stop-opacity="0"/></linearGradient></defs><line x1="${pad}" y1="45" x2="${width - pad}" y2="45" stroke="#283040"/><line x1="${pad}" y1="95" x2="${width - pad}" y2="95" stroke="#283040"/><line x1="${pad}" y1="145" x2="${width - pad}" y2="145" stroke="#283040"/><polygon points="${area}" fill="url(#chartFill)"/><polyline points="${line}" fill="none" stroke="#b5f36c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>${dots}</svg>`;
}

function renderInsights() { $('#insight-list').innerHTML = demo.insights.map((item, index) => `<div class="insight-item"><div class="insight-icon">${['↗', '◷', '!'][index]}</div><div><strong>${item.title}</strong><p>${item.text}</p></div></div>`).join(''); }
function renderPatches() { $('#patch-table').innerHTML = demo.patches.map((patch) => `<tr><td><strong>${patch.title}</strong></td><td>${patch.date}</td><td class="change-positive">+${patch.change.toLocaleString()}%</td><td><span class="tag ${patch.status}">${patch.status}</span></td></tr>`).join(''); }
function renderSources() { $('#source-list').innerHTML = demo.sources.map((source) => `<div class="source-item"><div class="source-icon">${source.icon}</div><div><strong>${source.name}</strong><small>${source.detail}</small></div></div>`).join(''); }

function renderDataTable() {
  const rows = state.currentFilter === 'all' ? demo.dataRows : demo.dataRows.filter((row) => row.filter === state.currentFilter);
  $('#record-count').textContent = `${rows.length}개 표시 중`;
  $('#data-table').innerHTML = rows.map((row) => `<tr><td>${row.type}</td><td>${row.date}</td><td>${row.item}</td><td class="${row.value.includes('+') ? 'change-positive' : ''}">${row.value}</td><td>${row.memo}</td></tr>`).join('');
}

function showView(viewName) {
  $$('.view').forEach((view) => view.classList.toggle('active', view.id === `${viewName}-view`));
  $$('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === viewName));
  const titles = { overview: '세피리아 분석 대시보드', chat: 'AI 분석 대화', data: '데이터 탐색', history: '대화 기록' };
  $('#page-title').textContent = titles[viewName];
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function answerFor(question) {
  if (question.includes('가격')) return '가격 데이터는 21개의 변경 시점 스냅샷으로 구성되어 있어요. 1.0 출시일에는 역대 최저가인 ₩9,900이 기록됐지만, 가격과 플레이어 수의 인과관계는 현재 데이터만으로 단정하기 어렵습니다.';
  if (question.includes('허브') || question.includes('팔로워')) return '플레이어 수와 허브 팔로워가 함께 상위 10% 수준으로 증가한 이벤트는 0.8.3, 0.10.0, 0.11.0, 1.0 등입니다. 두 지표는 같은 관심 증가에 반응할 수 있으므로 독립적인 증거로 보기는 어렵습니다.';
  if (question.includes('최근')) return '1.0 출시 직후 급등한 플레이어 수는 이후 낮아졌지만, M1 분석 기준 패치 전 7일 평균보다 높은 수준을 유지했습니다. 최근 수치는 백엔드 연결 후 최신 CSV 기준으로 다시 계산하도록 만들 예정입니다.';
  return 'M1 분석 기준으로 가장 큰 변화는 1.0 정식 출시입니다. 패치 전 7일 평균 대비 이후 7일 평균이 약 +1,388% 증가했습니다. 다만 정식 출시와 패치가 같은 날이므로 패치 자체의 효과라고 단정할 수는 없습니다.';
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
  } catch (error) {
    document.getElementById(loadingId).outerHTML = `<div class="message assistant error-message"><div class="avatar">!</div><div><span class="message-label">BACKEND ERROR</span><p>${escapeHtml(error.message)}<br><small>FastAPI가 http://127.0.0.1:8000 에서 실행 중인지, backend/.env의 AI_API_KEY가 설정됐는지 확인하세요.</small></p></div></div>`;
  } finally {
    state.isSending = false;
  }
}

function renderHistory() {
  if (!state.conversations.length) return;
  $('#history-list').innerHTML = state.conversations.slice().reverse().map((item) => `<div class="history-row"><div class="history-icon">✦</div><div><strong>${escapeHtml(item.question)}</strong><p>${item.date}</p></div><button class="text-button" data-go-view="chat">열기 →</button></div>`).join('');
  $$('#history-list [data-go-view]').forEach((button) => button.addEventListener('click', () => showView(button.dataset.goView)));
}

function escapeHtml(value) { return value.replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char])); }

function init() {
  renderMetrics(); renderChart(); renderInsights(); renderPatches(); renderSources(); renderDataTable();
  $$('.nav-item').forEach((button) => button.addEventListener('click', () => showView(button.dataset.view)));
  $$('[data-go-view]').forEach((button) => button.addEventListener('click', () => showView(button.dataset.goView)));
  $$('.segmented-control button').forEach((button) => button.addEventListener('click', () => { $$('.segmented-control button').forEach((item) => item.classList.remove('active')); button.classList.add('active'); state.currentFilter = button.dataset.filter; renderDataTable(); }));
  $$('.suggestion-list button').forEach((button) => button.addEventListener('click', () => { showView('chat'); sendMessage(button.dataset.question); }));
  $('#chat-form').addEventListener('submit', (event) => { event.preventDefault(); sendMessage($('#chat-input').value); });
  $('#refresh-button').addEventListener('click', (event) => { event.currentTarget.animate([{ transform: 'rotate(0)' }, { transform: 'rotate(360deg)' }], { duration: 500 }); renderMetrics(); renderDataTable(); });
}

init();
