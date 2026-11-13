#!/usr/bin/env python3
"""유럽 통상 브리프 「국가 정보」 통계 수집 (월 1회 실행, 일일 절차와 별개).

사용법: python3 tools/fetch_country_stats.py [--dry-run]
출처(모두 공식·무료 공개 API, 인증키 불필요, 값은 API 응답 그대로 — 임의 추정·입력 없음):
  - World Bank WDI: 명목 GDP(USD), 1인당 GDP(USD), 실질 GDP 성장률, 인구 (연간)
  - Eurostat: HICP 물가상승률(전년동월비, prc_hicp_minr), 실업률(계절조정, une_rt_m) — 수록국만
      Eurostat 미수록국은 World Bank 연간 대체값(FP.CPI.TOTL.ZG, SL.UEM.TOTL.ZS)을 쓰고 출처·연도를 그대로 표시
  - BIS 중앙은행 정책금리(WS_CBPOL): 비유로국은 자국, 유로 사용국은 유로지역(ECB 예금금리 기준 BIS 시계열 XM)
  - UN Comtrade(공개 미리보기 API): 한국 보고 기준 대상국별 수출·수입(연간·월간 최신)
결과: data/country-stats.json, data/country-stats.js. 출처별 실패 시 직전 파일의 값을 유지하고 status에 기록.
"""
import csv
import io
import json
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from countries import COUNTRIES  # noqa: E402

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / 'data/country-stats.json'
OUT_JS = ROOT / 'data/country-stats.js'
UA = 'eu-trade-brief-stats/1.0 (+https://trade-brief-kr.github.io/eu-trade-brief/; research)'
WB = {'gdp': 'NY.GDP.MKTP.CD', 'gdpPerCapita': 'NY.GDP.PCAP.CD', 'gdpGrowth': 'NY.GDP.MKTP.KD.ZG',
      'population': 'SP.POP.TOTL', 'inflationWB': 'FP.CPI.TOTL.ZG', 'unemploymentWB': 'SL.UEM.TOTL.ZS'}
EUROSTAT = 'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
BIS_URL = 'https://stats.bis.org/api/v2/data/dataflow/BIS/WS_CBPOL/1.0/D.?lastNObservations=45&format=csv'
BIS_PAGE = 'https://data.bis.org/topics/CBPOL'
COMTRADE = 'https://comtradeapi.un.org/public/v1'
KOREA = 410
# Comtrade 참조표에 ISO3가 여러 코드로 중복된 국가: 한국 보고 통계가 쓰는 포괄 코드로 고정.
# 모나코(MCO)는 참조표상 'Europe EU, nes'(492)로 잘못 연결되므로 제외(프랑스 251 'France, Monaco'에 포함).
COMTRADE_CODES = {'FR': 251, 'NO': 579, 'CH': 757, 'MC': None}
COMTRADE_NOTE = {'MC': '프랑스 수치에 포함(UN Comtrade 251 France, Monaco)',
                 'LI': '스위스 수치에 포함(UN Comtrade 757 Switzerland, Liechtenstein)'}
# 자국 정책금리 대신 사용하는 통화의 정책금리를 보여줄 국가(공식 통화 협정·일방 사용).
RATE_PROXY = {'ME': ('XM', '유로 사용국(ECB 금리)'), 'XK': ('XM', '유로 사용국(ECB 금리)'),
              'MC': ('XM', '유로 사용국(ECB 금리)'), 'AD': ('XM', '유로 사용국(ECB 금리)'),
              'SM': ('XM', '유로 사용국(ECB 금리)'), 'VA': ('XM', '유로 사용국(ECB 금리)'),
              'LI': ('CH', '스위스 프랑 사용국(SNB 금리)')}
EUROSTAT_GEO = {'GR': 'EL', 'XK': 'XK'}  # Eurostat은 그리스를 EL로 표기


def log(m):
    print(m, file=sys.stderr)


def http_get(url, timeout=60, retries=3, pause=2.0):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = f'HTTP {e.code}'
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.gaierror):
                raise RuntimeError(f'DNS 조회 실패: {e.reason}') from e
            last = str(e.reason)
        except Exception as e:  # noqa: BLE001
            last = type(e).__name__
        time.sleep(pause * (i + 1))
    raise RuntimeError(last or 'unknown')


def http_json(url, **kw):
    try:
        return json.loads(http_get(url, **kw))
    except ValueError:
        raise RuntimeError('JSON 아님') from None


