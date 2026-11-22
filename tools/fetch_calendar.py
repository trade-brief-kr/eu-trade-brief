#!/usr/bin/env python3
"""공식 공개 일정만 수집. 주간(월요일), 일일 뉴스 런과 별개. 인증키 불필요.

날짜만 공표한 일정은 공표일 유지, 시간대가 명시된 ICS는 KST로 변환.
--source-cache DIR: 네트워크 실패 시 manifest.json에 URL·조회일이 기록된
공식 페이지 텍스트/ICS 캐시만 허용. 캐시 사용도 부분 실패(종료 코드 3).
0: 전 출처 성공, 3: 부분 실패, 1: 일정 0개/검증 실패.
"""
import argparse
import html
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlparse
from zoneinfo import ZoneInfo

from countries import NAMES
from fetch_country_stats import KST, ROOT, http_get

SOURCES = [
    ('ecb', 'ECB', 'EU', 'https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html'),
    ('eurostat', 'Eurostat', 'EU', 'https://ec.europa.eu/eurostat/news/release-calendar'),
    ('boe', 'BoE', '영국', 'https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates'),
    ('snb', 'SNB', '스위스', 'https://www.snb.ch/en/services-events/digital-services/event-schedule'),
    ('riksbank', 'Riksbank', '스웨덴', 'https://www.riksbank.se/en-gb/press-and-published/calendar/'),
    ('norges', 'Norges Bank', '노르웨이', 'https://www.norges-bank.no/en/topics/Monetary-policy/Monetary-policy-meetings/'),
    ('nbp', 'NBP', '폴란드', 'https://nbp.pl/en/monetary-policy/monetary-policy-council/schedule-of-mpc-meetings/'),
    ('cnb', 'CNB', '체코', 'https://www.cnb.cz/en/monetary-policy/bank-board-decisions/'),
    ('mnb', 'MNB', '헝가리', 'https://www.mnb.hu/en/monetary-policy/the-monetary-council'),
    ('consilium', 'EU 이사회', 'EU', 'https://www.consilium.europa.eu/en/meetings/calendar/'),
]
EUROSTAT_INDICATORS = 'https://ec.europa.eu/eurostat/news/euro-indicators/release-calendar'
# The subscription page publishes category 2 as "Euro indicators release".
EUROSTAT_ICAL = 'https://ec.europa.eu/eurostat/o/calendars/eventsIcal?theme=0&category=2'
NBP_SCHEDULE_PL = 'https://nbp.pl/polityka-pieniezna/rada-polityki-pienieznej/harmonogram-rpp/'
IRISH_PRESIDENCY_API = 'https://irish-presidency.consilium.europa.eu/api/events/'
IRISH_PRESIDENCY_START = date(2026, 7, 1)
IRISH_PRESIDENCY_END = date(2026, 12, 31)
# Public filters on the presidency calendar for Council, Eurogroup, European Council and summits.
IRISH_COUNCIL_TYPES = (
    '271842c3-2535-4f5a-a049-bcdab2758865',
    '800bbdac-845d-492c-876b-8cf61e9b195a',
    '6b7901c5-1094-4713-add8-3364400eee98',
    'cffca3a4-ef72-4f31-8713-560fb82753fb',
)
MONTHS = {m.lower(): i for i, m in enumerate(('January','February','March','April','May','June','July','August','September','October','November','December'), 1)}
MONTHS.update({m[:3]: n for m, n in list(MONTHS.items())})
MONTHS.update(dict(zip(('stycznia','lutego','marca','kwietnia','maja','czerwca','lipca','sierpnia','września','października','listopada','grudnia'), range(1,13))))
MONTH = '|'.join(sorted(MONTHS, key=len, reverse=True))
DATE_RE = re.compile(rf'\b(\d{{1,2}})\s+({MONTH})\s+(20\d{{2}})\b', re.I)
CATEGORIES = {'통화정책','통계발표','EU회의','통상'}
COUNCILS = [
    ('foreign affairs council (trade)', 'EU 외교이사회(통상)', '통상'),
    ('economic and financial affairs council', 'EU 경제·재무이사회(ECOFIN)', 'EU회의'),
    ('special european council', '특별 유럽이사회', 'EU회의'),
    ('informal meeting of heads of state or government', 'EU 정상 비공식 회의', 'EU회의'),
    ('european council', '유럽이사회', 'EU회의'),
    ('euro summit', '유로 정상회의', 'EU회의'),
    ('eurogroup', '유로그룹 회의', 'EU회의'),
    ('competitiveness council', 'EU 경쟁력이사회', 'EU회의'),
    ('general affairs council', 'EU 일반이사회', 'EU회의'),
    ('transport, telecommunications and energy council', 'EU 교통·통신·에너지이사회', 'EU회의'),
    ('eu-uk summit', 'EU·영국 정상회의', 'EU회의'),
    ('eu-western balkans summit', 'EU·서부발칸 정상회의', 'EU회의'),
    ('foreign affairs council', 'EU 외교이사회', 'EU회의'),
]


