'use strict';
(() => {
  const app = window.EuroTradeBrief;
  if (!app) return;
  const {esc, link, kst} = app;
  const number = (value, digits = 1) => value.toLocaleString('ko-KR', {maximumFractionDigits:digits});
  const numeric = value => typeof value === 'number' && Number.isFinite(value);
  const usd = value => Math.abs(value) >= 1e12 ? `${number(value / 1e12,2)}조 달러` : `${number(value / 1e8,Math.abs(value) >= 1e10 ? 0 : 1)}억 달러`;
  const people = value => value >= 1e6 ? `${number(value / 1e6,2)}백만 명` : `${number(value / 1e4,2)}만 명`;
  const percent = value => `${number(value,2)}%`;
  const groupName = country => country.group === 'EU' ? 'EU(비유로)' : country.group || (country.eu ? country.euro ? 'EU·유로' : 'EU(비유로)' : '비EU');
  const COLUMNS = [
    ['name','국가'], ['gdp','명목 GDP',usd],
    ['gdpPerCapita','1인당 GDP',v => `${number(v,0)}달러`],
    ['gdpGrowth','성장률',percent], ['population','인구',people],
    ['inflation','물가',percent], ['unemployment','실업률',percent],
    ['policyRate','정책금리',percent],
    ['exports','한국 수출',v => number(v / 1e8,2)],
    ['imports','한국 수입',v => number(v / 1e8,2)]
  ];
  const SORTS = [['','기본 국가 순서'], ...COLUMNS.map(([key,label]) => [key,label])];
  const GROUPS = ['전체','EU·유로','EU(비유로)','비EU'];
  let data = null, group = '전체', sort = '', descending = true, detailCountry = '';
  const panel = () => document.getElementById('country-info');
  const YEARS = ['2025','2026','2027'];
  function sparkline(item, title) {
    const points = (item?.series || []).filter(p => Array.isArray(p) && typeof p[0] === 'string' && numeric(p[1])).slice(-24);
    if (points.length < 2) return '';
    const values = points.map(p => p[1]), low = Math.min(...values), high = Math.max(...values);
    const coords = points.map((p,i) => `${(4 + i * 172 / (points.length - 1)).toFixed(2)},${(high === low ? 25 : 46 - (p[1] - low) * 42 / (high - low)).toFixed(2)}`).join(' ');
    const label = `${title}: ${points[0][0]} ${number(points[0][1],2)}% → ${points.at(-1)[0]} ${number(points.at(-1)[1],2)}%`;
    return `<figure class="stat-spark"><svg viewBox="0 0 180 50" role="img" aria-label="${esc(label)}"><title>${esc(label)}</title><polyline points="${coords}" fill="none" stroke="currentColor" stroke-width="2" vector-effect="non-scaling-stroke"/></svg><figcaption>${esc(points[0][0])} ~ ${esc(points.at(-1)[0])}${item.seriesBasis ? ` · ${esc(item.seriesBasis)}` : ''}</figcaption></figure>`;
  }
  function outlookSource(metric) {
    if (!metric?.source) return '자료 없음';
    return `${link(metric.url,metric.source)} · ${esc(metric.vintage || '')} · ${esc(metric.basis || '')}`;
  }
  function outlookCells(metric) {
    return YEARS.map(year => {
      const point = metric?.values?.[year];
      return `<td class="${year === '2025' ? 'outlook-actual' : 'outlook-forecast'}">${numeric(point?.value) ? esc(number(point.value,1)) + '%' : '<span class="stats-missing">자료 없음</span>'}</td>`;
    }).join('');
  }
  function outlookHTML(countries, detail = false) {
    const rows = detail ? countries : [...(data.aggregates || []), ...countries];
    return `<article class="${detail ? 'stat-card stat-card--wide' : 'card stats-table-card outlook-card'}"><h3>성장·물가 전망 <small>2025 실적 · 2026–2027 전망</small></h3>${!detail && data?.outlookGeneratedAt ? `<p class="stat-meta">전망 갱신 ${esc(kst(data.outlookGeneratedAt,true))}</p>` : ''}<div class="table-scroll" role="region" aria-label="성장·물가 전망표" tabindex="0"><table class="stats-table outlook-table"><caption class="sr-only">실질 GDP 성장률과 연평균 물가상승률. 단위 %. 2026·2027년은 전망.</caption><thead><tr><th scope="col" rowspan="2">${detail ? '지표' : '국가·지역'}</th>${detail ? '' : '<th scope="col" rowspan="2">지표</th>'}${YEARS.map(y => `<th scope="col" class="${y === '2025' ? 'outlook-actual' : 'outlook-forecast'}">${y}</th>`).join('')}</tr><tr>${YEARS.map(y => `<th scope="col" class="${y === '2025' ? 'outlook-actual' : 'outlook-forecast'}">${y === '2025' ? '실적' : '전망'}</th>`).join('')}</tr></thead><tbody>${rows.map(c => ['gdp','inflation'].map((key,i) => `<tr${!detail && c.name === app.getCountry() ? ' class="is-selected"' : ''}>${!detail && i === 0 ? `<th scope="rowgroup" rowspan="2">${esc(c.name)}</th>` : ''}<th scope="row">${key === 'gdp' ? '실질 GDP' : '물가'}</th>${outlookCells(c.outlook?.[key])}</tr>`).join('')).join('')}</tbody></table></div>${detail ? ['gdp','inflation'].map(key => `<p class="stat-meta">${key === 'gdp' ? '성장' : '물가'}: ${outlookSource(countries[0].outlook?.[key])}</p>`).join('') : `<details class="outlook-sources"><summary>지표별 출처·빈티지</summary>${rows.map(c => `<p class="stat-meta"><strong>${esc(c.name)}</strong><br>성장: ${outlookSource(c.outlook?.gdp)}<br>물가: ${outlookSource(c.outlook?.inflation)}</p>`).join('')}</details>`}<p class="stat-meta">AMECO 수준 계열로 전년비 계산. 공표 표와 끝자리 반올림이 다를 수 있음. 물가는 AMECO HICP 우선, 미수록 시 IMF CPI(정의 차이). AMECO Spring 2026 기준 2025 실적·2026–2027 전망 구분. IMF는 API에 판 정보가 없어 조회일만 표시.</p></article>`;
  }
  function metricHTML(title, item, format) {
    const it = item || {}, available = numeric(it.value);
    const period = it.period || it.date || (it.year ? `${it.year}년` : '');
    return `<article class="stat-card"><h4>${esc(title)}</h4><p class="stat-value${available ? '' : ' is-missing'}">${available ? esc(format(it.value)) : '자료 없음'}</p>${period || it.basis ? `<p class="stat-meta">${esc([period,it.basis].filter(Boolean).join(' · '))}</p>` : ''}${it.source || it.url ? `<p class="stat-meta">출처: ${link(it.url,it.source || '원자료')}${it.license ? ` · ${esc(it.license)}` : ''}</p>` : ''}${sparkline(it,title)}${it.note ? `<p class="stat-note">${esc(it.note)}</p>` : ''}</article>`;
  }
  function tradeBlock(label, record) {
    if (!record) return `<section class="trade-block"><h5>${esc(label)}</h5><p class="stat-meta">자료 없음</p></section>`;
    return `<section class="trade-block"><h5>${esc(label)} <span>${esc(record.period || '')}</span></h5><dl class="trade-grid">${[['한국 수출','exports'],['한국 수입','imports'],['한국 수지','balance']].map(([name,key]) => `<div><dt>${name}</dt><dd${key === 'balance' && numeric(record[key]) ? ` class="${record[key] >= 0 ? 'is-surplus' : 'is-deficit'}"` : ''}>${numeric(record[key]) ? `${esc(number(record[key] / 1e8,2))}<small>억 달러</small>` : '자료 없음'}</dd></div>`).join('')}</dl></section>`;
  }
  function tradeHTML(country) {
    const trade = country.trade?.comtrade || {};
    const source = trade.source || data?.sources?.comtrade?.name || 'UN Comtrade';
    const url = trade.url || data?.sources?.comtrade?.url;
    return `<article class="stat-card stat-card--wide"><h4>대한국 교역 <small>한국 보고 기준 · 수출 FOB / 수입 CIF</small></h4>${tradeBlock('연간',trade.annual)}${trade.monthly ? tradeBlock('최근 공개 월',trade.monthly) : ''}<p class="stat-meta">출처: ${link(url,source)}</p>${trade.note ? `<p class="stat-note">${esc(trade.note)}</p>` : ''}</article>`;
  }
  function countryHTML(country, selected = '') {
    const bank = country.centralBank;
    return `<article class="card stats-detail${country.name === selected ? ' is-selected' : ''}"><header class="stats-detail-head"><div><h3>${esc(country.name)} <small lang="en">${esc(country.nameEn || '')}</small></h3><p class="stat-meta">관할 무역관: ${esc(country.office || '자료 없음')}</p></div><span class="group-badge">${esc(groupName(country))}</span></header><div class="stat-cards">${metricHTML('명목 GDP',country.gdp,usd)}${metricHTML('1인당 GDP',country.gdpPerCapita,v => `${number(v,0)}달러`)}${metricHTML('실질 GDP 성장률',country.gdpGrowth,percent)}${metricHTML('인구',country.population,people)}${metricHTML('물가상승률',country.inflation,percent)}${metricHTML('실업률',country.unemployment,percent)}${metricHTML('정책금리',country.policyRate,percent)}${tradeHTML(country)}${outlookHTML([country],true)}</div><footer class="central-bank">중앙은행: ${bank ? link(bank.url,bank.name || '중앙은행') : '<span class="muted">자료 없음</span>'}</footer></article>`;
  }
  function sortValue(country, key) {
    if (key === 'name') return country.name;
    return key === 'exports' || key === 'imports' ? country.trade?.comtrade?.annual?.[key] : country[key]?.value;
  }
  function sortedCountries(countries, selected, selectedGroup = '전체', key = '', desc = true) {
    return countries.filter(c => selectedGroup === '전체' || groupName(c) === selectedGroup || c.name === selected).slice().sort((a,b) => {
      if (a.name === selected) return -1;
      if (b.name === selected) return 1;
      if (!key) return 0;
      const av = sortValue(a,key), bv = sortValue(b,key);
      if (key === 'name') return (desc ? -1 : 1) * av.localeCompare(bv,'ko');
      if (!numeric(av)) return numeric(bv) ? 1 : 0;
      if (!numeric(bv)) return -1;
      return (desc ? -1 : 1) * (av - bv);
    });
  }
  function tableCell(country, key, format) {
    const trade = key === 'exports' || key === 'imports';
    const item = trade ? country.trade?.comtrade?.annual : country[key];
    const value = trade ? item?.[key] : item?.value;
    const period = String(item?.period || item?.date || item?.year || '');
    const compact = /^\d{4}-\d{2}/.test(period) ? period.slice(2,7) : period;
    return `<td>${numeric(value) ? esc(format(value)) : '<span class="stats-missing">–</span>'}${period ? `<small class="stats-cell-period" title="${esc(period)}">${esc(compact)}</small>` : ''}</td>`;
  }
  function tableHTML(countries, selected) {
    const sources = data.sources || {};
    const sourceLinks = [
      link(sources.worldBank?.url || 'https://data.worldbank.org/','World Bank WDI(CC BY 4.0)'),
      link(sources.eurostat?.url || 'https://ec.europa.eu/eurostat/','Eurostat'),
      link(sources.bis?.url || 'https://data.bis.org/topics/CBPOL','BIS'),
      link(sources.comtrade?.url || 'https://comtradeplus.un.org/','UN Comtrade(한국 보고 기준)')
    ];
    return `<article class="card stats-table-card"><h3 id="stats-table-title">전체 국가 비교 <small>한국 수출·수입: 연간, 억 달러</small></h3><p class="stat-meta stats-table-help" id="stats-table-help">국가명을 누르면 아래에 상세 정보를 표시합니다. 열 제목을 눌러 정렬할 수 있습니다.</p><div class="table-scroll" role="region" aria-labelledby="stats-table-title" aria-describedby="stats-table-help" tabindex="0"><table class="stats-table"><caption class="sr-only">국가별 경제 지표와 한국의 연간 수출입 비교. 각 값 아래에 기준 연도·월을 표시합니다.</caption><thead><tr>${COLUMNS.map(([key,label]) => `<th scope="col"${sort === key ? ` aria-sort="${descending ? 'descending' : 'ascending'}"` : ''}><button type="button" class="stats-sort-button" data-sort="${key}">${label}${sort === key ? descending ? ' ↓' : ' ↑' : ''}${key === 'exports' || key === 'imports' ? '<small>연간 · 억 달러</small>' : ''}</button></th>`).join('')}</tr></thead><tbody>${countries.map(country => `<tr data-country="${esc(country.name)}"${country.name === selected ? ' class="is-selected"' : ''}><th scope="row"><button type="button" class="link-button" data-country="${esc(country.name)}" aria-controls="stats-detail" aria-expanded="${country.name === detailCountry}">${esc(country.name)}</button><span class="group-badge">${esc(groupName(country))}</span></th>${COLUMNS.slice(1).map(([key,,format]) => tableCell(country,key,format)).join('')}</tr>`).join('')}</tbody></table></div><p class="stat-meta stats-table-sources">출처: ${sourceLinks.join(' · ')}</p></article>`;
  }
  function failures(status, path = '') {
    if (typeof status === 'string') return /실패|fail|error/i.test(status) ? [`${path}: ${status}`] : [];
    if (!status || typeof status !== 'object') return [];
    return Object.entries(status).flatMap(([key,value]) => failures(value, path ? `${path} · ${key}` : key));
  }
  function render() {
    const root = panel();
    root.setAttribute('aria-busy','false');
    if (!data) {
      root.innerHTML = '<article class="card"><h2>국가 정보</h2><p class="muted">국가 통계를 아직 불러올 수 없습니다. 잠시 후 다시 확인해 주세요.</p></article>';
      return;
    }
    const selected = app.getCountry(), countries = sortedCountries(data.countries,selected,group,sort,descending);
    if (!countries.some(c => c.name === detailCountry)) detailCountry = countries[0]?.name || '';
    const detail = countries.find(c => c.name === detailCountry);
    const errors = failures(data.status);
    root.innerHTML = `<section class="card stats-picker"><div class="stats-head"><div><p class="eyebrow">COUNTRY PROFILE</p><h2>국가 정보 <small>${data.countries.length}개국</small></h2></div></div><p class="stats-updated">통계 기준: World Bank WDI, Eurostat, BIS, UN Comtrade(한국 보고 기준) · 갱신 ${esc(kst(data.generatedAt,true) || '시각 정보 없음')}</p>${errors.length ? `<details class="stat-note"><summary>일부 통계 갱신 실패 · 직전 값 또는 공식 원본 캐시 유지 (${errors.length}개)</summary><p>${errors.map(esc).join('<br>')}</p></details>` : ''}<div class="chips" role="group" aria-label="국가 그룹 필터">${GROUPS.map(g => `<button class="country-chip" type="button" data-group="${g}" aria-pressed="${group === g}">${g}</button>`).join('')}</div><div class="stats-sort"><label for="stats-sort">정렬<select id="stats-sort">${SORTS.map(([value,label]) => `<option value="${value}"${value === sort ? ' selected' : ''}>${label}</option>`).join('')}</select></label><button id="stats-direction" type="button"${sort ? '' : ' disabled'} aria-label="${descending ? '오름차순으로 변경' : '내림차순으로 변경'}">${descending ? '내림차순 ↓' : '오름차순 ↑'}</button><p class="stat-meta" role="status">${countries.length}개국${selected ? ` · ${esc(selected)} 우선 표시` : ''}</p></div></section>${outlookHTML(countries)}${tableHTML(countries,selected)}<div id="stats-detail" class="country-profiles" role="region" aria-label="${esc(detailCountry)} 상세 정보" tabindex="-1">${detail ? countryHTML(detail,selected) : ''}</div><p class="stats-disclaimer muted">지표별 공표 시차와 기준이 다릅니다. 값이 없는 항목은 표에서 –로, 상세 카드에서 자료 없음으로 표시합니다. 한국 수출·수입·수지는 한국 보고 기준입니다.</p>`;
  }
  function rerenderAndFocus(selector) {
    const positions = [...panel().querySelectorAll('.table-scroll')].map(el => el.scrollLeft);
    render();
    panel().querySelectorAll('.table-scroll').forEach((el,i) => { el.scrollLeft = positions[i] || 0; });
    panel().querySelector(selector)?.focus({preventScroll:true});
  }
  function showDetail(name) {
    const country = data?.countries.find(c => c.name === name);
    const detail = panel().querySelector('#stats-detail');
    if (!country || !detail) return;
    detailCountry = country.name;
    detail.innerHTML = countryHTML(country,app.getCountry());
    detail.setAttribute('aria-label',`${detailCountry} 상세 정보`);
    panel().querySelectorAll('.link-button[data-country]').forEach(button => {
      button.setAttribute('aria-expanded',String(button.dataset.country === detailCountry));
    });
    detail.focus({preventScroll:true});
    detail.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',block:'start'});
  }
  function init() {
    panel().addEventListener('click', e => {
      const chip = e.target.closest('[data-group]');
      if (chip) { group = chip.dataset.group; rerenderAndFocus(`[data-group="${group}"]`); }
      const header = e.target.closest('[data-sort]');
      if (header) {
        const key = header.dataset.sort;
        descending = sort === key ? !descending : key !== 'name';
        sort = key;
        rerenderAndFocus(`[data-sort="${sort}"]`);
      }
      const row = e.target.closest('tbody [data-country]');
      if (row) showDetail(row.dataset.country);
      if (e.target.closest('#stats-direction')) { descending = !descending; rerenderAndFocus('#stats-direction'); }
    });
    panel().addEventListener('change', e => {
      if (e.target.id === 'stats-sort') { sort = e.target.value; descending = sort !== 'name'; rerenderAndFocus('#stats-sort'); }
    });
    window.addEventListener('eutb:countrychange', () => {
      const selected = data?.countries.find(c => c.name === app.getCountry());
      if (selected && group !== '전체' && groupName(selected) !== group) group = '전체';
      detailCountry = selected?.name || '';
      render();
    });
    app.statsReady.then(value => { data = value; detailCountry = app.getCountry(); render(); });
  }
  window.EuroTradeStats = {usd, people, metricHTML, countryHTML, sortedCountries, failures, sparkline, outlookHTML};
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
