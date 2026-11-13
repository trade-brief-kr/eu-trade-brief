# 운영 절차

모든 명령은 저장소 루트(`/workspace/eu-trade-brief`)에서 실행. 시각은 KST.
뉴스 조사는 사람이 직접 하지 않고 반드시 `tools/run_codex_research.sh`(Codex CLI 웹검색, ChatGPT 로그인)로만 한다.

## 1. 일일 (매일, 예: 오전)
```bash
cd /workspace/eu-trade-brief
git pull --ff-only
bash tools/run_codex_research.sh            # Codex 조사 → 검증 → data/report.json (보통 10~30분, 최대 2400초)
python3 tools/publish_daily.py              # 보관본·색인·report.js·feed.xml·index.html ?v= 캐시 버전
git add -A data feed.xml index.html
git commit -m "Daily brief $(TZ=Asia/Seoul date +%F)"
git push
```
- 러너 종료 코드: 0 성공(다음 단계 진행) / 2 사용법·동시실행 / 10 Codex 실패 / 11 타임아웃 / 12 결과 없음·JSON 오류 / 13 검증 실패 / 14 사전검증 실패.
  0이 아니면 게시하지 않는다(data/report.json은 바뀌지 않음). 로그: `/tmp/eu-trade-brief-runs/codex-run-<날짜시각>/`
  (prompt.md, codex.log, raw-report.json, verify-log.json, elapsed_seconds). 실패 시 한 번 재실행, 그래도 실패하면 그날은 건너뛴다.
- 검증 내용: date=오늘, 게재일 30시간 이내(“[누락 보완]” 항목 96시간), 출처 매체명·URL 필수, utm 제거, 대상 42개국 외 삭제,
  국가당 최대 2건, EU Top Issues 3건 이상(목표 5건). 링크 curl 재확인은 기본 OFF(`--check-links`로 켬).
- 게시 확인: `curl -s https://trade-brief-kr.github.io/eu-trade-brief/data/report.json | python3 -c "import json,sys;print(json.load(sys.stdin)['date'])"`
  (Pages 반영 1~2분)
- 드라이런: `bash tools/run_codex_research.sh --out /tmp/eutb-dry/report.json` (저장소 파일 변경 없음),
  프롬프트만: `bash tools/run_codex_research.sh --prompt-only --out /tmp/eutb-dry/report.json`

## 2. 주간 일정 (매주 월요일 — 일일 브리프 게시 후 또는 별도)
일일 뉴스 Codex 런에는 넣지 않는다. 월간 통계 때만 돌리면 일정이 낡으므로 주간 갱신을 권고한다.
```bash
python3 tools/fetch_calendar.py
python3 -c "import sys;sys.path.insert(0,'tools');from build_report_js import stamp_index;print(stamp_index())"
```
- `data/calendar.json/.js`: 오늘(KST)부터 약 35일(약 5주) 뒤까지 양끝 포함. ECB·Eurostat·BoE·SNB·Riksbank·Norges Bank·NBP·CNB·MNB·EU 이사회 공식 일정.
- Eurostat은 주요 HICP·GDP·실업만. 동적 달력이 비어 있으면 공개 ICS 링크와 공식 발표문의 명시된 다음 발표일을 시도한다.
- Consilium은 403 차단 가능. 다음 달력 페이지·공개 RSS도 시도하며 실패 원인·시도 URL을 `status`에 기록한다. RSS 게시일을 회의일/통상 기한으로 사용하지 않는다.
- 종료 코드 0: 전 출처 성공 / 3: 부분 실패(확인된 일정과 기간 내 직전 일정 유지) / 1: 일정 0개 또는 검증 실패. 0개면 게시하지 말고 원인을 확인한다.
- 날짜만 있는 일정은 현지 공표일, 시각·시간대가 있는 ICS는 KST 변환. 통상 조치 마감은 원문에 명시된 날짜만 수록하며 임의 기한을 만들지 않는다.
- 국가 선택은 EU 차원 + 선택 국가만 표시한다. 전체를 선택하면 모두 표시.