class Page(HTMLParser):
    """외부 의존성 없이 본문 줄/표 행/공개 피드 링크 보존."""
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.parts, self.links, self.ignore = [], [], 0
        self.feed(raw)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style'):
            self.ignore += 1
        if tag in ('p','div','li','tr','dt','dd','h1','h2','h3','h4','br','article') and not self.ignore:
            self.parts.append('\n')
        if tag in ('td','th'):
            self.parts.append(' | ')
        for k in ('href', 'src', 'value', 'data-url'):
            if attrs.get(k) and (k == 'href' or re.search(r'ics|ical|calendar|rss', attrs[k], re.I)):
                self.links.append(attrs[k])

    def handle_endtag(self, tag):
        if tag in ('script','style'):
            self.ignore = max(0, self.ignore - 1)
        if tag in ('p','div','li','tr','dt','dd','h1','h2','h3','h4','article') and not self.ignore:
            self.parts.append('\n')

    def handle_data(self, text):
        if not self.ignore:
            self.parts.append(text)

    @property
    def text(self):
        return '\n'.join(re.sub(r'\s+', ' ', l).strip() for l in ''.join(self.parts).splitlines() if l.strip())


def text_page(raw):
    if re.search(r'<(?:html|div|body|table)\b', raw, re.I):
        p = Page(raw)
        return p.text, p.links
    return html.unescape(raw).replace('\xa0',' '), []


def day(d, m, y):
    return date(int(y), MONTHS[m.lower()], int(d)).isoformat()


def event(d, title, source, url, country, category='통화정책', note=None):
    e = dict(date=d, title=title, entity=source, country=country, category=category, source=source, url=url)
    if note:
        e['note'] = note
    return e


def official_url(base, link):
    candidate = urljoin(base, link)
    parsed = urlparse(candidate)
    return candidate if parsed.scheme == 'https' and parsed.netloc == urlparse(base).netloc else base


