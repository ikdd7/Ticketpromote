# Ticketpromote — 공연 인기글 자동 생성 파이프라인

KOPIS(공연예술통합전산망) 인기 공연 데이터를 매일 자동 수집해
**티스토리/워드프레스에 바로 붙여넣을 수 있는 블로그 글**(Markdown + HTML)을
생성합니다. 제휴 링크가 자동으로 삽입되므로, 트래픽이 쌓이면 제휴 수수료로 환전됩니다.

```
ArtBridge(KOPIS)  ─수집→  data/performances.json
                                   │
                  scripts/generate_post.py  ←  config/affiliate.json (제휴 설정)
                                   │
                                   ▼
                content/<날짜>-weekly-trending.md   ← 블로그에 붙여넣기
                content/<날짜>-weekly-trending.html  ← HTML 에디터에 붙여넣기
```

## 역할 분담

| 단계 | 담당 | 자동화 |
|------|------|--------|
| 1. 인기 공연 데이터 수집 | Claude(루프) | ✅ 자동 |
| 2. 블로그 글 생성(제휴 링크 삽입) | `generate_post.py` | ✅ 자동 |
| 3. **제휴 가입 + 발행 채널 연결(=환전)** | **사용자** | ⛳ 수동(최초 1회) |
| 4. 글 발행 | 사용자 / 추후 자동화 | 반자동 |

## 빠른 시작

```bash
# 콘텐츠 생성 (data/ + config/ 를 읽어 content/ 에 글 생성)
python3 scripts/generate_post.py
```

`content/` 에 생성된 `.md` 를 블로그에 붙여넣으면 끝입니다.

## 환전 설정 (사용자가 채우는 유일한 부분)

`config/affiliate.json` 한 파일만 채우면 모든 글에 자동 반영됩니다.

1. **제휴 프로그램 가입** — 예: 애드픽/텐핑(공연 CPA), 또는 자체 도메인 리다이렉트
2. `affiliate.domain_overrides` 에 예매처별 트래킹 링크 템플릿 입력
   (`{url}` 자리에 대상 URL이 인코딩되어 들어감)
3. 또는 `affiliate.redirect_base` 에 본인 도메인 리다이렉트 입력
4. 블로그/티스토리 + 애드센스 채널 연결

> 제휴 설정을 비워두면 UTM 파라미터만 붙은 일반 링크로 생성됩니다(에러 없음).

## 자동 운영(루프)

매일 자동 갱신은 `RUNBOOK.md` 참고. 핵심은:
Claude 가 루프마다 ArtBridge 인기 공연을 다시 받아 `data/performances.json` 을
갱신하고 `generate_post.py` 를 실행해 그날짜 글을 만드는 것입니다.

## 디렉터리

```
scripts/generate_post.py   글 생성기 (표준 라이브러리만, 의존성 없음)
config/affiliate.json      제휴/UTM/채널 설정 (← 환전 지점)
data/performances.json     최신 수집 데이터 (루프마다 갱신)
content/                   생성된 발행용 글 (md + html)
RUNBOOK.md                 일일 자동화 운영 가이드
```