def wb_bulk(ind):
    data = http_json(f'https://api.worldbank.org/v2/country/all/indicator/{ind}?format=json&per_page=20000', timeout=120, retries=5)
    if not (isinstance(data, list) and len(data) > 1 and isinstance(data[1], list)) or data[0].get('pages', 1) != 1:
        raise RuntimeError('형식 오류')
    latest, series = {}, {}
    for row in data[1]:
        k = row.get('countryiso3code')
        if k and row.get('value') is not None:
            series.setdefault(k, []).append([row['date'], row['value']])
            if k not in latest or row['date'] > latest[k]['date']:
                latest[k] = dict(row)
    for k in latest:
        latest[k]['series'] = sorted(series[k])[-12:]
    return latest


def eurostat_latest(dataset, params, geos):
    """국가별 최신값과 짧은 원 관측 시계열. 보간·반올림하지 않음."""
    q = [(k, v) for k, v in params.items() if k != '_since'] + [('geo', g) for g in geos] + [('sinceTimePeriod', params.get('_since', '2024-01'))]
    d = http_json(EUROSTAT + dataset + '?' + urllib.parse.urlencode(q), timeout=90)
    dims, size = d['id'], d['size']
    idx = {k: {v: i for v, i in d['dimension'][k]['category']['index'].items()} for k in dims}
    gi, ti = dims.index('geo'), dims.index('time')
    inv_geo = {i: g for g, i in idx['geo'].items()}
    inv_time = {i: t for t, i in idx['time'].items()}
    series = {}
    for flat, val in d.get('value', {}).items():
        flat = int(flat)
        coords = []
        for s in reversed(size):
            coords.append(flat % s)
            flat //= s
        coords.reverse()
        g, t = inv_geo[coords[gi]], inv_time[coords[ti]]
        if val is not None:
            series.setdefault(g, []).append([t, val])
    out = {}
    for g, points in series.items():
        points = sorted(points)[-12 if params.get('freq') == 'Q' else -24:]
        out[g] = {'value': points[-1][1], 'period': points[-1][0], 'series': points}
    return out


def bis_rates(url=BIS_URL):
    latest, series = {}, {}
    for row in csv.DictReader(io.StringIO(http_get(url).decode('utf-8-sig'))):
        v = (row.get('OBS_VALUE') or '').strip()
        try:
            fv = float(v)
        except ValueError:
            continue
        if fv != fv:  # NaN
            continue
        a, p = row.get('REF_AREA'), row.get('TIME_PERIOD')
        if not a or not p:
            continue
        series.setdefault(a, []).append([p, fv])
        if a not in latest or p > latest[a]['date']:
            latest[a] = {'value': fv, 'date': p}
    for a in latest:
        latest[a]['series'] = sorted(series[a])[-24:]
    return latest


def comtrade(countries):
    ref = http_json('https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json')
    by3 = {r['PartnerCodeIsoAlpha3']: int(r['id']) for r in ref.get('results', [])
           if r.get('PartnerCodeIsoAlpha3') and not r.get('isGroup') and not r.get('entryExpiredDate')}
    code_of = {c[0]: by3[c[1]] for c in countries if c[1] in by3}
    for iso2, code in COMTRADE_CODES.items():
        if code is None:
            code_of.pop(iso2, None)
        else:
            code_of[iso2] = code
    res, meta = {'annual': {}, 'monthly': {}}, {}
    for freq, key in (('A', 'annual'), ('M', 'monthly')):
        time.sleep(1.5)
        da = http_json(f'{COMTRADE}/getDA/C/{freq}/HS?reporterCode={KOREA}')
        periods = [str(r['period']) for r in da.get('data', []) if r.get('period')]
        if not periods:
            continue
        period = max(periods)
        label = period if freq == 'A' else f'{period[:4]}-{period[4:6]}'
        meta[key] = label
        time.sleep(1.5)
        q = urllib.parse.urlencode({'reporterCode': KOREA, 'partnerCode': ','.join(map(str, sorted(set(code_of.values())))),
                                    'period': period, 'flowCode': 'X,M', 'cmdCode': 'TOTAL', 'customsCode': 'C00',
                                    'motCode': 0, 'partner2Code': 0})
        d = http_json(f'{COMTRADE}/preview/C/{freq}/HS?{q}', timeout=90)
        if d.get('error'):
            raise RuntimeError(str(d['error'])[:120])
        vals = {}
        for r in d.get('data', []):
            f = {'X': 'exports', 'M': 'imports'}.get(r.get('flowCode'))
            if f and r.get('primaryValue') is not None:
                vals.setdefault(int(r['partnerCode']), {})[f] = float(r['primaryValue'])
        for iso2, code in code_of.items():
            v = vals.get(code)
            if v and 'exports' in v and 'imports' in v:
                res[key][iso2] = {'period': label, 'exports': v['exports'], 'imports': v['imports'],
                                  'balance': v['exports'] - v['imports']}
    return res, meta


