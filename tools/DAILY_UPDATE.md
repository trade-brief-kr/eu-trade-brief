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

## 2. 월간 통계 (매월 1일 1회 — 일일 절차에 넣지 않음)
```bash
cd /workspace/eu-trade-brief
git pull --ff-only
python3 tools/fetch_country_stats.py        # World Bank·Eurostat·BIS·UN Comtrade → data/country-stats.json/.js (1~2분)
python3 -c "import sys;sys.path.insert(0,'tools');from build_report_js import stamp_index;print(stamp_index())"
git add data/country-stats.json data/country-stats.js index.html
git commit -m "Monthly stats $(TZ=Asia/Seoul date +%F)"
git push
```
- 종료 코드 0: 전 출처 성공 / 3: 일부 출처 실패(해당 출처는 직전 값 유지, `status`에 기록 — 내용 확인 후 그대로 게시 가능).
- 값은 API 응답 그대로이며 임의 입력·추정 금지. 미수록 지표는 화면에 “자료 없음”으로 표시.

## 3. 대상 국가 변경
`tools/countries.py`의 COUNTRIES만 수정(관할지역표 개정 시) → 월간 통계 절차 재실행 → 다음 일일 조사부터 반영.
