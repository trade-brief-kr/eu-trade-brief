#!/usr/bin/env bash
# 유럽 통상 브리프 조사 러너: ChatGPT(Codex CLI, 웹검색)로 일일 data/report.json을 작성하고 검증한다.
# 사람·에이전트는 직접 뉴스 조사하지 않고 이 스크립트만 실행한다. 게시는 하지 않는다(다음 단계 publish_daily.py).
#
# 사용법: bash tools/run_codex_research.sh [--out PATH] [--timeout SEC] [--check-links] [--keep-work] [--prompt-only]
#   --out PATH      검증 통과본을 쓸 위치 (기본 data/report.json). 드라이런은 저장소 밖 경로 지정.
#   --timeout SEC   Codex 최대 실행 시간 (기본 2400초, 환경변수 CODEX_TIMEOUT)
#   --check-links   (선택) 후처리에서 URL curl 재확인(404/410/DNS만 삭제). 기본 OFF — Codex 검증을 신뢰.
#   --keep-work     Codex 임시 작업 폴더를 지우지 않음
#   --prompt-only   Codex를 실행하지 않고 프롬프트만 <로그폴더>/prompt.md 로 생성 후 종료(0).
#
# 종료 코드 (0일 때만 publish_daily.py 진행)
#   0  성공   2  사용법·환경 오류/동시 실행   10 Codex 실패   11 Codex 타임아웃
#   12 결과 없음·JSON 파싱 불가   13 검증 실패   14 게시 규칙 사전검증 실패
# 실패 시 --out 파일은 변경되지 않는다. 로그: /tmp/eu-trade-brief-runs/codex-run-<날짜시각>/
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT=""; TIMEOUT="${CODEX_TIMEOUT:-2400}"; EFFORT="${CODEX_EFFORT:-high}"; CHECK_LINKS=""; KEEP=0; PROMPT_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --check-links) CHECK_LINKS="--check-links"; shift ;;
    --keep-work) KEEP=1; shift ;;
    --prompt-only) PROMPT_ONLY=1; shift ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "알 수 없는 옵션: $1" >&2; exit 2 ;;
  esac
done
[ -f "$ROOT/tools/research_prompt.md" ] || { echo "tools/research_prompt.md 없음" >&2; exit 2; }
if [ "$PROMPT_ONLY" != 1 ]; then command -v codex >/dev/null || { echo "codex CLI 없음" >&2; exit 2; }; fi

TODAY="$(TZ=Asia/Seoul date +%F)"
NOW_ISO="$(TZ=Asia/Seoul date +%Y-%m-%dT%H:%M:%S+09:00)"
DEFAULT_OUT="$ROOT/data/report.json"; : "${OUT:=$DEFAULT_OUT}"
mkdir -p "$(dirname "$OUT")"; OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
exec 9>"/tmp/eu-trade-brief-research.lock"
flock -n 9 || { echo "다른 조사 러너가 실행 중" >&2; exit 2; }
if [ "$OUT" = "$DEFAULT_OUT" ]; then LOGBASE="/tmp/eu-trade-brief-runs"; else LOGBASE="$(dirname "$OUT")"; fi
LOGDIR="$LOGBASE/codex-run-$TODAY-$(TZ=Asia/Seoul date +%H%M%S)"; mkdir -p "$LOGDIR"
WORK="$(mktemp -d /tmp/codex-eutb.XXXXXX)"
cleanup() { [ "$KEEP" = 1 ] || rm -rf "$WORK"; }
trap cleanup EXIT

COUNTRY_LIST="$(python3 - "$ROOT/tools" <<'PY'
import sys; sys.path.insert(0, sys.argv[1]); from countries import COUNTRIES
for c in COUNTRIES:
    tag = 'EU·유로' if c[6] else ('EU' if c[5] else '비EU')
    print(f"- {c[2]} ({c[3]}, {tag}, 관할 {c[4]})")
PY
)"
PREV="$(python3 - "$ROOT/data/report.json" "$TODAY" <<'PY' 2>/dev/null
import json, sys
try: r = json.load(open(sys.argv[1], encoding='utf-8'))
except Exception: sys.exit(0)
if r.get('date') == sys.argv[2]: sys.exit(0)
print(f"직전 브리프 {r.get('date')} (같은 사안 반복 금지, 새 진전만):")
for t in r.get('topIssues', []): print('- [EU]', t.get('text', '')[:90])
for c in r.get('countryNews', []):
    for it in c.get('items', []): print(f"- [{c['country']}]", it.get('title', ''))
PY
)"

