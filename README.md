# 유럽 통상 브리프

https://trade-brief-kr.github.io/eu-trade-brief/

유럽과 거래·협력하는 한국 독자를 위한 일일 통상 브리핑 정적 사이트입니다. 공개 보도와 공식 통계를 정리한 참고 자료이며 어떤 기관의 공식 자료도 아닙니다.

## 구성
- **일일 브리프**
  - ★ EU Top Issues: EU 차원(집행위·이사회·유럽의회·ECB·Eurostat, 통상·규제·제재) 주요 이슈 약 5건, 항상 상단 고정
  - ★ 일일보도동향: □ 국가별 주요 뉴스 1~2건(현지어 주요 매체·정부·통계청·중앙은행 발표 기반). 뉴스가 없는 국가는 생략
  - 날짜 이동, 보관본, 지난 보고서 키워드 검색, 텍스트 복사, 출처 원문 링크(유료·재게재본은 「재게재」 링크)
  - 「국가」 선택(브라우저에 저장): 선택 국가를 맨 위로 올리고 강조하며 다른 국가는 숨기지 않음
- **국가 정보**: 대상 42개국 주요 통계(명목 GDP, 1인당 GDP, 실질 성장률, 인구, 물가상승률, 실업률, 정책금리, 대한국 교역)

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
  - Eurostat: HICP 물가상승률(prc_hicp_minr, 전년동월비), 실업률(une_rt_m, 계절조정)
  - BIS 중앙은행 정책금리(WS_CBPOL): 유로 사용국은 유로지역(ECB) 금리, 리히텐슈타인은 스위스 금리
  - UN Comtrade 공개 API: 한국 보고 기준 대상국별 수출·수입(연간·월간 최신). 모나코는 프랑스, 리히텐슈타인은 스위스 수치에 포함

## 운영
`tools/DAILY_UPDATE.md` 참고 (일일 조사·게시 / 월간 통계 갱신 절차 분리).

## 파일
- `index.html`, `assets/` — 화면
- `data/report.json(.js)` 최신 보고서, `data/archive/` 날짜별 보관본·색인, `feed.xml` RSS
- `data/country-stats.json(.js)` 국가 통계
- `tools/countries.py` 대상 국가, `tools/research_prompt.md` 조사 기준, `tools/run_codex_research.sh` 조사 러너,
  `tools/verify_report.py` 후처리 검증, `tools/build_report_js.py` 스키마·캐시 버전, `tools/publish_daily.py` 게시, `tools/fetch_country_stats.py` 통계 수집