def main(argv):
    dry = '--dry-run' in argv
    try:
        previous = json.loads(OUT_JSON.read_text(encoding='utf-8'))
        prev = {c['id']: c for c in previous.get('countries', [])}
    except (OSError, ValueError):
        previous, prev = {}, {}
    status, rows = {}, {}

    wb = {}
    for key, ind in WB.items():
        try:
            wb[key] = wb_bulk(ind)
            status[f'worldBank:{ind}'] = 'ok'
        except Exception as e:  # noqa: BLE001
            status[f'worldBank:{ind}'] = f'실패({e})'
            log(f'World Bank {ind} 실패: {e}')

    geos = [EUROSTAT_GEO.get(c[0], c[0]) for c in COUNTRIES]
    euro = {}
    for key, ds, params in (
        ('gdpGrowth', 'namq_10_gdp', {'unit': 'CLV_PCH_SM', 's_adj': 'SCA', 'na_item': 'B1GQ', 'freq': 'Q', '_since': f'{datetime.now(KST).year - 3}-Q1'}),
        ('inflation', 'prc_hicp_minr', {'unit': 'RCH_A', 'coicop18': 'TOTAL', 'freq': 'M', '_since': '2025-01'}),
        ('unemployment', 'une_rt_m', {'s_adj': 'SA', 'age': 'TOTAL', 'sex': 'T', 'unit': 'PC_ACT', 'freq': 'M', '_since': '2025-01'}),
    ):
        try:
            euro[key] = eurostat_latest(ds, dict(params), geos)
            status[f'eurostat:{ds}'] = f'ok({len(euro[key])}개국)'
        except Exception as e:  # noqa: BLE001
            status[f'eurostat:{ds}'] = f'실패({e})'
            log(f'Eurostat {ds} 실패: {e}')
    try:
        bis = bis_rates()
        status['bis'] = f'ok({len(bis)}개 지역)'
    except Exception as e:  # noqa: BLE001
        bis = None
        status['bis'] = f'실패({e})'
    try:
        bis_monthly = bis_rates(BIS_URL.replace('/D.?lastNObservations=45', '/M.?lastNObservations=24'))
        status['bis:series'] = f'ok({len(bis_monthly)}개 지역)'
    except Exception as e:
        bis_monthly = {}
        status['bis:series'] = f'실패({e})'
    try:
        trade, tmeta = comtrade(COUNTRIES)
        status['comtrade'] = f"ok(연간 {tmeta.get('annual')} {len(trade['annual'])}개국, 월간 {tmeta.get('monthly')} {len(trade['monthly'])}개국)"
    except Exception as e:  # noqa: BLE001
        trade, tmeta = None, {}
        status['comtrade'] = f'실패({e})'

    def wb_item(key, c, field_prev):
        ind = WB[key]
        url = f'https://data.worldbank.org/indicator/{ind}?locations={c[0]}'
        if key not in wb:
            return field_prev
        row = wb[key].get(c[1])
        if not row:
            return {'value': None, 'source': 'World Bank', 'url': url, 'note': 'World Bank 미수록'}
        item = {'value': row['value'], 'year': row['date'], 'source': 'World Bank WDI', 'license': 'CC BY 4.0', 'url': url}
        if key in ('gdpGrowth', 'inflationWB', 'unemploymentWB'):
            item['series'] = row['series']
            item['seriesBasis'] = '연간 (%)'
        return item

    out = []
    for c in COUNTRIES:
        iso2, iso3, name, eng, office, is_eu, is_euro, cb, cburl = c
        p = prev.get(iso2, {})
        geo = EUROSTAT_GEO.get(iso2, iso2)
        r = {'id': iso2, 'iso3': iso3, 'name': name, 'nameEn': eng, 'office': office, 'eu': is_eu, 'euro': is_euro,
             'group': 'EU·유로' if is_euro else ('EU' if is_eu else '비EU'),
             'centralBank': {'name': cb, 'url': cburl} if cb else None}
        for key in ('gdp', 'gdpPerCapita', 'gdpGrowth', 'population'):
            r[key] = wb_item(key, c, p.get(key))
        growth = euro.get('gdpGrowth', {}).get(geo)
        if growth:
            r['gdpGrowth'] = dict(growth, basis='분기 전년동기비·계절 및 달력조정 (%)', seriesBasis='분기 전년동기비 (%)', source='Eurostat', url='https://ec.europa.eu/eurostat/databrowser/view/namq_10_gdp/default/table')
        elif 'gdpGrowth' not in euro and (p.get('gdpGrowth') or {}).get('source') == 'Eurostat':
            r['gdpGrowth'] = p['gdpGrowth']
        if 'outlook' in p:
            r['outlook'] = p['outlook']
        for key, ds, wbkey, page in (
            ('inflation', 'prc_hicp_minr', 'inflationWB', 'https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_minr/default/table'),
            ('unemployment', 'une_rt_m', 'unemploymentWB', 'https://ec.europa.eu/eurostat/databrowser/view/une_rt_m/default/table'),
        ):
            if key not in euro:
                r[key] = p.get(key)
                continue
            hit = euro[key].get(geo)
            if hit:
                r[key] = {**hit, 'seriesBasis': '월간 전년동월비 (%)' if key == 'inflation' else '월간·계절조정 (%)', 'basis': 'HICP 전년동월비' if key == 'inflation' else '월간·계절조정',
                          'source': 'Eurostat', 'url': page}
            else:
                w = wb_item(wbkey, c, p.get(key))
                if w and w.get('value') is not None:
                    w = dict(w, basis='CPI 연간' if key == 'inflation' else '연간(ILO 모형추정)')
                r[key] = w
        if bis is None:
            r['policyRate'] = p.get('policyRate')
        else:
            area, basis = ('XM', '유로지역(ECB)') if is_euro else RATE_PROXY.get(iso2, (iso2, '자국 중앙은행'))
            hit = bis.get(area)
            r['policyRate'] = ({'value': hit['value'], 'date': hit['date'], 'unit': '%', 'source': 'BIS',
                                'basis': basis, 'url': BIS_PAGE}
                               if hit else {'value': None, 'source': 'BIS', 'url': BIS_PAGE, 'note': 'BIS 미수록'})
            if hit:
                monthly = bis_monthly.get(area)
                r['policyRate']['series'] = monthly['series'] if monthly else hit['series']
                r['policyRate']['seriesBasis'] = '월간 관측 (%)' if monthly else '일간 관측 (%)'
                if not monthly and (p.get('policyRate') or {}).get('series'):
                    r['policyRate']['series'] = p['policyRate']['series']
                    r['policyRate']['seriesBasis'] = p['policyRate'].get('seriesBasis', '')
        if trade is None:
            r['trade'] = p.get('trade')
        else:
            r['trade'] = {'comtrade': {'annual': trade['annual'].get(iso2), 'monthly': trade['monthly'].get(iso2),
                                       'source': 'UN Comtrade (한국 보고 기준)', 'url': 'https://comtradeplus.un.org/'}}
            if iso2 in COMTRADE_NOTE:
                r['trade']['comtrade']['note'] = COMTRADE_NOTE[iso2]
        out.append(r)

    doc = {'generatedAt': datetime.now(KST).replace(microsecond=0).isoformat(), 'status': status,
           'sources': {
               'worldBank': {'name': 'World Bank World Development Indicators', 'url': 'https://data.worldbank.org/', 'license': 'CC BY 4.0'},
               'eurostat': {'name': 'Eurostat', 'url': 'https://ec.europa.eu/eurostat/', 'license': 'CC BY 4.0 (Eurostat 재사용 정책)'},
               'bis': {'name': 'BIS Central bank policy rates', 'url': BIS_PAGE},
               'comtrade': {'name': 'UN Comtrade (public preview)', 'url': 'https://comtradeplus.un.org/', 'periods': tmeta}},
           'countries': out}
    for key in ('aggregates', 'outlookGeneratedAt'):
        if key in previous:
            doc[key] = previous[key]
    for key in ('ameco', 'imf'):
        if key in previous.get('sources', {}):
            doc['sources'][key] = previous['sources'][key]
    if 'outlook' in previous.get('status', {}):
        doc['status']['outlook'] = previous['status']['outlook']
    for k, v in status.items():
        log(f'{k}: {v}')
    if dry:
        print(json.dumps(doc, ensure_ascii=False, indent=1)[:3000])
        return 0
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    OUT_JS.write_text('window.COUNTRY_STATS = ' + json.dumps(doc, ensure_ascii=False, indent=2) + ';\n', encoding='utf-8')
    print(f'작성: {OUT_JSON.relative_to(ROOT)} ({len(out)}개국)')
    return 0 if all(not str(v).startswith('실패') for v in status.values()) else 3


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