PROMPT="$LOGDIR/prompt.md"
{
cat <<HDR
당신은 한국 독자를 위한 「유럽 통상 브리프」(일일)의 조사·작성자다. 웹 검색으로 실제 기사·공식 발표를 찾아 원문을 열어
확인하고, 결과를 현재 작업 폴더의 report.json 파일 하나로만 저장한다. 다른 파일은 만들거나 고치지 않는다.

기준 시각: $NOW_ISO (KST). 오늘 날짜(date): $TODAY. 조사 기간: 기준 시각 이전 24시간 게재분.

HDR
cat "$ROOT/tools/research_prompt.md"
cat <<MID

## 대상 국가 (이 이름 그대로 country에 기재, 목록 밖 국가 금지, 이 순서로 정렬)
$COUNTRY_LIST

${PREV:-(직전 브리프 없음)}

## 작업 순서 (시간 배분)
1. EU 차원 이슈 검색 → topIssues 5건.
2. 주요국부터 국가별 현지어 매체·정부 발표 검색 → 국가당 1~2건. 가능한 한 많은 국가(목표 15개국 이상), 뉴스 없는 국가는 생략.
3. 각 출처 원문을 열어 게재일시·내용 확인 후 기재. 확인 못 하면 넣지 않음.

## report.json 형식 (UTF-8, 유효한 JSON)
{
  "date": "$TODAY",
  "generatedAt": "<작성 시각 ISO 8601, +09:00>",
  "coverage": "최근 24시간 보도 중심",
  "topIssues": [
    {"text": "EU 집행위, ○○ 반덤핑 확정관세 부과 결정 … 발표", "source": "European Commission",
     "url": "https://…원문", "altUrl": "(선택) 재게재 URL", "publishedAt": "2026-…T…+01:00", "countries": ["(관련 국가가 있으면 대상국 이름)"]}
  ],
  "countryNews": [
    {"country": "독일",
     "items": [
       {"title": "짧은 제목", "category": "국제·외교|정책·규제|경제동향|산업동향|대외교역|에너지 중 하나", "korea": false,
        "bullets": [
          {"text": "핵심 내용 한 줄(명사형 종결)", "source": "Handelsblatt", "url": "https://…", "altUrl": "(선택)", "publishedAt": "…"},
          {"text": "(선택) 둘째 줄"}
        ]}
     ]}
  ],
  "notes": []
}
- bullet 첫 줄에 출처(source·url·publishedAt) 필수. 둘째 줄은 같은 출처면 생략 가능.
- 모든 URL에서 utm_* 등 추적 파라미터 제거.

## 마지막 점검 (저장 전에 반드시)
- date == $TODAY, JSON 문법 유효, topIssues 3건 이상(목표 5), 국가당 items 최대 2개, 국가 순서 = 위 목록 순서.
- 모든 출처 원문 확인 완료, 24시간(누락 보완 72시간) 밖·불확실 항목 삭제.
- 한국어 명사형 종결, 현지어 원문은 한국어로 번역, 내부 업무 지시 표현 없음.
- 현재 작업 폴더에 report.json 저장.
MID
} > "$PROMPT"
if [ "$PROMPT_ONLY" = 1 ]; then echo "프롬프트만 생성(Codex 미실행): $PROMPT"; exit 0; fi

echo "[$(TZ=Asia/Seoul date +%T) KST] Codex 일일 조사 시작 (최대 ${TIMEOUT}s) work=$WORK log=$LOGDIR"
START=$(date +%s)
for v in $(compgen -e | grep -E '^(DATA_GO_KR|GH_|GITHUB_)|KEY|TOKEN|SECRET|PASSWORD' || true); do unset "$v"; done
timeout --kill-after=60 "$TIMEOUT" codex --search exec -c model_reasoning_effort="\"$EFFORT\"" --skip-git-repo-check --ephemeral \
  -s workspace-write -C "$WORK" -o "$LOGDIR/codex-last-message.txt" - < "$PROMPT" > "$LOGDIR/codex.log" 2>&1
RC=$?
ELAPSED=$(( $(date +%s) - START )); echo "$ELAPSED" > "$LOGDIR/elapsed_seconds"
echo "[$(TZ=Asia/Seoul date +%T) KST] Codex 종료 rc=$RC, ${ELAPSED}s"
if [ $RC -eq 124 ] || [ $RC -eq 137 ]; then echo "Codex 타임아웃(${TIMEOUT}s)" >&2; exit 11; fi
if [ $RC -ne 0 ]; then echo "Codex 실패 rc=$RC (로그: $LOGDIR/codex.log)" >&2; tail -5 "$LOGDIR/codex.log" >&2; exit 10; fi
[ -s "$WORK/report.json" ] || { echo "Codex가 report.json을 만들지 않음" >&2; exit 12; }
cp "$WORK/report.json" "$LOGDIR/raw-report.json"

python3 "$ROOT/tools/verify_report.py" --input "$LOGDIR/raw-report.json" --output "$LOGDIR/verified-report.json" \
  --log "$LOGDIR/verify-log.json" $CHECK_LINKS
VRC=$?; [ $VRC -eq 0 ] || exit $VRC
python3 - "$LOGDIR/verified-report.json" "$TODAY" "$ROOT/tools" <<'PY' || exit 14
import json, sys
sys.path.insert(0, sys.argv[3]); from build_report_js import validate
r = validate(json.load(open(sys.argv[1], encoding='utf-8')))
assert r['date'] == sys.argv[2], f"date {r['date']} != {sys.argv[2]}"
print(f"사전검증 통과(게시 안 함): {r['date']}")
PY
cp "$LOGDIR/verified-report.json" "$OUT.tmp" && mv "$OUT.tmp" "$OUT"
echo "완료: $OUT (로그 $LOGDIR). 다음 단계: python3 tools/publish_daily.py"
exit 0