def calendar_date(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return dt.astimezone(KST).date() if dt.tzinfo else dt.date()


def parse_ics(raw, source, url, country):
    raw = re.sub(r'\r?\n[ \t]', '', raw)
    out = []
    for block in raw.split('BEGIN:VEVENT')[1:]:
        block = block.split('END:VEVENT')[0]
        fields = {}
        for line in block.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                fields[k] = v
        if fields.get('STATUS') == 'CANCELLED':
            continue
        startkey = next((k for k in fields if k.split(';')[0] == 'DTSTART'), '')
        value = fields.get(startkey, '')
        title = fields.get('SUMMARY', '').replace('\\,', ',').replace('\\n', ' ')
        if not value:
            continue
        if re.fullmatch(r'\d{8}', value):
            d = datetime.strptime(value, '%Y%m%d').date().isoformat()
        else:
            tz = re.search(r'TZID=([^;:]+)', startkey)
            if not value.endswith('Z') and not tz:
                continue  # no guessing the timezone of a floating time
            dt = datetime.strptime(value.rstrip('Z'), '%Y%m%dT%H%M%S')
            dt = dt.replace(tzinfo=ZoneInfo(tz[1].strip('"')) if tz else timezone.utc)
            d = dt.astimezone(KST).date().isoformat()
        translated = classify(source, title)
        if translated:
            label, cat = translated
            link = fields.get('URL') or url
            if source in ('EU 이사회', 'Eurostat'):
                link = official_url(url, link)
            out.append(event(d, label, source, link, country, cat))
    return out


def classify(source, title):
    t = title.lower()
    if source == 'Eurostat':
        if re.search(r'hicp|inflation|consumer price', t):
            return ('유로지역 HICP 물가 속보 발표' if 'flash' in t else '유로지역 HICP 물가 발표', '통계발표')
        if re.search(r'\bgdp\b|gross domestic product', t):
            indicator = 'GDP·고용' if 'employment' in t else 'GDP'
            return (f"EU·유로지역 {indicator}{' 속보' if 'flash' in t else ''} 발표", '통계발표')
        if 'unemployment' in t:
            return ('EU·유로지역 실업률 발표', '통계발표')
        for indicator, label in (
            ('industrial production', '산업생산'),
            ('industrial producer prices', '산업생산자물가'),
            ('international trade in goods', '상품무역'),
            ('retail trade', '소매판매'),
        ):
            if indicator in t:
                return (f'EU·유로지역 {label} 발표', '통계발표')
        return None
    if source == 'EU 이사회':
        return next(((label, cat) for token, label, cat in COUNCILS if token in t), None)
    if re.search(r'non.monetary|minutes|speech|discussion|press conference|introductory remarks', t):
        return None
    if re.search(r'monetary policy|policy rate decision|mpc summary|geldpolitische lagebeurteilung', t):
        return (f'{source} 통화정책 결정 발표' if re.search(r'publication|assessment|decision|summary', t) else f'{source} 통화정책 회의', '통화정책')
    return None


def parse_eurostat_ical(raw, name, country):
    if not raw.lstrip().startswith('BEGIN:VCALENDAR') or 'END:VCALENDAR' not in raw:
        raise ValueError('Eurostat iCalendar 응답 형식 오류')
    events = parse_ics(raw, name, EUROSTAT_INDICATORS, country)
    if not events:
        raise ValueError('Eurostat iCalendar 주요 지표 일정 없음')
    return events


def read_irish_events(obtain, attempts, events, name, country, start, end):
    params = {
        'StartDate': max(start, IRISH_PRESIDENCY_START),
        'EndDate': min(end, IRISH_PRESIDENCY_END),
        'Types': ','.join(IRISH_COUNCIL_TYPES),
    }
    seen = set()
    for page in range(1, 41):
        query = urlencode(dict(params, page=page))
        raw = obtain(f'{IRISH_PRESIDENCY_API}?{query}', attempts)
        if raw in seen:
            raise ValueError('의장국 일정 페이지가 반복됨')
        groups, found = parse_irish_events(raw, name, country)
        if not groups:
            return
        seen.add(raw)
        events.extend(found)
    raise ValueError('의장국 일정 페이지 한도 초과')


def parse_irish_events(raw, name, country):
    groups = json.loads(raw)
    if not isinstance(groups, list):
        raise ValueError('의장국 일정 JSON 응답 형식 오류')
    events = []
    for group in groups:
        d = calendar_date(group['date']).isoformat()
        for item in group['events']:
            translated = classify(name, item['title'])
            if translated:
                label, cat = translated
                link = official_url(IRISH_PRESIDENCY_API, item['url'])
                events.append(event(d, label, name, link, country, cat))
    return groups, events


def parse_nbp_schedule(raw, name, url, country):
    text, _ = text_page(raw)
    year = None
    pending = {}
    # The PL/EN timetables put the year in a heading and the dates in the rows.
    month = dict(zip(
        ('styczeń', 'luty', 'marzec', 'kwiecień', 'maj', 'czerwiec', 'lipiec',
         'sierpień', 'wrzesień', 'październik', 'listopad', 'grudzień'), range(1, 13)
    ))
    month.update(MONTHS)
    month_pattern = '|'.join(sorted(month, key=len, reverse=True))
    dates = re.compile(
        rf'(?<![\d./])(?:(\d{{1,2}})\s*[-–—]\s*)?(\d{{1,2}})'
        rf'(?:\s+({month_pattern})\b|[./](\d{{1,2}})(?!\d))'
        rf'(?:[\s./]+(20\d{{2}})\b)?', re.I
    )
    month_row = re.compile(
        rf'^\s*\|?\s*({month_pattern})\s*\|\s*(\d{{1,2}})(?!\d)'
        rf'(?:\s*[-–—]\s*(\d{{1,2}})(?!\d))?',
        re.I
    )
    for line in text.splitlines():
        line = line.strip(' #*')
        heading = re.search(r'\b(20\d{2})\b', line)
        if re.search(r'schedule|harmonogram|terminy', line, re.I):
            if re.search(r'minutes|dyskusji|publikacji|publication', line, re.I):
                year = None
                continue
            if heading and re.search(r'MPC|RPP|meeting|posiedze|monetary policy', line, re.I):
                year = int(heading[1])
        elif re.fullmatch(r'(?:rok\s+)?20\d{2}(?:\s*r\.?)?', line, re.I):
            year = int(heading[1])
        if year is None:
            continue
        replacement = re.search(r'\b(?:przeniesion\w*|rescheduled|changed)\b', line, re.I)
        if replacement:
            line = line[replacement.end():]
        row = month_row.match(line)
        if row and (row.end() == len(line) or line[row.end()] not in './'):
            first, last = int(row[2]), int(row[3] or row[2])
            pending[year, month[row[1].lower()]] = (first, last)
            continue
        for match in dates.finditer(line):
            first, last = int(match[1] or match[2]), int(match[2])
            number = month[match[3].lower()] if match[3] else int(match[4])
            y = int(match[5]) if match[5] else year
            if 1 <= first <= last <= 31 and 1 <= number <= 12:
                pending[y, number] = first, last
    if not pending:
        raise ValueError('NBP 공식 회의 일정표를 찾지 못함')
    return [
        event(date(y, m, d).isoformat(), f'{name} 통화정책 회의', name, url, country)
        for (y, m), (first, last) in pending.items()
        for d in range(first, last + 1)
    ]


def parse_release_schedule(raw, url):
    """Eurostat 발표문에 명시한 차기 발표일만. 보도일을 일정으로 쓰지 않음."""
    text, _ = text_page(raw)
    is_gdp = bool(re.search(r'#?\s*GDP (?:up|down|stable)', text, re.I))
    is_hicp = bool(re.search(r'annual inflation|HICP', text, re.I))
    if not (is_gdp or is_hicp):
        return []
    out = []
    contexts = re.findall(r'(?:[^.\n]*scheduled for[^.\n]*|[^.\n]*will be released on[^.\n]*)',text,re.I)
    for context in contexts:
        for i, m in enumerate(DATE_RE.finditer(context)):
            label = ('EU·유로지역 GDP·고용 속보 발표' if i == 0 and 'flash' in context.lower() else 'EU·유로지역 GDP·고용 발표') if is_gdp else '유로지역 HICP 물가 발표'
            out.append(event(day(m[1],m[2],m[3]),label,'Eurostat',url,'EU','통계발표'))
    # HICP flash release explicitly identifies its next flash date in the header.
    if is_hicp and re.search(r'Flash estimate', text, re.I):
        m = re.search(r'Next release:\s*(' + DATE_RE.pattern + ')',text,re.I)
        if m:
            d = DATE_RE.search(m[1])
            out.append(event(day(d[1],d[2],d[3]),'유로지역 HICP 물가 속보 발표','Eurostat',url,'EU','통계발표'))
    # A release may repeat a date in both its summary and detailed timetable.
    by_date = {}
    for e in out:
        old = by_date.get(e['date'])
        if not old or '속보' in e['title']:
            by_date[e['date']] = e
    return list(by_date.values())


def parse_page(ident, raw, source, url, country):
    if 'BEGIN:VCALENDAR' in raw:
        return parse_ics(raw, source, url, country)
    text, _ = text_page(raw)
    text = text.replace('\xa0',' ')
    out = []
    if ident == 'ecb':
        for m in re.finditer(r'(\d{2})/(\d{2})/(20\d{2})\s*\n([^\n]+)', text):
            if 'monetary policy meeting' in m[4].lower() and 'non-monetary' not in m[4].lower():
                out.append(event(date(int(m[3]),int(m[2]),int(m[1])).isoformat(), 'ECB 통화정책 회의' + ('·결정 발표' if 'Day 2' in m[4] else ''), source,url,country))
        if 'monetary policy meeting' not in text:
            raise ValueError('ECB 일정 구조 변경')
    elif ident in ('boe','cnb','mnb'):
        if ident == 'boe':
            sections = re.findall(r'(20\d{2}) confirmed dates(.*?)(?=20\d{2} confirmed dates|Monetary Policy Committee Reports|$)', text, re.S)
        elif ident == 'cnb':
            sections = re.findall(r'Bank Board meetings on monetary policy in (20\d{2})(.*?)(?=Board decision|CNB Board decisions|$)', text, re.S)
        else:
            sections = re.findall(r"Monetary Council.s meetings \((20\d{2})\)(.*?)(?=\n(?:2\.|II\.|3\.|III\.)|Monetary Council.s meetings|$)", text, re.S)
        if not sections:
            raise ValueError('정책회의 연도/표를 찾지 못함')
        for year, section in sections:
            pattern = rf'(\d{{1,2}})\s+({MONTH})' + (r'\s*\(P\)' if ident == 'mnb' else '')
            for m in re.finditer(pattern, section, re.I):
                out.append(event(day(m[1],m[2],year),f'{source} 통화정책 결정 발표' if ident == 'boe' else f'{source} 통화정책 회의',source,url,country))
    elif ident == 'snb':
        for m in re.finditer(r'(\d{2})\.(\d{2})\.(20\d{2})\s+(\d{2}:\d{2})\s+([^\n]+)', text):
            if 'monetary policy assessment' in m[5].lower() and 'press release' in m[5].lower():
                dt = datetime.strptime(f'{m[3]}-{m[2]}-{m[1]} {m[4]}','%Y-%m-%d %H:%M').replace(tzinfo=ZoneInfo('Europe/Zurich'))
                out.append(event(dt.astimezone(KST).date().isoformat(),'SNB 통화정책 평가·결정 발표',source,url,country))
        if 'Monetary policy assessment' not in text:
            raise ValueError('SNB 정책 일정 없음')
    elif ident in ('riksbank','norges','consilium'):
        # Date headings define event blocks; unrelated footer/news dates are excluded.
        if ident == 'consilium':
            text = text.split('Meeting calendar', 1)[-1].split('About the secretariat',1)[0]
        if ident == 'riksbank':
            text = text.split('Calendar 20',1)[-1].split('Close menu Close menu',1)[0]
        matches = list(DATE_RE.finditer(text))
        for i, m in enumerate(matches):
            after = text[m.end():matches[i+1].start() if i+1 < len(matches) else m.end()+450]
            segment = after
            if ident == 'riksbank':
                first = next((l.strip(' *#') for l in after.splitlines() if l.strip(' *#')), '')
                if not re.match(r'Monetary policy meeting:|Publication of monetary policy decision', first, re.I):
                    continue
                segment = first
            translated = classify(source, segment)
            if translated:
                label, cat = translated
                # Council may have several relevant meetings under one date heading.
                labels = [translated]
                if ident == 'consilium':
                    labels = []
                    for line in after.splitlines():
                        hit = classify(source,line)
                        if hit and hit not in labels:
                            labels.append(hit)
                for label, cat in labels:
                    out.append(event(day(m[1],m[2],m[3]),label,source,url,country,cat))
        if not matches:
            raise ValueError('일정 날짜 없음(동적 페이지/구조 변경 가능)')
    return out


def validate(doc):
    for k in ('asOf','start','end'):
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', doc[k]) or date.fromisoformat(doc[k]).isoformat() != doc[k]:
            raise ValueError(f'{k}: YYYY-MM-DD')
    for e in doc['events']:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', e['date']) or date.fromisoformat(e['date']).isoformat() != e['date']:
            raise ValueError('일정 날짜 오류')
        if not doc['start'] <= e['date'] <= doc['end']:
            raise ValueError('수록 기간 밖 일정')
        u = urlparse(e['url'])
        if u.scheme not in ('http','https') or not u.netloc:
            raise ValueError('출처 http(s) URL 필수')
        if e['country'] not in ['EU', *NAMES] or e['category'] not in CATEGORIES:
            raise ValueError('국가/카테고리 오류')
        if not all(isinstance(e.get(k), str) and e[k].strip() for k in ('title','source','entity')):
            raise ValueError('제목·출처·기관 필수')
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--as-of', type=date.fromisoformat, help='재현용 KST 기준일; 기본 오늘')
    ap.add_argument('--source-cache', type=Path)
    ap.add_argument('--out', type=Path, help='지정한 경로에 JSON만 저장')
    args = ap.parse_args(argv)
    now = datetime.now(KST)
    start = args.as_of or now.date()
    end = start + timedelta(days=35)
    manifest = {}
    if args.source_cache:
        manifest = json.loads((args.source_cache / 'manifest.json').read_text(encoding='utf-8'))
    doc = dict(generatedAt=now.isoformat(timespec='seconds'),asOf=start.isoformat(),start=start.isoformat(),end=end.isoformat(),sources=[],status={},events=[])
    try:
        previous = json.loads((ROOT / 'data/calendar.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        previous = {}

    def obtain(url, attempts):
        try:
            raw = http_get(url, timeout=25, retries=1).decode('utf-8-sig')
            if len(raw) < 4096 and '/_Incapsula_Resource' in raw:
                raise ValueError('공개 일정 대신 접근 제한 페이지 응답')
            attempts.append({'url':url,'status':'ok'})
            return raw
        except Exception as exc:
            attempts.append({'url':url,'status':f'실패({exc})'})
            entry = manifest.get(url)
            if entry:
                # Explicit recorded acquisition date; do not relabel as a fresh HTTP fetch.
                date.fromisoformat(entry['asOf'])
                if (start - date.fromisoformat(entry['asOf'])).days not in range(0,8):
                    raise ValueError('공식 페이지 캐시 7일 경과') from exc
                path = (args.source_cache / entry['file']).resolve()
                if args.source_cache.resolve() not in path.parents:
                    raise ValueError('캐시 경로 오류') from exc
                attempts.append({'url':url,'status':f'공식 페이지 텍스트 캐시 사용({entry["asOf"]})'})
                return path.read_text(encoding='utf-8')
            raise

    for ident, name, country, url in SOURCES:
        source = dict(id=ident,name=name,url=url)
        doc['sources'].append(source)
        attempts, events, errors = [], [], []
        urls = [url]
        if ident == 'consilium':
            urls += [url+'?page=2']
        if ident == 'eurostat':
            urls = [EUROSTAT_ICAL, 'https://ec.europa.eu/eurostat/news/euro-indicators']
            urls += [u for u in manifest if u.startswith('https://ec.europa.eu/eurostat/')
                     and '/products-euro-indicators/w/' in u]
        if ident == 'nbp':
            urls = [NBP_SCHEDULE_PL, url]
        if ident == 'norges':
            urls += ['https://www.norges-bank.no/en/news-events/calendar/']
        parsed = False
        for target in urls:
            try:
                raw = obtain(target, attempts)
                if ident == 'eurostat':
                    if target == EUROSTAT_ICAL:
                        events.extend(parse_eurostat_ical(raw, name, country))
                        parsed = True
                        if any(doc['start'] <= e['date'] <= doc['end'] for e in events):
                            break
                        continue
                    if '/products-euro-indicators/w/' in target:
                        found = parse_release_schedule(raw,target)
                        events.extend(found)
                        parsed = parsed or bool(found)
                        continue
                    _, links = text_page(raw)
                    releases = list(dict.fromkeys(urljoin(target,l) for l in links if '/products-euro-indicators/w/2-' in l))[:8]
                    for release in releases:
                        if release not in urls and urlparse(release).hostname == 'ec.europa.eu':
                            urls.append(release)
                    continue
                if ident == 'nbp':
                    events.extend(parse_nbp_schedule(raw, name, target, country))
                    parsed = True
                    break
                _, links = text_page(raw)
                # Prefer published .ics/iCalendar links when exposed by the official page.
                feeds = [urljoin(target, l) for l in links if re.search(r'\.ics(?:\?|$)|icalendar|[?&]format=ics', l, re.I)]
                for feed in list(dict.fromkeys(feeds))[:60]:
                    if urlparse(feed).hostname != urlparse(url).hostname:
                        continue
                    try:
                        events.extend(parse_ics(obtain(feed,attempts),name,feed,country))
                        parsed = True
                    except Exception as exc:
                        errors.append(f'ICS: {exc}')
                if '<rss' in raw or '<feed' in raw:
                    # News timestamps are not meeting dates; never infer deadlines from RSS publication dates.
                    continue
                found = parse_page(ident,raw,name,target,country)
                events.extend(found)
                parsed = True
            except Exception as exc:
                errors.append(str(exc))
        council_partial = ident == 'consilium' and (not parsed or bool(errors) or not events)
        if council_partial and start <= IRISH_PRESIDENCY_END and end >= IRISH_PRESIDENCY_START:
            try:
                read_irish_events(obtain, attempts, events, name, country, start, end)
                parsed = True
            except Exception as exc:
                errors.append(str(exc))
        if not parsed or council_partial:
            retained = [e for e in previous.get('events',[]) if e.get('source') == name]
            known = {(e['date'], e['title']) for e in events}
            for e in retained:
                if (e['date'], e['title']) not in known:
                    events.append(dict(e, note='수집 실패로 직전 확인 일정 유지. 원문 재확인 권고.'))
        filtered = [e for e in events if doc['start'] <= e['date'] <= doc['end']]
        doc['events'].extend(filtered)
        failed = not parsed or bool(errors) or council_partial or any(a['status'].startswith('실패') for a in attempts)
        count = len(filtered)
        doc['status'][ident] = dict(ok=not failed, count=count, message=(f'부분 실패 · 확인 일정 {count}건' if failed else f'수집 성공 · 기간 내 {count}건'), attempts=attempts)
        if errors:
            doc['status'][ident]['errors'] = list(dict.fromkeys(errors))
        print(f'{name}: {doc["status"][ident]["message"]}')
    unique = {(e['date'], e['title'], e['entity'], e['country']):e for e in doc['events']}
    doc['events'] = sorted(unique.values(), key=lambda e:(e['date'],e['country'],e['title']))
    validate(doc)
    payload = json.dumps(doc, ensure_ascii=False, indent=2)
    if not doc['events']:
        # Keep an existing nonempty file intact on total acquisition failure.
        print('실패: 확인된 일정 0개. 기존 파일 유지.',file=sys.stderr)
        return 1
    (args.out or ROOT / 'data/calendar.json').write_text(payload+'\n',encoding='utf-8')
    if args.out is None:
        (ROOT / 'data/calendar.js').write_text('window.CALENDAR_DATA = '+payload+';\n',encoding='utf-8')
    print(f'일정 작성: {len(doc["events"])}건 ({start} ~ {end}, 포함)')
    return 0 if all(s['ok'] for s in doc['status'].values()) else 3


if __name__ == '__main__':
    sys.exit(main())
