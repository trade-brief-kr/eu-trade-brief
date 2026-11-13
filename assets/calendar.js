'use strict';
(() => {
  const app = window.EuroTradeBrief;
  if (!app) return;
  const {esc, link, kst} = app;
  let data;
  const visibleEvents = (events, country) => events.filter(e => !country || e.country === 'EU' || e.country === country);
  function render() {
    const root = document.getElementById('calendar');
    root.setAttribute('aria-busy', 'false');
    if (!data) {
      root.innerHTML = '<article class="card"><h2>주요 일정</h2><p class="muted">일정을 불러올 수 없습니다. 다음 갱신 후 다시 확인해 주세요.</p></article>';
      return;
    }
    const selected = app.getCountry();
    const events = visibleEvents(data.events, selected).slice().sort((a,b) => a.date.localeCompare(b.date));
    const days = new Map();
    events.forEach(e => { if (!days.has(e.date)) days.set(e.date, []); days.get(e.date).push(e); });
    const partial = Object.values(data.status || {}).some(s => s?.ok === false);
    const expired = data.end < new Intl.DateTimeFormat('sv-SE', {timeZone:'Asia/Seoul'}).format(new Date());
    root.innerHTML = `<article class="card"><p class="eyebrow">EUROPE CALENDAR</p><h2>주요 일정</h2><p class="muted">${esc(data.start)} ~ ${esc(data.end)} · ${selected ? `EU + ${esc(selected)}` : '전체'} · ${events.length}건</p><p class="stat-meta">갱신 ${esc(kst(data.generatedAt,true))} · 조회 기준 ${esc(data.asOf)} (KST)</p><p class="stat-meta">공식 공표 날짜 기준. 시각·시간대가 있는 일정은 KST로 변환하며 날짜만 공표한 일정은 현지 공표일을 유지합니다. 일정은 변경될 수 있으므로 원문을 확인해 주세요.</p>${expired ? '<p class="stat-note">수록 기간이 지났습니다. 주간 일정 갱신이 필요합니다.</p>' : ''}${partial ? '<p class="stat-note">일부 출처를 갱신하지 못해 확인된 일정만 표시합니다.</p>' : ''}</article>${days.size ? [...days].map(([date, items]) => `<section class="card calendar-day"><h3><time datetime="${esc(date)}">${esc(date)}</time></h3><ul>${items.map(e => `<li><span class="group-badge">${esc(e.category)}</span> <strong>${esc(e.title)}</strong><p class="stat-meta">${esc(e.country)} · ${esc(e.entity)} · ${link(e.url,e.source)}</p>${e.note ? `<p class="stat-meta">${esc(e.note)}</p>` : ''}</li>`).join('')}</ul></section>`).join('') : '<p class="card muted">선택 국가와 EU 차원의 확인된 주요 일정이 없습니다.</p>'}<details class="card calendar-sources"><summary>출처 및 수집 상태</summary><ul>${(data.sources || []).map(s => `<li>${link(s.url,s.name)} — ${esc(data.status?.[s.id]?.message || '상태 정보 없음')}</li>`).join('')}</ul></details>`;
  }
  function init() {
    window.addEventListener('eutb:countrychange',render);
    app.readData('data/calendar', () => window.CALENDAR_DATA, d => d && Array.isArray(d.events) && app.validDate(d.start) && app.validDate(d.end))
      .then(d => { data = d; render(); }).catch(() => render());
  }
  window.EuroTradeCalendar = {visibleEvents};
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