## 3. 월간 통계 (매월 1일 1회 — 일일 절차에 넣지 않음)
```bash
cd /workspace/eu-trade-brief
git pull --ff-only
python3 tools/fetch_country_stats.py        # 최신값 + 짧은 원 관측 시계열 (1~2분)
python3 tools/fetch_outlook.py              # 반드시 다음에 실행: AMECO 우선·IMF 보완 전망 병합
python3 -c "import sys;sys.path.insert(0,'tools');from build_report_js import stamp_index;print(stamp_index())"
git add data/country-stats.json data/country-stats.js index.html
git commit -m "Monthly stats $(TZ=Asia/Seoul date +%F)"
git push
```
- 종료 코드 0: 전 출처 성공 / 3: 일부 출처 실패(해당 출처는 직전 값 유지, `status`에 기록 — 내용 확인 후 그대로 게시 가능).
- 월간 두 명령을 위 순서로 고정한다. 통계 재실행은 기존 각국 `outlook`, 집계, 출처·빈티지를 보존한다. 전망만 갱신할 때는 `fetch_outlook.py`만 실행 가능.
- 통계 값은 API 응답 그대로이며 임의 입력·추정 금지. 성장 Eurostat `namq_10_gdp` 분기 전년동기비(`CLV_PCH_SM`, 계절·달력조정) 최대 12분기, 없으면 WB 연간 성장 최대 12개. HICP·실업 월간 최대 24개, BIS 월간 최대 24개(실패 시 기존 시계열 또는 최근 일간 관측). 원 관측을 보간·반올림하지 않는다.
- 전망: [EU 집행위 AMECO ZIP](https://ec.europa.eu/economy_finance/db_indicators/ameco/documents/ameco0.zip) 우선. 현재 파일일 2026-06-02, Spring 2026(2026년 봄), 2027년까지. 2026-11-13 기준 Autumn 2026 전망은 아직 미게시.
- GDP는 `.1.1.0.0.OVGD` 실질 수준만 사용(PPS `.1.2.0.0` 제외), 물가는 `.1.0.0.0.ZCPIH`(2015=100) 우선. EU27·EA21(불가리아 포함)도 동일. 수준에서 전년비를 계산해 소수 1자리: **AMECO 수준 계열로 전년비 계산. 공표 표와 끝자리 반올림이 다를 수 있음.**
- AMECO 미수록 지표는 [IMF NGDP_RPCH](https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH)·[PCPIPCH](https://www.imf.org/external/datamapper/api/v1/PCPIPCH) 전체 응답에서 필터. 영국 물가는 IMF CPI(HICP와 정의 차이). 집계는 EU·EURO, 코소보는 KOS/UVK. 브라우저 위장 UA를 쓰지 않는다.
- IMF Datamapper에는 판(vintage) 정보가 없으므로 조회일만 표시한다. 2025 실적, 2026·2027 전망 구분은 Spring 2026 기준. 미수록 소국은 자료 없음(현재 모나코·교황청; 다른 소국도 지표별 공백 가능).
- 네트워크 실패 시 직전 자료 유지와 `status`를 확인한다. 제한된 환경에서는 `fetch_outlook.py --cache-dir DIR`에 공식 원본 `ameco0.zip`, `imf-NGDP_RPCH.json`, `imf-PCPIPCH.json`을 명시적으로 제공할 수 있다. 파일 취득일(mtime)을 조회일로 사용하며 캐시 사용은 종료 코드 3.
- 일정에도 `fetch_calendar.py --source-cache DIR` 사용 가능. `manifest.json`은 URL별 `{file, asOf: "YYYY-MM-DD"}`를 기록한 공식 HTML/ICS/본문 텍스트 캐시 목록이며 7일 이내만 허용한다. 수집 실패 상태를 숨기지 않는다.

## 4. 대상 국가 변경
`tools/countries.py`의 COUNTRIES만 수정(관할지역표 개정 시) → 월간 통계 절차 재실행 → 다음 일일 조사부터 반영.
