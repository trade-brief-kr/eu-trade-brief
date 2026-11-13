# 유럽 통상 브리프

https://trade-brief-kr.github.io/eu-trade-brief/

유럽과 거래·협력하는 한국 독자를 위한 일일 통상 브리핑 정적 사이트입니다. 공개 보도와 공식 통계를 정리한 참고 자료이며 어떤 기관의 공식 자료도 아닙니다.

## 구성
- **일일 브리프**
  - ★ EU Top Issues: EU 차원(집행위·이사회·유럽의회·ECB·Eurostat, 통상·규제·제재) 주요 이슈 약 5건, 항상 상단 고정
  - ★ 일일보도동향: □ 국가별 주요 뉴스 1~2건(현지어 주요 매체·정부·통계청·중앙은행 발표 기반). 뉴스가 없는 국가는 생략
  - 날짜 이동, 보관본, 지난 보고서 키워드 검색, 텍스트 복사, 출처 원문 링크(유료·재게재본은 「재게재」 링크)
  - 「국가」 선택(브라우저에 저장): 선택 국가를 맨 위로 올리고 강조하며 다른 국가는 숨기지 않음
- **국가 정보**: 대상 42개국 주요 통계(명목 GDP, 1인당 GDP, 실질 성장률, 인구, 물가상승률, 실업률, 정책금리, 대한국 교역), 상세 카드의 인라인 SVG 추이, EU·유로지역 + 42개국의 2025 실적·2026–2027 성장·물가 전망표. 그룹 필터·정렬 적용.
- **주요 일정**: 향후 약 5주 공식 정책회의·주요 지표 발표·EU 회의. 국가 선택 시 EU + 해당 국가만, 전체 선택 시 전부 표시.
- 일일 브리프의 선택 필드 `lead`는 오늘 보고서 사실만으로 작성한 한 문장 요약(한국어·명사형·약 80–140자). 있으면 Top Issues 위와 복사 텍스트에 표시하며 이전 보고서도 그대로 지원.

