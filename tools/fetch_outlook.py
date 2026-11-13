#!/usr/bin/env python3
"""AMECO 우선·IMF 보완 전망을 기존 country-stats에 병합 (월간, 무료·무키).

--cache-dir DIR: 네트워크 실패 시에만 해당 디렉터리의 공식 원본을 사용.
파일: ameco0.zip, imf-NGDP_RPCH.json, imf-PCPIPCH.json.
캐시는 취득일(파일 mtime)을 표시하며 실패 상태/종료 코드 3을 유지한다.
"""
import argparse
import csv
import io
import json
import math
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

from fetch_country_stats import KST, OUT_JSON, OUT_JS, http_get

AMECO = 'https://ec.europa.eu/economy_finance/db_indicators/ameco/documents/ameco0.zip'
IMF = 'https://www.imf.org/external/datamapper/api/v1/'
YEARS = ('2025', '2026', '2027')
NOTE = 'AMECO 수준 계열로 전년비 계산. 공표 표와 끝자리 반올림이 다를 수 있음.'


def number(value):
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (ValueError, TypeError):
        return None


def parse_ameco(raw):
    result = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        dates = []
        for name in archive.namelist():
            if not name.lower().endswith('.txt'):
                continue
            dates.append(archive.getinfo(name).date_time[:3])
            for row in csv.DictReader(io.StringIO(archive.read(name).decode('utf-8-sig', errors='replace')), delimiter=';'):
                code = row.get('CODE', '').strip()
                if re.fullmatch(r'[A-Z0-9]+\.(?:1\.1\.0\.0\.OVGD|1\.0\.0\.0\.ZCPIH)', code):
                    result[code] = {y: number(row.get(y)) for y in ('2024', *YEARS)}
        if not result:
            raise ValueError('AMECO 필수 수준 계열 없음')
        file_date = '%04d-%02d-%02d' % max(dates)
    return result, file_date


def ameco_metric(rows, code, vintage, key):
    suffix = '1.1.0.0.OVGD' if key == 'gdp' else '1.0.0.0.ZCPIH'
    series = rows.get(f'{code}.{suffix}', {})
    values = {}
    for y in YEARS:
        a, b = series.get(str(int(y) - 1)), series.get(y)
        value = round((b / a - 1) * 100, 1) if a and b is not None else None
        values[y] = {'value': value, 'kind': 'actual' if y == '2025' else 'forecast'}
    return {'source': 'European Commission AMECO', 'vintage': vintage, 'url': AMECO,
            'indicator': 'OVGD' if key == 'gdp' else 'ZCPIH', 'basis': '실질 GDP 전년비 (%)' if key == 'gdp' else 'HICP 연평균 전년비 (%) · 2015=100 지수',
            'note': NOTE, 'values': values}


def imf_metric(rows, codes, key, accessed):
    ind = 'NGDP_RPCH' if key == 'gdp' else 'PCPIPCH'
    series = next((rows.get(ind, {}).get(c) for c in codes if rows.get(ind, {}).get(c)), {})
    return {'source': f'IMF WEO (Datamapper, 조회일 {accessed})', 'vintage': f'조회일 {accessed} · API 판 정보 없음',
            'url': IMF + ind, 'indicator': ind,
            'basis': '실질 GDP 전년비 (%)' if key == 'gdp' else 'CPI 연평균 상승률 (%) · HICP와 정의 차이',
            'values': {y: {'value': number(series.get(y)), 'kind': 'actual' if y == '2025' else 'forecast'} for y in YEARS}}


