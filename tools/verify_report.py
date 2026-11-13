#!/usr/bin/env python3
"""Codex가 만든 유럽 통상 브리프를 게시 전에 후처리·검증한다 (항목은 지우기만, 만들지 않음).

사용법: python3 tools/verify_report.py --input RAW.json --output REPORT.json [--log LOG.json]
                                      [--check-links] [--now ISO] [--window-hours 30]
처리:
  1. JSON 파싱, date == 오늘(KST) 필수.
  2. 모든 URL에서 utm_* 제거. altUrl만 있으면 url로 올림.
  3. publishedAt 기간 확인: 기본 30시간(24h+여유), text가 "[누락 보완"으로 시작하면 96시간. 기간 밖·형식 오류 → 삭제.
     통과하면 publishedAt은 "date"(게시 현지 날짜)로 바꿈. "[누락 보완…]" 표기는 게시본에서 제거.
  4. url은 있는데 source 없음 → 삭제. 출처 URL이 하나도 없는 Top Issue·국가 항목 → 삭제.
  5. 국가명 정규화(countries.py), 대상 외 국가 → 삭제, 중복 국가 병합, 국가당 항목 최대 2개(초과분 삭제), 국가 순서 정렬.
  6. headline·followup 등 스키마 밖 필드 제거. category가 목록 밖이면 "".
  7. 링크 curl 재검증은 기본 OFF (Codex 검증 신뢰). --check-links 시 404/410/DNS 실패만 삭제.
  8. build_report_js.validate (EU Top Issues 3개 이상 등).
품질 경고(Top Issues 5개 미만, 보도동향 국가 수 적음, 120자 넘는 bullet)는 로그·stderr에만.
종료 코드: 0 성공, 12 읽기/JSON 오류, 13 검증 실패. 실패 시 --output은 쓰지 않고 *.rejected.json 남김.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_report_js import CATEGORIES, MAX_ITEMS_PER_COUNTRY, validate  # noqa: E402
from countries import NAMES, canon  # noqa: E402

KST = timezone(timedelta(hours=9))
MARK = re.compile(r'^\s*\[누락 보완[^\]]*\]\s*')


def clean_url(u):
    if not isinstance(u, str) or not u.strip():
        return u
    p = urlparse(u.strip())
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.lower().startswith('utm_')]
    return urlunparse(p._replace(query=urlencode(q)))


def parse_ts(v):
    try:
        t = datetime.fromisoformat(str(v).replace('Z', '+00:00'))
        return t if t.tzinfo else None
    except ValueError:
        return None


def link_dead(u):
    try:
        out = subprocess.run(['curl', '-sS', '-o', '/dev/null', '-L', '--max-time', '20', '-A', 'Mozilla/5.0',
                              '-w', '%{http_code}', u], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return False
    code = out.stdout.strip()
    return code in ('404', '410') or (code == '000' and 'resolve' in out.stderr.lower())


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--log')
    ap.add_argument('--check-links', action='store_true')
    ap.add_argument('--now')
    ap.add_argument('--window-hours', type=float, default=30.0)
    a = ap.parse_args(argv)
    now = parse_ts(a.now) if a.now else datetime.now(KST)
    today = now.astimezone(KST).date().isoformat()
    log = {'removed': [], 'warnings': [], 'today': today}

    def finish(code, msg, report=None):
        log['result'] = msg
        if a.log:
            Path(a.log).write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
        if code == 0:
            Path(a.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print('검증 통과:', msg)
        else:
            if report is not None:
                Path(a.output + '.rejected.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            print('검증 실패:', msg, file=sys.stderr)
        for w in log['warnings']:
            print('품질 경고:', w, file=sys.stderr)
        return code

    try:
        r = json.loads(Path(a.input).read_text(encoding='utf-8'))
        assert isinstance(r, dict)
    except Exception as e:  # noqa: BLE001
        return finish(12, f'JSON 읽기 실패: {e}')
    if r.get('date') != today:
        return finish(13, f"date {r.get('date')} != 오늘 {today}", r)

    def check_src(b, where, need_text=True):
        """정상이면 정리된 dict, 버려야 하면 None."""
        if not isinstance(b, dict):
            return None
        if need_text and not str(b.get('text', '')).strip():
            return None
        for k in ('url', 'altUrl'):
            if b.get(k):
                b[k] = clean_url(b[k])
            else:
                b.pop(k, None)
        if b.get('altUrl') and not b.get('url'):
            b['url'] = b.pop('altUrl')
        if b.get('url') and not str(b.get('source', '')).strip():
            log['removed'].append({'where': where, 'reason': 'source 없음'})
            return None
        pub = b.pop('publishedAt', None)
        if pub:
            t = parse_ts(pub)
            hours = 96 if str(b.get('text', '')).lstrip().startswith('[누락 보완') else a.window_hours
            if t is None or t < now - timedelta(hours=hours) or t > now + timedelta(hours=2):
                log['removed'].append({'where': where, 'reason': f'기간 밖/형식 오류 publishedAt={pub}', 'text': str(b.get('text', ''))[:60]})
                return None
            b['date'] = t.date().isoformat()
        elif b.get('url') and not b.get('date'):
            log['warnings'].append(f'{where}: publishedAt 없는 출처')
        if 'text' in b:
            b['text'] = MARK.sub('', b['text'])
            if len(b['text']) > 160:
                log['warnings'].append(f"{where}: {len(b['text'])}자(간결 형식 초과)")
        if a.check_links and b.get('url') and link_dead(b['url']):
            log['removed'].append({'where': where, 'reason': '링크 404/410/DNS', 'url': b['url']})
            return None
        return b

    tops = []
    for i, t in enumerate(r.get('topIssues') or []):
        t = check_src(t, f'top[{i}]')
        if not t:
            continue
        if not t.get('url'):
            log['removed'].append({'where': f'top[{i}]', 'reason': '출처 URL 없음'})
            continue
        t['countries'] = [c for c in (canon(x) for x in t.get('countries', []) or []) if c]
        tops.append({k: t[k] for k in ('text', 'source', 'url', 'altUrl', 'date', 'countries') if k in t})

    merged = {}
    for i, cn in enumerate(r.get('countryNews') or []):
        if not isinstance(cn, dict):
            continue
        c = canon(cn.get('country'))
        if not c:
            log['removed'].append({'where': f'countryNews[{i}]', 'reason': f"대상 외 국가 {cn.get('country')}"})
            continue
        for j, it in enumerate(cn.get('items') or []):
            if not isinstance(it, dict):
                continue
            where = f'{c}:{it.get("title", "")}'
            bullets = [b for b in (check_src(b, where) for b in it.get('bullets') or []) if b]
            srcs = [s for s in (check_src(dict(s, text=s.get('text') or '-'), where) for s in it.get('sources') or []
                                if isinstance(s, dict)) if s and s.get('url')]
            for s in srcs:
                s.pop('text', None)
            if not bullets or not str(it.get('title', '')).strip():
                continue
            if not any(b.get('url') for b in bullets) and not srcs:
                log['removed'].append({'where': where, 'reason': '출처 URL 없는 항목'})
                continue
            cat = it.get('category', '')
            out = {'title': it['title'].strip(), 'category': cat if cat in CATEGORIES else '',
                   'korea': bool(it.get('korea', False)), 'bullets': bullets}
            if srcs:
                out['sources'] = srcs
            merged.setdefault(c, []).append(out)
    news = []
    for c in NAMES:
        items = merged.get(c)
        if not items:
            continue
        if len(items) > MAX_ITEMS_PER_COUNTRY:
            log['removed'].append({'where': c, 'reason': f'국가당 {MAX_ITEMS_PER_COUNTRY}개 초과분 삭제', 'n': len(items)})
            items = items[:MAX_ITEMS_PER_COUNTRY]
        news.append({'country': c, 'items': items})

    out = {'date': r['date'], 'generatedAt': r.get('generatedAt') or now.isoformat(timespec='seconds'),
           'coverage': r.get('coverage') or '최근 24시간 보도 중심', 'topIssues': tops, 'countryNews': news,
           'notes': [n for n in r.get('notes', []) if isinstance(n, str)]}
    if isinstance(r.get('lead'), str) and r['lead'].strip():
        out['lead'] = r['lead'].strip()
    if len(tops) < 5:
        log['warnings'].append(f'EU Top Issues {len(tops)}개(목표 5개)')
    if len(news) < 10:
        log['warnings'].append(f'일일보도동향 국가 {len(news)}개(목표 10개 이상)')
    try:
        validate(out)
    except (ValueError, KeyError, TypeError) as e:
        return finish(13, str(e), out)
    n = sum(len(c['items']) for c in news)
    return finish(0, f"{out['date']} Top {len(tops)}건, 보도동향 {len(news)}개국 {n}건, 삭제 {len(log['removed'])}건", out)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
