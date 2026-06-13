# RUNBOOK — 일일 자동화 운영 가이드

## 1. 매일 한 번 실행되는 작업 (루프)

Claude Code 세션에서 아래 작업을 매일(또는 원하는 주기로) 반복합니다.

1. ArtBridge `get_trending_performances` 로 인기 공연 N개 수집
   - 필요시 `filter_free_events`(무료 공연), `search_events_by_location`(지역별)도 병행
2. 각 공연을 `get_event_detail` 로 보강(관람료·예매 링크·공연시간)
3. 결과를 `data/performances.json` 형식으로 저장
4. `python3 scripts/generate_post.py` 실행 → `content/<날짜>-weekly-trending.md/.html` 생성
5. 변경분 커밋 & 푸시

> 데이터 수집은 ArtBridge MCP 도구가 필요하므로 "스크립트 단독 cron" 이 아니라
> Claude 루프(에이전트가 도구를 호출)로 돌립니다.

## 2. 루프 거는 법

Claude Code 의 `/loop` 기능 사용:

```
/loop 24h 인기 공연을 ArtBridge로 다시 수집해 data/performances.json 을 갱신하고
        generate_post.py 를 실행한 뒤 content/ 변경분을 커밋·푸시해줘
```

또는 매일 아침 한 번 세션을 열어 위 프롬프트를 직접 실행해도 됩니다.

## 3. data/performances.json 스키마

```json
{
  "generated_at": "YYYY-MM-DD",
  "source": "KOPIS (ArtBridge ...)",
  "performances": [
    {
      "rank": 1,
      "id": "PF293186",
      "title": "공연명",
      "genre": "서커스/마술",
      "region": "경기도",
      "venue": "공연장",
      "period_start": "2026.06.13",
      "period_end": "2026.06.20",
      "poster": "https://...png",
      "popularity": 90,
      "days_left": 7,
      "price": "전석 18,000원",
      "running_time": "45분",
      "age": "전체 관람가",
      "booking": [{ "name": "예매처", "url": "https://..." }]
    }
  ]
}
```

필수: `rank`, `title`. 나머지는 있으면 글에 자동 포함, 없으면 생략(에러 없음).

## 4. 수익(환전) 체크리스트 — 사용자 1회 작업

- [ ] 제휴 프로그램 가입 (애드픽/텐핑 등 공연 CPA, 또는 쿠팡파트너스 등 보조 상품)
- [ ] `config/affiliate.json` 에 트래킹 링크/리다이렉트 입력
- [ ] 발행 채널 개설 (티스토리/블로그 + 구글 애드센스 승인)
- [ ] 첫 글 수동 발행 → 검색 노출(SEO) 확인
- [ ] 트래픽 쌓이면 발행 자동화(워드프레스 API 등) 추가 검토

## 5. 현실적 기대치

- 월 30만원 = 일 방문 1,000~3,000 + 제휴 클릭/전환이 누적되어야 도달.
- 초기 1~2개월은 SEO 색인/신뢰도 쌓는 기간으로 매출 거의 없음이 정상.
- 자동화는 "콘텐츠 생산 비용 0" 을 만들어 줄 뿐, 발행 채널의 권위(도메인 신뢰도)와
  꾸준함이 트래픽을 만든다.
