# 커스텀 도메인 + SEO 가이드

GitHub 기본 주소(`ikdd7.github.io/idea`) 대신 **내 도메인**으로 발행하면
브랜드·신뢰도·SEO에 유리합니다. (AdSense 승인에도 도움)

## 1. 도메인 준비
- 가비아/후이즈/Cloudflare 등에서 도메인 구매 (예: `ticketweekly.kr`, 연 1~2만원대)

## 2. DNS 설정 (도메인 등록처에서)
**서브도메인(권장, 예: `www.ticketweekly.kr`)**
- `CNAME` 레코드: `www` → `ikdd7.github.io`

**루트 도메인(`ticketweekly.kr`)도 쓰려면** A/AAAA 레코드 추가:
- A: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
- AAAA: `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`

## 3. 저장소 설정
1. 저장소 루트에 `CNAME` 파일 생성 → 내용은 도메인 한 줄 (예: `www.ticketweekly.kr`)
2. GitHub → Settings → Pages → **Custom domain** 에 도메인 입력 → **Enforce HTTPS** 체크
3. `_config.yml` 수정:
   ```yaml
   url: "https://www.ticketweekly.kr"
   baseurl: ""
   ```
   → 이후 다시 푸시하면 새 도메인으로 배포됩니다.

## 4. SEO 마무리 (이미 적용된 것 + 할 일)
이미 적용됨:
- ✅ `jekyll-seo-tag` — title/description/canonical/Open Graph 메타 자동
- ✅ `jekyll-sitemap` — `/sitemap.xml` 자동 생성
- ✅ `robots.txt` — 크롤링 허용 + 사이트맵 안내
- ✅ JSON-LD 구조화 데이터 — 공연 ItemList(Event) + FAQPage (검색 리치결과)
- ✅ RSS 피드 `/feed.xml`

직접 할 일:
- [ ] **Google Search Console** 에 사이트 등록 → `sitemap.xml` 제출
- [ ] **네이버 서치어드바이저** 에 사이트 등록 (국내 유입 핵심) → 사이트맵 제출
- [ ] 색인 후 1~2주 관찰하며 인기 키워드 중심으로 제목/본문 보강
