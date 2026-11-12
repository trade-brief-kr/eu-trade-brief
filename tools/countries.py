"""유럽 통상 브리프 대상 국가 목록 (공통 모듈).

근거: KOTRA 「해외무역관 관할지역표」('26.5.1. 기준, https://www.kotra.or.kr/subList/20000005998 첨부 PDF)의
「나. 유럽지역」에 적힌 주권국가 전체. 해외 영토·자치령(세인트마틴, 건지·맨·저지섬, 지브롤터, 그린란드, 페로 제도,
올란드 제도)은 별도 국가로 두지 않고 관할국 소식에 포함한다.
필드: (ISO2, ISO3, 한국어명, 영문명, 관할 무역관, EU 회원국, 유로 사용(통화정책=ECB), 중앙은행명, 중앙은행 URL)
순서: 경제 규모·한국과의 교역 규모를 고려한 화면 기본 순서.
"""

COUNTRIES = [
    ('DE', 'DEU', '독일', 'Germany', '프랑크푸르트·함부르크·뮌헨', True, True, '독일 연방은행', 'https://www.bundesbank.de/en'),
    ('FR', 'FRA', '프랑스', 'France', '파리', True, True, '프랑스 중앙은행', 'https://www.banque-france.fr/en'),
    ('GB', 'GBR', '영국', 'United Kingdom', '런던', False, False, '영란은행', 'https://www.bankofengland.co.uk/'),
    ('IT', 'ITA', '이탈리아', 'Italy', '밀라노', True, True, '이탈리아 중앙은행', 'https://www.bancaditalia.it/'),
    ('ES', 'ESP', '스페인', 'Spain', '마드리드', True, True, '스페인 중앙은행', 'https://www.bde.es/'),
    ('NL', 'NLD', '네덜란드', 'Netherlands', '암스테르담', True, True, '네덜란드 중앙은행', 'https://www.dnb.nl/en/'),
    ('PL', 'POL', '폴란드', 'Poland', '바르샤바', True, False, '폴란드 중앙은행', 'https://nbp.pl/en/'),
    ('BE', 'BEL', '벨기에', 'Belgium', '브뤼셀', True, True, '벨기에 중앙은행', 'https://www.nbb.be/en'),
    ('SE', 'SWE', '스웨덴', 'Sweden', '스톡홀름', True, False, '스웨덴 중앙은행', 'https://www.riksbank.se/en-gb/'),
    ('CH', 'CHE', '스위스', 'Switzerland', '취리히', False, False, '스위스 중앙은행', 'https://www.snb.ch/en/'),
    ('AT', 'AUT', '오스트리아', 'Austria', '빈', True, True, '오스트리아 중앙은행', 'https://www.oenb.at/en/'),
    ('CZ', 'CZE', '체코', 'Czechia', '프라하', True, False, '체코 중앙은행', 'https://www.cnb.cz/en/'),
    ('HU', 'HUN', '헝가리', 'Hungary', '부다페스트', True, False, '헝가리 중앙은행', 'https://www.mnb.hu/en'),
    ('SK', 'SVK', '슬로바키아', 'Slovakia', '브라티슬라바', True, True, '슬로바키아 중앙은행', 'https://nbs.sk/en/'),
    ('RO', 'ROU', '루마니아', 'Romania', '부쿠레슈티', True, False, '루마니아 중앙은행', 'https://www.bnr.ro/'),
    ('DK', 'DNK', '덴마크', 'Denmark', '코펜하겐', True, False, '덴마크 중앙은행', 'https://www.nationalbanken.dk/en'),
    ('FI', 'FIN', '핀란드', 'Finland', '헬싱키', True, True, '핀란드 중앙은행', 'https://www.suomenpankki.fi/en/'),
    ('NO', 'NOR', '노르웨이', 'Norway', '스톡홀름', False, False, '노르웨이 중앙은행', 'https://www.norges-bank.no/en/'),
    ('IE', 'IRL', '아일랜드', 'Ireland', '런던', True, True, '아일랜드 중앙은행', 'https://www.centralbank.ie/'),
    ('PT', 'PRT', '포르투갈', 'Portugal', '리스본', True, True, '포르투갈 중앙은행', 'https://www.bportugal.pt/en'),
    ('GR', 'GRC', '그리스', 'Greece', '아테네', True, True, '그리스 중앙은행', 'https://www.bankofgreece.gr/en'),
    ('BG', 'BGR', '불가리아', 'Bulgaria', '소피아', True, True, '불가리아 국립은행', 'https://www.bnb.bg/?toLang=_EN'),
    ('HR', 'HRV', '크로아티아', 'Croatia', '자그레브', True, True, '크로아티아 국립은행', 'https://www.hnb.hr/en/'),
    ('SI', 'SVN', '슬로베니아', 'Slovenia', '자그레브', True, True, '슬로베니아 중앙은행', 'https://www.bsi.si/en'),
    ('RS', 'SRB', '세르비아', 'Serbia', '베오그라드', False, False, '세르비아 국립은행', 'https://nbs.rs/en/'),
    ('LT', 'LTU', '리투아니아', 'Lithuania', '바르샤바', True, True, '리투아니아 중앙은행', 'https://www.lb.lt/en/'),
    ('LV', 'LVA', '라트비아', 'Latvia', '스톡홀름', True, True, '라트비아 중앙은행', 'https://www.bank.lv/en/'),
    ('EE', 'EST', '에스토니아', 'Estonia', '헬싱키', True, True, '에스토니아 중앙은행', 'https://www.eestipank.ee/en'),
    ('LU', 'LUX', '룩셈부르크', 'Luxembourg', '브뤼셀', True, True, '룩셈부르크 중앙은행', 'https://www.bcl.lu/en/'),
    ('CY', 'CYP', '키프로스', 'Cyprus', '아테네', True, True, '키프로스 중앙은행', 'https://www.centralbank.cy/en/'),
    ('MT', 'MLT', '몰타', 'Malta', '밀라노', True, True, '몰타 중앙은행', 'https://www.centralbankmalta.org/'),
    ('IS', 'ISL', '아이슬란드', 'Iceland', '스톡홀름', False, False, '아이슬란드 중앙은행', 'https://www.cb.is/'),
    ('AL', 'ALB', '알바니아', 'Albania', '아테네', False, False, '알바니아 중앙은행', 'https://www.bankofalbania.org/'),
    ('MK', 'MKD', '북마케도니아', 'North Macedonia', '소피아', False, False, '북마케도니아 국립은행', 'https://www.nbrm.mk/'),
    ('BA', 'BIH', '보스니아-헤르체고비나', 'Bosnia and Herzegovina', '자그레브', False, False, '보스니아-헤르체고비나 중앙은행', 'https://www.cbbh.ba/'),
    ('ME', 'MNE', '몬테네그로', 'Montenegro', '베오그라드', False, False, '몬테네그로 중앙은행', 'https://www.cbcg.me/en'),
    ('XK', 'XKX', '코소보', 'Kosovo', '베오그라드', False, False, '코소보 중앙은행', 'https://bqk-kos.org/'),
    ('LI', 'LIE', '리히텐슈타인', 'Liechtenstein', '취리히', False, False, '', ''),
    ('MC', 'MCO', '모나코', 'Monaco', '파리', False, False, '', ''),
    ('AD', 'AND', '안도라', 'Andorra', '마드리드', False, False, '', ''),
    ('SM', 'SMR', '산마리노', 'San Marino', '밀라노', False, False, '', ''),
    ('VA', 'VAT', '교황청', 'Holy See (Vatican City)', '밀라노', False, False, '', ''),
]

NAMES = [c[2] for c in COUNTRIES]
BY_NAME = {c[2]: c for c in COUNTRIES}
ALIASES = {'보스니아헤르체고비나': '보스니아-헤르체고비나', '보스니아': '보스니아-헤르체고비나', '마케도니아': '북마케도니아',
           '체코공화국': '체코', '사이프러스': '키프로스', '바티칸': '교황청', '그리스·키프로스': '그리스'}


def canon(name):
    n = str(name or '').strip()
    n = ALIASES.get(n, n)
    return n if n in BY_NAME else None