def available(metric):
    return any(v['value'] is not None for v in metric['values'].values())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache-dir', type=Path)
    args = ap.parse_args(argv)
    doc = json.loads(OUT_JSON.read_text(encoding='utf-8'))
    now = datetime.now(KST)
    status, imf, accessed = {}, {}, {}

    def obtain(url, filename):
        try:
            raw = http_get(url, timeout=45, retries=1)
            accessed[filename] = now.date().isoformat()
            status[filename] = 'ok'
            return raw
        except Exception as exc:
            status[filename] = f'실패({exc})'
            cache = args.cache_dir / filename if args.cache_dir else None
            if cache and cache.is_file():
                accessed[filename] = datetime.fromtimestamp(cache.stat().st_mtime, KST).date().isoformat()
                status[filename] += f' · 공식 원본 캐시 사용({accessed[filename]})'
                return cache.read_bytes()
            raise

    ameco, vintage = {}, ''
    try:
        ameco, file_date = parse_ameco(obtain(AMECO, 'ameco0.zip'))
        # Known Spring 2026 archive. Do not label a future archive as this vintage.
        vintage = 'Spring 2026 (2026년 봄)' if file_date == '2026-06-02' else f'AMECO 파일일 {file_date}'
        doc.setdefault('sources', {})['ameco'] = {'name': 'European Commission AMECO', 'url': AMECO, 'vintage': vintage, 'fileDate': file_date, 'note': NOTE}
    except Exception as exc:
        status['ameco0.zip'] = status.get('ameco0.zip', '') + f' · 실패({exc})'
    for ind in ('NGDP_RPCH', 'PCPIPCH'):
        filename = f'imf-{ind}.json'
        try:
            imf[ind] = json.loads(obtain(IMF + ind, filename))['values'][ind]
            if not isinstance(imf[ind], dict) or not imf[ind]:
                raise ValueError('IMF 계열 없음')
        except Exception as exc:
            status[filename] = status.get(filename, '') + f' · 실패({exc})'
    if imf:
        doc.setdefault('sources', {})['imf'] = {'name': 'IMF WEO (Datamapper)', 'url': IMF,
            'accessedAt': {ind: accessed.get(f'imf-{ind}.json') for ind in imf}, 'note': 'Datamapper API는 판(vintage) 필드를 제공하지 않음. CPI는 HICP와 정의 차이.'}
    aggregates = {c['id']: c for c in doc.get('aggregates', [])}
    targets = [(c, c['iso3'], ['KOS', 'UVK'] if c['id'] == 'XK' else [c['iso3']]) for c in doc['countries']]
    for ident, name, acode, icode in [('EU', 'EU', 'EU27', 'EU'), ('EA', '유로지역', 'EA21', 'EURO')]:
        c = aggregates.setdefault(ident, {'id': ident, 'name': name})
        targets.append((c, acode, [icode]))
    for country, acode, icodes in targets:
        outlook = country.setdefault('outlook', {})
        for key in ('gdp', 'inflation'):
            metric = ameco_metric(ameco, acode, vintage, key)
            if not available(metric):
                ind = 'NGDP_RPCH' if key == 'gdp' else 'PCPIPCH'
                metric = imf_metric(imf, icodes, key, accessed.get(f'imf-{ind}.json', now.date().isoformat()))
                # On acquisition failure preserve a previously sourced metric.
                if not available(metric) and key in outlook and (not ameco or ind not in imf):
                    continue
            outlook[key] = metric if available(metric) else {'values': {y: {'value': None, 'kind': 'actual' if y == '2025' else 'forecast'} for y in YEARS}, 'note': 'AMECO·IMF 미수록'}
    doc['aggregates'] = [aggregates[k] for k in ('EU', 'EA')]
    doc['outlookGeneratedAt'] = now.isoformat(timespec='seconds')
    doc.setdefault('status', {})['outlook'] = status
    # Keep main statistics timestamp and every unrelated field unchanged.
    text = json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False)
    OUT_JSON.write_text(text + '\n', encoding='utf-8')
    OUT_JS.write_text('window.COUNTRY_STATS = ' + text + ';\n', encoding='utf-8')
    count = sum(any(available(m) for m in c['outlook'].values()) for c in doc['countries'])
    print(f'전망 병합: {count}/{len(doc["countries"])}개국, 집계 {len(doc["aggregates"])}개')
    for key, value in status.items():
        print(f'{key}: {value}')
    return 0 if all(v == 'ok' for v in status.values()) else 3


if __name__ == '__main__':
    sys.exit(main())