## 대상 국가와 근거
KOTRA 유럽지역 무역관이 관할하는 국가 전체를 대상으로 합니다.
- 유럽지역 무역관 목록(24개 무역관·22개국): https://www.kotra.or.kr/subList/41000002020
- 무역관별 관할 국가: KOTRA 「해외무역관 관할지역표」('26.5.1. 기준) 「나. 유럽지역」 — https://www.kotra.or.kr/subList/20000005998 첨부 PDF
- 관할지역표의 주권국가 42개국을 모두 포함하였습니다. 해외 영토·자치령(세인트마틴, 건지섬·맨섬·저지섬, 지브롤터, 그린란드, 페로 제도, 올란드 제도)은
  별도 국가로 두지 않고 관할국 소식에 포함합니다. CIS 지역(러시아·우크라이나 등)은 별도 지역이므로 제외합니다.
- 관할 변경 시 `tools/countries.py` 한 곳만 고치면 조사 프롬프트·검증·통계에 반영됩니다.

| # | 국가 | 영문 | 관할 무역관 | 구분 |
|---|---|---|---|---|
| 1 | 독일 | Germany | 프랑크푸르트·함부르크·뮌헨 | EU·유로 |
| 2 | 프랑스 | France | 파리 | EU·유로 |
| 3 | 영국 | United Kingdom | 런던 | 비EU |
| 4 | 이탈리아 | Italy | 밀라노 | EU·유로 |
| 5 | 스페인 | Spain | 마드리드 | EU·유로 |
| 6 | 네덜란드 | Netherlands | 암스테르담 | EU·유로 |
| 7 | 폴란드 | Poland | 바르샤바 | EU |
| 8 | 벨기에 | Belgium | 브뤼셀 | EU·유로 |
| 9 | 스웨덴 | Sweden | 스톡홀름 | EU |
| 10 | 스위스 | Switzerland | 취리히 | 비EU |
| 11 | 오스트리아 | Austria | 빈 | EU·유로 |
| 12 | 체코 | Czechia | 프라하 | EU |
| 13 | 헝가리 | Hungary | 부다페스트 | EU |
| 14 | 슬로바키아 | Slovakia | 브라티슬라바 | EU·유로 |
| 15 | 루마니아 | Romania | 부쿠레슈티 | EU |
| 16 | 덴마크 | Denmark | 코펜하겐 | EU |
| 17 | 핀란드 | Finland | 헬싱키 | EU·유로 |
| 18 | 노르웨이 | Norway | 스톡홀름 | 비EU |
| 19 | 아일랜드 | Ireland | 런던 | EU·유로 |
| 20 | 포르투갈 | Portugal | 리스본 | EU·유로 |
| 21 | 그리스 | Greece | 아테네 | EU·유로 |
| 22 | 불가리아 | Bulgaria | 소피아 | EU·유로 |
| 23 | 크로아티아 | Croatia | 자그레브 | EU·유로 |
| 24 | 슬로베니아 | Slovenia | 자그레브 | EU·유로 |
| 25 | 세르비아 | Serbia | 베오그라드 | 비EU |
| 26 | 리투아니아 | Lithuania | 바르샤바 | EU·유로 |
| 27 | 라트비아 | Latvia | 스톡홀름 | EU·유로 |
| 28 | 에스토니아 | Estonia | 헬싱키 | EU·유로 |
| 29 | 룩셈부르크 | Luxembourg | 브뤼셀 | EU·유로 |
| 30 | 키프로스 | Cyprus | 아테네 | EU·유로 |
| 31 | 몰타 | Malta | 밀라노 | EU·유로 |
| 32 | 아이슬란드 | Iceland | 스톡홀름 | 비EU |
| 33 | 알바니아 | Albania | 아테네 | 비EU |
| 34 | 북마케도니아 | North Macedonia | 소피아 | 비EU |
| 35 | 보스니아-헤르체고비나 | Bosnia and Herzegovina | 자그레브 | 비EU |
| 36 | 몬테네그로 | Montenegro | 베오그라드 | 비EU |
| 37 | 코소보 | Kosovo | 베오그라드 | 비EU |
| 38 | 리히텐슈타인 | Liechtenstein | 취리히 | 비EU |
| 39 | 모나코 | Monaco | 파리 | 비EU |
| 40 | 안도라 | Andorra | 마드리드 | 비EU |
| 41 | 산마리노 | San Marino | 밀라노 | 비EU |
| 42 | 교황청 | Holy See (Vatican City) | 밀라노 | 비EU |

## 데이터·출처
- 뉴스: 웹 검색 기반 자동 조사(Codex CLI) 후 스크립트 검증(날짜·24시간 범위·출처 URL·국가명·스키마). 모든 항목에 원 매체 링크.
- 통계(월 1회 갱신, 인증키 없는 공식 공개 API, 값은 응답 그대로):
  - World Bank WDI (CC BY 4.0): 명목 GDP, 1인당 GDP, 실질 GDP 성장률, 인구, (Eurostat 미수록국) CPI·실업률 연간값
  - Eurostat: GDP 성장률(namq_10_gdp, 분기 전년동기비·계절/달력조정, 최대 12분기), HICP 물가상승률(prc_hicp_minr, 전년동월비), 실업률(une_rt_m, 계절조정), 월간 최대 24개. 분기 GDP 미수록 시 WB 연간 성장률. BIS 정책금리도 짧은 원 관측 시계열을 저장하며 보간하지 않음
  - BIS 중앙은행 정책금리(WS_CBPOL): 유로 사용국은 유로지역(ECB) 금리, 리히텐슈타인은 스위스 금리
  - UN Comtrade 공개 API: 한국 보고 기준 대상국별 수출·수입(연간·월간 최신). 모나코는 프랑스, 리히텐슈타인은 스위스 수치에 포함

- 성장·물가 전망: [AMECO 벌크 ZIP](https://ec.europa.eu/economy_finance/db_indicators/ameco/documents/ameco0.zip) 우선, [IMF WEO Datamapper](https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH) 보완(무료·무키, 식별 가능한 UA). 현재 AMECO 파일은 2026-06-02 / Spring 2026, 2027년까지이며 2026-11-13 기준 Autumn 2026은 아직 미게시.
  GDP `.1.1.0.0.OVGD`(PPS 제외)·물가 `.1.0.0.0.ZCPIH` 수준에서 전년비 계산, 소수 1자리. **AMECO 수준 계열로 전년비 계산. 공표 표와 끝자리 반올림이 다를 수 있음.** EU27·EA21 사용. AMECO 미수록 지표는 IMF NGDP_RPCH·PCPIPCH, EU·EURO 집계로 보완. 영국 등 IMF 물가는 CPI로 HICP와 정의 차이. IMF API에 판 정보가 없어 조회일만 표시. 지표별 출처·빈티지 명시, 미수록 소국은 자료 없음(현재 모나코·교황청).
- 일정: ECB·Eurostat·BoE·SNB·Riksbank·Norges Bank·NBP·CNB·MNB·Consilium 공식 페이지·공개 ICS. Consilium 403·동적 페이지·미공표 일정은 공백 가능, 시도와 부분 실패를 `status`로 공개. 날짜를 임의로 만들지 않음. 시간대 있는 ICS는 KST, 날짜만 공표한 일정은 현지 공표일 유지.

## 운영
매주 월요일(일일 게시 후 또는 별도) `python3 tools/fetch_calendar.py` 후 `stamp_index()` 실행 권고. 일정 수집은 일일 Codex 뉴스 런에 넣지 않습니다.
월간 통계는 `python3 tools/fetch_country_stats.py` → `python3 tools/fetch_outlook.py` 순서로 실행한 뒤 캐시 버전을 갱신합니다. 통계를 다시 받아도 기존 전망은 보존합니다.
```bash
python3 tools/fetch_calendar.py
python3 -c "import sys;sys.path.insert(0,'tools');from build_report_js import stamp_index;print(stamp_index())"
```
`tools/DAILY_UPDATE.md` 참고 (일일 조사·게시 / 월간 통계 갱신 절차 분리).

## 파일
- `index.html`, `assets/` — 화면
- `data/report.json(.js)` 최신 보고서, `data/archive/` 날짜별 보관본·색인, `feed.xml` RSS
- `data/country-stats.json(.js)` 국가 통계·전망, `data/calendar.json(.js)` 주요 일정
- `tools/countries.py` 대상 국가, `tools/research_prompt.md` 조사 기준, `tools/run_codex_research.sh` 조사 러너,
  `tools/verify_report.py` 후처리 검증, `tools/build_report_js.py` 스키마·캐시 버전, `tools/publish_daily.py` 게시, `tools/fetch_country_stats.py` 통계·시계열 수집, `tools/fetch_outlook.py` 전망 병합, `tools/fetch_calendar.py` 주간 일정 수집
