#!/bin/bash
# SessionStart 훅: 세션이 열리면(예약 트리거 포함) 오늘자 인기 공연 글이 없을 때
# 에이전트에게 일일 자동화 작업을 지시(additionalContext)한다.
# 데이터 수집(ArtBridge MCP)은 에이전트만 가능하므로 훅은 '지시'까지만 담당.
set -euo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# python3 는 표준 라이브러리만 사용 → 설치 불필요, 존재만 확인
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"[ticketpromote] python3 미설치 — 일일 자동화 불가."}}'
  exit 0
fi

TODAY="$(date +%F)"
POST="_posts/${TODAY}-weekly-trending.md"

# 이미 오늘 글이 있으면 멱등하게 종료(중복 실행 방지)
if [ -f "$POST" ]; then
  exit 0
fi

CTX="[ticketpromote 일일 자동화] 오늘(${TODAY}) 인기 공연 글이 아직 없습니다. 다음을 순서대로 수행하세요:
1) ArtBridge get_trending_performances 로 인기 공연을 수집하고, 상위 공연은 get_event_detail 로 예매링크·관람료를 보강합니다.
2) data/performances.json 을 오늘 날짜(\"generated_at\": \"${TODAY}\")로 갱신합니다 (스키마는 RUNBOOK.md 참고).
3) ./scripts/daily_update.sh 를 실행해 글 생성·커밋·푸시합니다 (GitHub Actions가 사이트를 자동 배포).
이 작업은 자동 발행 파이프라인의 정규 일과입니다."

# additionalContext 를 안전하게 JSON 인코딩해 stdout 으로만 출력
CTX="$CTX" python3 - <<'PY'
import json, os
ctx = os.environ["CTX"]
print(json.dumps(
    {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}},
    ensure_ascii=False,
))
PY
