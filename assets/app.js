'use strict';
(() => {
  const FALLBACK_COUNTRIES = ['독일','프랑스','영국','이탈리아','스페인','네덜란드','폴란드','벨기에','스웨덴','스위스','오스트리아','체코','헝가리','슬로바키아','루마니아','덴마크','핀란드','노르웨이','아일랜드','포르투갈','그리스','불가리아','크로아티아','슬로베니아','세르비아','리투아니아','라트비아','에스토니아','룩셈부르크','키프로스','몰타','아이슬란드','알바니아','북마케도니아','보스니아-헤르체고비나','몬테네그로','코소보','리히텐슈타인','모나코','안도라','산마리노','교황청'];
  const CATEGORIES = ['국제·외교','정책·규제','경제동향','산업동향','대외교역','에너지'];
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function safeUrl(value) {
    if (typeof value !== 'string' || !/^https?:\/\//i.test(value)) return '';
    try { const u = new URL(value); return ['http:', 'https:'].includes(u.protocol) ? u.href : ''; } catch { return ''; }
  }
  function link(url, label, className = '') {
    const href = safeUrl(url);
    return href ? `<a class="${esc(className)}" href="${esc(href)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>` : esc(label);
  }
  function validDate(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const d = new Date(value + 'T00:00:00Z');
    return Number.isFinite(d.getTime()) && d.toISOString().slice(0, 10) === value;
  }
  const dotted = value => String(value || '').replaceAll('-', '.');
  function kst(value, full = false) {
    if (!value) return '';
    const raw = String(value);
    const date = new Date(raw + (/T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?$/.test(raw) ? '+09:00' : ''));
    if (!Number.isFinite(date.getTime())) return '';
    const parts = Object.fromEntries(new Intl.DateTimeFormat('en-GB', {timeZone:'Asia/Seoul', year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', hourCycle:'h23'}).formatToParts(date).map(p => [p.type,p.value]));
    return full ? `${parts.year}.${parts.month}.${parts.day} ${parts.hour}:${parts.minute} KST` : `${Number(parts.month)}월 ${Number(parts.day)}일 ${parts.hour}:${parts.minute} KST 갱신`;
  }
  const script = document.currentScript || document.querySelector('script[src*="assets/app.js"]');
  const version = script ? new URL(script.src, location.href).searchParams.get('v') || '1' : '1';
  const bust = path => path + (path.includes('?') ? '&' : '?') + 'v=' + encodeURIComponent(version);
  const pendingScripts = new Map();
  function loadScript(path) {
    if (pendingScripts.has(path)) return pendingScripts.get(path);
    const promise = new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = bust(path);
      s.onload = () => { s.remove(); resolve(); };
      s.onerror = () => { s.remove(); reject(new Error('missing')); };
      document.head.appendChild(s);
    });
    pendingScripts.set(path, promise);
    return promise.finally(() => pendingScripts.delete(path));
  }
  // JSON is authoritative on HTTP(S); preloaded scripts also support file://.
  async function readData(path, fallback, validate = value => value != null) {
    try {
      const response = await fetch(bust(path + '.json'), {cache:'no-cache'});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const value = await response.json();
      if (!validate(value)) throw new Error('format');
      return value;
    } catch {
      if (validate(fallback())) return fallback();
      await loadScript(path + '.js');
      const value = fallback();
      if (!validate(value)) throw new Error('format');
      return value;
    }
  }
  function usable(report) {
    return !!report && validDate(report.date) && Array.isArray(report.topIssues) && report.topIssues.every(t => t && typeof t.text === 'string') && Array.isArray(report.countryNews) && report.countryNews.every(c => c && typeof c.country === 'string' && Array.isArray(c.items) && c.items.every(i => i && typeof i.title === 'string' && Array.isArray(i.bullets) && i.bullets.every(b => b && typeof b.text === 'string')));
  }
  function orderNews(report, selected = '', names = FALLBACK_COUNTRIES) {
    const rank = name => name === selected ? -1 : names.includes(name) ? names.indexOf(name) : names.length;
    return (report.countryNews || []).filter(c => c.items.length).slice().sort((a,b) => rank(a.country) - rank(b.country));
  }
  function sourceHTML(s, showDate = true) {
    const name = s.source || (safeUrl(s.url) ? '원문' : '');
    return (name ? link(s.url, `(${name})`, 'source') : '') +
      (safeUrl(s.altUrl) ? ' ' + link(s.altUrl, '「재게재」', 'source-alt') : '') +
      (showDate && s.date ? ` <span class="source-date">게재 ${esc(dotted(s.date))}</span>` : '');
  }
  function itemHTML(item) {
    const category = item.category ? `<span class="badge cat-${CATEGORIES.indexOf(item.category)}">${esc(item.category)}</span>` : '';
    return `<article class="issue"><h4>${esc(item.title)}${category}${item.korea === true ? '<span class="badge korea-badge">한국 관련</span>' : ''}</h4><ul>${item.bullets.map(b => `<li class="bullet">${esc(b.text)} ${sourceHTML(b)}</li>`).join('')}</ul>${item.sources?.length ? `<p class="sources">출처: ${item.sources.map(s => sourceHTML(s)).join(' · ')}</p>` : ''}</article>`;
  }
  function reportHTML(report, selected = '', names = FALLBACK_COUNTRIES) {
    let html = `<section class="card top">${typeof report.lead === 'string' && report.lead.trim() ? `<p class="lead">${esc(report.lead)}</p>` : ''}<h2>★ EU Top Issues</h2>${report.coverage ? `<p class="coverage">${esc(report.coverage)}</p>` : ''}<ul class="top-list">${report.topIssues.map(t => `<li class="bullet${selected && t.countries?.includes(selected) ? ' is-selected' : ''}">${esc(t.text)} ${sourceHTML(t)}</li>`).join('')}</ul></section>`;
    const news = orderNews(report, selected, names);
    html += `<section class="card news-block"><h2>★ 일일보도동향</h2>${news.length ? news.map(c => `<section class="country-section${selected === c.country ? ' is-selected' : ''}"><h3>□ ${esc(c.country)}</h3>${c.items.map(itemHTML).join('')}</section>`).join('') : '<p class="muted">이 보고서에 수록된 국가별 보도가 없습니다.</p>'}</section>`;
    if (report.notes?.length) html += `<footer class="notes">${report.notes.map(n => `<p>${esc(n)}</p>`).join('')}</footer>`;
    return html;
  }
  function sourceText(s) {
    return [s.source ? `(${s.source})` : '', safeUrl(s.url), safeUrl(s.altUrl) ? `「재게재」 ${safeUrl(s.altUrl)}` : '', s.date ? `게재 ${s.date}` : ''].filter(Boolean).join(' ');
  }
  function plainText(report, selected = '', names = FALLBACK_COUNTRIES) {
    if (!report) return '';
    const out = ['유럽 통상 브리프', dotted(report.date), kst(report.generatedAt), report.coverage || '', '', ...(typeof report.lead === 'string' && report.lead.trim() ? [report.lead, ''] : []), '★ EU Top Issues'];
    report.topIssues.forEach(t => out.push(`ㅇ ${t.text} ${sourceText(t)}`.trim()));
    out.push('', '★ 일일보도동향');
    orderNews(report, selected, names).forEach(c => {
      out.push('', `□ ${c.country}`);
      c.items.forEach(i => {
        out.push(`${i.title}${i.category ? ` [${i.category}]` : ''}${i.korea === true ? ' [한국 관련]' : ''}`);
        i.bullets.forEach(b => out.push(`ㅇ ${b.text} ${sourceText(b)}`.trim()));
        if (i.sources?.length) out.push('출처: ' + i.sources.map(sourceText).join(' · '));
      });
    });
    if (report.notes?.length) out.push('', ...report.notes);
    return out.filter(x => x !== undefined).join('\n');
  }
  function searchIndex(entries, query) {
    const q = query.trim().toLocaleLowerCase('ko');
    if (!q) return [];
    return entries.flatMap(e => {
      const titles = (e.titles || []).filter(t => t && typeof t.t === 'string');
      const all = [...titles];
      if (e.topIssueHeadline && !titles.some(t => t.t === e.topIssueHeadline)) all.unshift({c:'EU',t:e.topIssueHeadline});
      return all.filter(t => t.t.toLocaleLowerCase('ko').includes(q)).map(t => ({date:e.date, c:t.c || 'EU', t:t.t}));
    });
  }
  let names = [...FALLBACK_COUNTRIES], selected = '', report = null, latest = null, entries = [], requested = '', loading = false, ready = false, error = '', activeTab = 0, token = 0;
  const cache = new Map();
  try { selected = localStorage.getItem('eutb.country') || ''; } catch { /* Storage is optional. */ }
  function updateCountries() {
    if (!names.includes(selected)) selected = '';
    $('country').innerHTML = '<option value="">전체</option>' + names.map(n => `<option value="${esc(n)}">${esc(n)}</option>`).join('');
    $('country').value = selected;
  }
  function setCountry(name) {
    selected = names.includes(name) ? name : '';
    try { localStorage.setItem('eutb.country', selected); } catch { /* file:// or private mode */ }
    updateCountries(); render();
    window.dispatchEvent(new CustomEvent('eutb:countrychange', {detail:{country:selected}}));
  }
  const latestDate = () => entries[0]?.date || latest?.date || '';
  function updateChrome() {
    const current = requested || report?.date || '';
    const options = [...entries];
    if (validDate(current) && !options.some(e => e.date === current)) options.push({date:current});
    options.sort((a,b) => b.date.localeCompare(a.date));
    $('archive-date').innerHTML = options.length ? options.map(e => `<option value="${esc(e.date)}">${esc(dotted(e.date))}${e.date === latestDate() ? ' (최신)' : ''}</option>`).join('') : '<option value="">보고서 없음</option>';
    $('archive-date').value = current;
    $('archive-date').disabled = loading || !options.length;
    const pos = entries.findIndex(e => e.date === current);
    $('prev-day').disabled = loading || pos < 0 || pos >= entries.length - 1;
    $('next-day').disabled = loading || pos <= 0;
    const old = !!latestDate() && (!!error || (!!current && current !== latestDate()));
    $('archive-banner').hidden = activeTab !== 0 || !old;
    $('archive-banner-text').textContent = error ? error : `지난 보고서(${dotted(current)})를 보고 있습니다.`;
    $('archive-controls').hidden = activeTab !== 0;
    $('copy').hidden = activeTab !== 0;
    $('copy').disabled = !report || loading || activeTab !== 0;
  }
  function render() {
    $('brief').setAttribute('aria-busy', String(!ready || loading));
    $('brief').innerHTML = report ? reportHTML(report, selected, names) : `<article class="card"><p class="muted" role="status">${esc(error || (!ready || loading ? '보고서를 불러오고 있습니다.' : '보고서가 아직 없습니다.'))}</p></article>`;
    $('report-date').textContent = report ? `${dotted(report.date)} (${new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',weekday:'long'}).format(new Date(report.date + 'T00:00:00+09:00'))})` : loading ? '보고서 불러오는 중' : error ? '보고서를 불러오지 못했습니다' : '보고서가 아직 없습니다';
    $('updated').textContent = report ? kst(report.generatedAt) : '';
    updateChrome();
  }
  function syncUrl(date) {
    const url = new URL(location.href);
    if (date === latestDate()) url.searchParams.delete('date'); else url.searchParams.set('date', date);
    try { history.replaceState(null, '', url.href); } catch { /* Some file:// browsers restrict history. */ }
  }
  async function loadReport(date) {
    if (!validDate(date)) throw new Error('date');
    if (latest?.date === date) return latest;
    if (cache.has(date)) return cache.get(date);
    const value = await readData(`data/archive/${date}`, () => window.REPORT_ARCHIVE?.[date], r => usable(r) && r.date === date);
    cache.set(date, value);
    return value;
  }
  async function showDate(date, write = true) {
    const id = ++token;
    requested = date; report = null; error = ''; loading = true;
    if (write && validDate(date)) syncUrl(date);
    render();
    try { const value = await loadReport(date); if (id !== token) return; report = value; }
    catch { if (id !== token) return; error = validDate(date) ? `${dotted(date)} 보고서를 불러오지 못했습니다.` : '보고서 날짜가 올바르지 않습니다.'; }
    if (id !== token) return;
    loading = false; render();
  }
  function selectTab(index) {
    activeTab = index;
    ['brief-tab','country-tab','calendar-tab'].forEach((id,i) => {
      $(id).setAttribute('aria-selected', String(i === index)); $(id).tabIndex = i === index ? 0 : -1;
      $(['brief','country-info','calendar'][i]).hidden = i !== index;
    });
    $('search-results').hidden = true;
    try { const u = new URL(location.href); u.hash = ['', 'country-info', 'calendar'][index]; history.replaceState(history.state, '', u); } catch (_) {}
    updateChrome();
  }
  function renderSearch() {
    const q = $('search').value.trim(), box = $('search-results');
    if (!q) { box.hidden = true; return; }
    const hits = searchIndex(entries, q);
    box.innerHTML = `<h2>‘${esc(q)}’ 검색 결과 (${hits.length}건)</h2>${hits.length ? `<ul class="result-list">${hits.map(hit => {
      const url = new URL(location.href); url.searchParams.set('date', hit.date);
      return `<li><a href="${esc(url.href)}" data-date="${esc(hit.date)}"><span class="result-meta">${esc(dotted(hit.date))} · [${esc(hit.c)}]</span><span class="result-title">${esc(hit.t)}</span></a></li>`;
    }).join('')}</ul>` : '<p class="muted">일치하는 보도가 없습니다. 주요 이슈와 국가별 제목에서 검색합니다.</p>'}<button class="close-search" type="button" data-close-search>닫기</button>`;
    box.hidden = false;
  }
  async function copyReport() {
    if (!report || loading) return;
    const text = plainText(report, selected, names);
    const done = () => { $('status').textContent = '보고서 텍스트를 복사했습니다.'; };
    try { await navigator.clipboard.writeText(text); done(); return; } catch { /* Legacy and file:// fallback */ }
    const focus = document.activeElement, area = document.createElement('textarea');
    area.value = text; area.setAttribute('aria-label','복사할 보고서'); area.style.cssText = 'position:fixed;left:-9999px;top:0';
    document.body.appendChild(area); area.select();
    try { if (!document.execCommand('copy')) throw new Error('copy'); done(); }
    catch {
      $('status').textContent = '자동 복사가 지원되지 않습니다. 아래 텍스트를 선택해 복사해 주세요.';
      const fallback = document.createElement('textarea'); fallback.className = 'copy-fallback'; fallback.value = text; fallback.setAttribute('aria-label','복사할 보고서');
      $('status').appendChild(fallback); fallback.focus(); fallback.select();
      area.remove(); return;
    }
    area.remove(); focus?.focus({preventScroll:true});
  }
  async function initReports() {
    const [r, list] = await Promise.all([
      readData('data/report', () => window.REPORT_DATA, usable).catch(() => null),
      readData('data/archive/index', () => window.REPORT_INDEX, Array.isArray).catch(() => [])
    ]);
    latest = r;
    entries = list.filter((e,i,a) => e && validDate(e.date) && a.findIndex(x => x?.date === e.date) === i);
    if (latest && !entries.some(e => e.date === latest.date)) entries.push({date:latest.date, topIssueHeadline:latest.topIssues[0]?.text || '', titles:latest.countryNews.flatMap(c => c.items.map(i => ({c:c.country,t:i.title}))).concat(latest.topIssues.map(t => ({c:'EU',t:t.text})))});
    entries.sort((a,b) => b.date.localeCompare(a.date)); ready = true;
    const want = new URL(location.href).searchParams.get('date') || latestDate();
    if (want) await showDate(want, false); else render();
    if ($('search').value.trim()) renderSearch();
  }
  let statsReady;
  function init() {
    updateCountries();
    $('country').addEventListener('change', e => setCountry(e.target.value));
    $('reset').addEventListener('click', () => setCountry(''));
    $('copy').addEventListener('click', copyReport);
    ['brief-tab','country-tab','calendar-tab'].forEach((id,i) => $(id).addEventListener('click', () => selectTab(i)));
    if (/^#(country-info|stats|country)$/.test(location.hash)) selectTab(1);
    if (location.hash === '#calendar') selectTab(2);
    window.addEventListener('hashchange', () => selectTab(location.hash === '#calendar' ? 2 : /^#(country-info|stats|country)$/.test(location.hash) ? 1 : 0));
    $('tabs').addEventListener('keydown', e => {
      if (!['ArrowLeft','ArrowRight','Home','End'].includes(e.key)) return;
      e.preventDefault(); const n = e.key === 'Home' ? 0 : e.key === 'End' ? 2 : (activeTab + (e.key === 'ArrowRight' ? 1 : 2)) % 3;
      selectTab(n); $(['brief-tab','country-tab','calendar-tab'][n]).focus();
    });
    $('archive-date').addEventListener('change', e => showDate(e.target.value));
    [['prev-day',1],['next-day',-1]].forEach(([id,step]) => $(id).addEventListener('click', () => {
      const pos = entries.findIndex(e => e.date === requested); if (pos >= 0 && entries[pos + step]) showDate(entries[pos + step].date);
    }));
    $('to-latest').addEventListener('click', () => { if (latestDate()) showDate(latestDate()); });
    $('search-form').addEventListener('submit', e => { e.preventDefault(); renderSearch(); });
    $('search').addEventListener('input', () => { if (!$('search').value.trim()) $('search-results').hidden = true; });
    $('search-results').addEventListener('click', e => {
      if (e.target.closest('[data-close-search]')) { $('search-results').hidden = true; $('search').focus(); return; }
      const a = e.target.closest('a[data-date]');
      if (!a || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || e.button > 0) return;
      e.preventDefault(); selectTab(0); showDate(a.dataset.date).then(() => { $('brief').focus({preventScroll:true}); $('main').scrollIntoView({block:'start'}); });
    });
    window.addEventListener('popstate', () => { if (ready) showDate(new URL(location.href).searchParams.get('date') || latestDate(), false); });
    statsReady = readData('data/country-stats', () => window.COUNTRY_STATS, d => d && Array.isArray(d.countries) && d.countries.length > 0 && d.countries.every(c => c && typeof c.name === 'string')).catch(() => null).then(d => {
      if (d) { names = d.countries.map(c => c.name); updateCountries(); render(); }
      return d;
    });
    api.statsReady = statsReady;
    initReports();
  }
  const api = {FALLBACK_COUNTRIES, esc, safeUrl, link, validDate, kst, bust, readData, usable, orderNews, reportHTML, plainText, searchIndex, getCountry:() => selected, getCountries:() => [...names], setCountry};
  window.EuroTradeBrief = api;
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
