# 검색 색인 등록 가이드 (구글 + 네이버)

자동 발행만으로는 부족하고, 검색엔진에 **사이트 등록 + 사이트맵 제출**을 해야
검색 유입(=트래픽=수익)이 시작됩니다. 1회 작업입니다.

사이트맵 주소: `https://ikdd7.github.io/sitemap.xml`
RSS 주소: `https://ikdd7.github.io/feed.xml`
(커스텀 도메인을 붙였다면 그 도메인 기준 주소로 대체)

---

## 1. 구글 서치콘솔 (Google Search Console)

1. https://search.google.com/search-console 접속 → 속성 추가 → **URL 접두어** 에
   `https://ikdd7.github.io/` 입력
2. 소유확인 방법 중 **HTML 태그** 선택 → `content="..."` 값(인증코드) 복사
3. 저장소 `_config.yml` 의 `google_site_verification: "여기에붙여넣기"` 에 입력 후 푸시
   → 배포되면 서치콘솔에서 **확인** 클릭
4. 좌측 **Sitemaps** → `sitemap.xml` 제출
5. 색인까지 보통 며칠~2주 소요

## 2. 네이버 서치어드바이저 (국내 유입 핵심)

1. https://searchadvisor.naver.com 접속 → 웹마스터도구 → 사이트 등록
   `https://ikdd7.github.io/`
2. 소유확인 **HTML 태그** → `content` 값 복사
3. `_config.yml` 의 `naver_site_verification: "여기에붙여넣기"` 에 입력 후 푸시 → **확인**
4. **요청 → 사이트맵 제출** 에 `sitemap.xml`, **RSS 제출** 에 `feed.xml` 등록

## 3. 인증코드 입력 위치 (요약)

```yaml
# _config.yml
google_site_verification: "구글에서_받은_코드"
naver_site_verification: "네이버에서_받은_코드"
```

> 두 코드는 `_layouts/default.html` 의 `<head>` 에 자동으로 메타태그로 출력됩니다.
> (구글은 jekyll-seo-tag가, 네이버는 직접 추가한 태그가 처리)

## 4. 등록 후 운영 팁

- 새 글이 매일 자동 생성되므로 사이트맵은 자동 갱신됩니다(재제출 불필요).
- 1~2주 뒤 서치콘솔 **실적** 에서 노출 키워드를 보고, 인기 키워드를 제목/본문에 반영.
- 네이버 유입이 크면 "이번 주 OO 공연", "무료 공연 추천" 류 키워드를 강화.
