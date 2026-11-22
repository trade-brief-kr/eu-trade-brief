#!/usr/bin/env python3
"""유럽 통상 브리프: report.json 스키마 검증 + data/report.js(file:// 대체본) + index.html 캐시 버전.

사용법: python3 tools/build_report_js.py [--check PATH]
  인자 없음  data/report.json 검증 후 data/report.js 작성, index.html ?v= 갱신
  --check    지정 파일만 검증 (쓰기 없음)
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.brief_common import ASSET_RE, js_literal, stamp_index as _stamp_index  # noqa: E402
from countries import BY_NAME, NAMES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES = ['국제·외교', '정책·규제', '경제동향', '산업동향', '대외교역', '에너지']
MIN_TOP = 3
MAX_ITEMS_PER_COUNTRY = 2


def require(cond, msg):
    if not cond:
        raise ValueError(msg)


def string(v, path, allow_empty=False):
    require(isinstance(v, str), f'{path}: 문자열이어야 합니다.')
    if not allow_empty:
        require(bool(v.strip()), f'{path}: 비어 있으면 안 됩니다.')


def ymd(v, path):
    string(v, path)
    try:
        require(date.fromisoformat(v).isoformat() == v, f'{path}: YYYY-MM-DD')
    except ValueError:
        raise ValueError(f'{path}: 유효한 YYYY-MM-DD 날짜여야 합니다.') from None


def url(v, path):
    if v in (None, ''):
        return
    string(v, path)
    p = urlparse(v)
    require(p.scheme in ('http', 'https') and bool(p.netloc), f'{path}: http(s) URL이어야 합니다.')
    require('utm_source=' not in v, f'{path}: utm_source 파라미터를 제거해야 합니다.')


def source(b, path, need_url=False):
    require(isinstance(b, dict), f'{path}: 객체여야 합니다.')
    if need_url:
        require(bool(b.get('url')), f'{path}.url: 출처 URL 필수(날조 금지)')
    if b.get('url'):
        url(b['url'], path + '.url')
        string(b.get('source'), path + '.source (url이 있으면 매체명 필수)')
    url(b.get('altUrl'), path + '.altUrl')
    if b.get('altUrl'):
        require(bool(b.get('url')), f'{path}: altUrl은 url과 함께만 사용합니다.')
    if b.get('date'):
        ymd(b['date'], path + '.date')


def validate(r):
    require(isinstance(r, dict), 'report: 객체여야 합니다.')
    ymd(r.get('date'), 'date')
    string(r.get('generatedAt'), 'generatedAt')
    try:
        datetime.fromisoformat(r['generatedAt'].replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('generatedAt: ISO 8601 형식이어야 합니다.') from None
    string(r.get('coverage'), 'coverage')
    if 'lead' in r:
        string(r['lead'], 'lead')
    tops = r.get('topIssues')
    require(isinstance(tops, list) and len(tops) >= MIN_TOP, f'topIssues: {MIN_TOP}개 이상 필요합니다.')
    for i, t in enumerate(tops):
        string(t.get('text') if isinstance(t, dict) else None, f'topIssues[{i}].text')
        source(t, f'topIssues[{i}]', need_url=True)
        cs = t.get('countries', [])
        require(isinstance(cs, list) and all(c in BY_NAME for c in cs), f'topIssues[{i}].countries: 대상 국가명만')
    news = r.get('countryNews')
    require(isinstance(news, list), 'countryNews: 배열이어야 합니다.')
    seen = []
    for i, cn in enumerate(news):
        p = f'countryNews[{i}]'
        require(isinstance(cn, dict) and cn.get('country') in BY_NAME, f'{p}.country: 대상 국가명({len(NAMES)}개국)만 허용')
        require(cn['country'] not in seen, f'{p}.country: 중복 {cn["country"]}')
        seen.append(cn['country'])
        items = cn.get('items')
        require(isinstance(items, list) and 1 <= len(items) <= MAX_ITEMS_PER_COUNTRY, f'{p}.items: 1~{MAX_ITEMS_PER_COUNTRY}개')
        for j, it in enumerate(items):
            q = f'{p}.items[{j}]'
            require(isinstance(it, dict), f'{q}: 객체')
            string(it.get('title'), q + '.title')
            require(it.get('category', '') in CATEGORIES + [''], f'{q}.category: {CATEGORIES} 중 하나')
            require(isinstance(it.get('korea', False), bool), f'{q}.korea: true/false')
            bs = it.get('bullets')
            require(isinstance(bs, list) and bs, f'{q}.bullets: 1개 이상')
            for k, b in enumerate(bs):
                string(b.get('text') if isinstance(b, dict) else None, f'{q}.bullets[{k}].text')
                source(b, f'{q}.bullets[{k}]')
            srcs = it.get('sources', [])
            require(isinstance(srcs, list), f'{q}.sources: 배열')
            for k, s in enumerate(srcs):
                source(s, f'{q}.sources[{k}]', need_url=True)
            require(any(b.get('url') for b in bs) or srcs, f'{q}: 출처 URL 1개 이상 필요(날조 금지)')
    require(seen == sorted(seen, key=NAMES.index), 'countryNews: 국가 순서는 countries.py 순서')
    notes = r.get('notes', [])
    require(isinstance(notes, list) and all(isinstance(n, str) for n in notes), 'notes: 문자열 배열')
    return r


def stamp_index(version=None):
    """index.html의 CSS·JS·data/*.js 경로에 ?v=<버전>을 붙여 브라우저 캐시를 무효화한다(게시 때마다 호출)."""
    return _stamp_index(ROOT, version, asset_re=ASSET_RE)


def main(argv):
    try:
        if argv[:1] == ['--check']:
            validate(json.loads(Path(argv[1]).read_text(encoding='utf-8')))
            print('검증 통과:', argv[1])
            return 0
        r = validate(json.loads((ROOT / 'data/report.json').read_text(encoding='utf-8')))
        (ROOT / 'data/report.js').write_text('window.REPORT_DATA = ' + js_literal(r) + ';\n', encoding='utf-8')
        print('data/report.js 작성:', r['date'], '/ index.html 캐시 버전:', stamp_index())
        return 0
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError) as e:
        print('검증 실패:', e, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
