#!/bin/bash
# 일일 자동 갱신: 글 생성 → 커밋 → 푸시
# (데이터 수집(ArtBridge)은 에이전트가 data/performances.json 을 갱신한 뒤 호출)
set -euo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
BRANCH="claude/model-1g2dvg"

python3 scripts/generate_post.py

if git diff --quiet && git diff --cached --quiet; then
  echo "[daily_update] 변경 없음 — 커밋 생략"
  exit 0
fi

git add -A
git commit -m "chore: $(date +%F) 인기 공연 일일 자동 갱신"

for i in 1 2 3 4; do
  if git push -u origin "$BRANCH"; then
    echo "[daily_update] 푸시 완료"
    exit 0
  fi
  sleep $((2 ** i))
done

echo "[daily_update] 푸시 실패" >&2
exit 1
