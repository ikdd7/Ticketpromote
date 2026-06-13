#!/usr/bin/env python3
"""공연 데이터(JSON) -> SEO 최적화된 발행용 글(Jekyll 게시물 + HTML 백업) 생성기.

표준 라이브러리만 사용합니다 (별도 설치 불필요).

생성물:
    _posts/<날짜>-weekly-trending.md   GitHub Pages(Jekyll)가 자동 발행 (front matter + HTML 본문)
    content/<날짜>-weekly-trending.html 타 채널 붙여넣기용 자가완결 HTML (CSS 인라인)

특징:
    - 포스터 카드형 레이아웃 (UX)
    - 출연진/회차/관람연령 등 충실한 정보
    - 구조화 데이터(JSON-LD): ItemList of Event + FAQPage (검색 리치결과/SEO)
    - 제휴 링크 자동 삽입 (config/affiliate.json)
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
from datetime import date
from urllib.parse import quote, urlencode, urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA = os.path.join(ROOT, "data", "performances.json")
DEFAULT_CONFIG = os.path.join(ROOT, "config", "affiliate.json")
OUT_DIR = os.path.join(ROOT, "content")
POSTS_DIR = os.path.join(ROOT, "_posts")
CSS_PATH = os.path.join(ROOT, "assets", "css", "style.css")


def load_json(path: str, fallback: dict | None = None) -> dict:
    if not os.path.exists(path):
        if fallback is not None:
            return fallback
        raise SystemExit(f"[error] 파일이 없습니다: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ----------------------------- 도우미 -----------------------------

def affiliate_link(url: str, cfg: dict) -> str:
    """예매 URL에 UTM/제휴 설정을 적용해 '환전 가능한' 링크로 변환."""
    if not url:
        return url
    aff = cfg.get("affiliate", {})
    utm = aff.get("utm", {})
    target = url
    if utm:
        sep = "&" if "?" in target else "?"
        target = f"{target}{sep}{urlencode(utm)}"
    host = urlsplit(url).netloc.lower()
    for dom, template in (aff.get("domain_overrides", {}) or {}).items():
        if dom and not dom.startswith("_") and dom.lower() in host and template:
            return template.replace("{url}", quote(target, safe=""))
    base = aff.get("redirect_base", "")
    if base:
        return f"{base}{quote(target, safe='')}"
    return target


def iso_date(d: str) -> str:
    """'2026.06.13' -> '2026-06-13'."""
    return re.sub(r"[.\s]", "-", d.strip()).strip("-")


def parse_price(price: str) -> tuple[bool, int | None]:
    """(무료여부, 최저가 숫자)."""
    if not price:
        return False, None
    if "무료" in price:
        return True, 0
    m = re.search(r"([\d,]+)\s*원", price)
    if m:
        return False, int(m.group(1).replace(",", ""))
    return False, None


def e(s: str) -> str:
    return html.escape(str(s), quote=True)


# ----------------------------- 본문(HTML) -----------------------------

def perf_card(p: dict, cfg: dict) -> str:
    is_free, _ = parse_price(p.get("price", ""))
    booking = p.get("booking", [])
    book_url = affiliate_link(booking[0]["url"], cfg) if booking else ""
    book_name = booking[0]["name"] if booking else "예매처"
    rank = p.get("rank", "")
    poster = p.get("poster", "")
    free_ribbon = '<span class="ribbon-free">무료</span>' if is_free else ""

    meta = []
    if p.get("region"):
        meta.append(f"<li>📍 <strong>지역</strong> {e(p['region'])}</li>")
    if p.get("venue"):
        meta.append(f"<li>🏛️ <strong>공연장</strong> {e(p['venue'])}</li>")
    if p.get("period_start"):
        dday = f' <span class="dday">D-{p["days_left"]}</span>' if p.get("days_left") is not None else ""
        meta.append(
            f"<li>📅 <strong>기간</strong> {e(p['period_start'])} ~ {e(p.get('period_end',''))}{dday}</li>"
        )
    if p.get("price"):
        cls = ' class="price-free"' if is_free else ""
        meta.append(f"<li>💰 <strong>관람료</strong> <span{cls}>{e(p['price'])}</span></li>")
    if p.get("running_time"):
        meta.append(f"<li>⏱️ <strong>공연시간</strong> {e(p['running_time'])}</li>")
    if p.get("age"):
        meta.append(f"<li>🔞 <strong>관람연령</strong> {e(p['age'])}</li>")
    if p.get("showtimes"):
        meta.append(f"<li>🕒 <strong>회차</strong> {e(p['showtimes'])}</li>")
    if p.get("cast"):
        meta.append(f"<li>🎬 <strong>출연</strong> {e(', '.join(p['cast']))}</li>")

    poster_html = (
        f'<a class="perf-poster" href="{e(book_url)}" target="_blank" rel="nofollow sponsored">'
        f'<img loading="lazy" src="{e(poster)}" alt="{e(p.get("title",""))} 포스터"></a>'
        if poster
        else ""
    )
    btn = (
        f'<a class="book-btn" href="{e(book_url)}" target="_blank" rel="nofollow sponsored">'
        f"🎟️ {e(book_name)}에서 예매하기 →</a>"
        if book_url
        else ""
    )
    return f"""<article class="perf-card" id="rank-{rank}">
  <div class="perf-rank">{rank}{free_ribbon}</div>
  {poster_html}
  <div class="perf-body">
    <h2 class="perf-title">{e(p.get('title','제목 미상'))} <span class="genre-badge">{e(p.get('genre',''))}</span></h2>
    <ul class="perf-meta">
      {''.join(meta)}
    </ul>
    {btn}
  </div>
</article>"""


def summary_table(perfs: list[dict]) -> str:
    rows = []
    for p in perfs:
        is_free, _ = parse_price(p.get("price", ""))
        price_cell = '<span class="price-free">무료</span>' if is_free else e(p.get("price", "-"))
        dday = f"D-{p['days_left']}" if p.get("days_left") is not None else "-"
        rows.append(
            f"<tr><td>{p.get('rank','')}</td>"
            f'<td><a href="#rank-{p.get("rank","")}">{e(p.get("title",""))}</a></td>'
            f"<td>{e(p.get('genre',''))}</td><td>{e(p.get('region',''))}</td>"
            f"<td>{price_cell}</td><td>{dday}</td></tr>"
        )
    return (
        '<table class="summary"><thead><tr>'
        "<th>순위</th><th>공연명</th><th>장르</th><th>지역</th><th>관람료</th><th>마감</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )


def event_ld(perfs: list[dict], cfg: dict) -> str:
    items = []
    for p in perfs:
        is_free, price_val = parse_price(p.get("price", ""))
        booking = p.get("booking", [])
        offer = {
            "@type": "Offer",
            "priceCurrency": "KRW",
            "availability": "https://schema.org/InStock",
        }
        if price_val is not None:
            offer["price"] = str(price_val)
        if booking:
            offer["url"] = affiliate_link(booking[0]["url"], cfg)
        event = {
            "@type": "Event",
            "name": p.get("title", ""),
            "startDate": iso_date(p.get("period_start", "")),
            "endDate": iso_date(p.get("period_end", "")),
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "location": {
                "@type": "Place",
                "name": p.get("venue", ""),
                "address": {"@type": "PostalAddress", "addressRegion": p.get("region", ""), "addressCountry": "KR"},
            },
            "image": p.get("poster", ""),
            "offers": offer,
        }
        if p.get("cast"):
            event["performer"] = [{"@type": "Person", "name": c} for c in p["cast"]]
        items.append({"@type": "ListItem", "position": p.get("rank", 0), "item": event})
    data = {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": items}
    return '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False, indent=2) + "\n</script>"


def faq_block(perfs: list[dict]) -> tuple[str, str]:
    free = [p["title"] for p in perfs if parse_price(p.get("price", ""))[0]]
    top = perfs[0]["title"] if perfs else ""
    regions = sorted({p.get("region", "") for p in perfs if p.get("region")})
    qa = [
        ("이번 주 가장 인기 있는 공연은 무엇인가요?",
         f"KOPIS 박스오피스 기준 이번 주 1위는 ‘{top}’입니다. 전체 순위는 본문 표에서 확인할 수 있습니다."),
        ("이번 주 무료로 볼 수 있는 공연이 있나요?",
         ("네, " + ", ".join(f"‘{t}’" for t in free) + " 등을 무료로 관람할 수 있습니다.") if free
         else "이번 주 목록에는 무료 공연이 포함되어 있지 않습니다."),
        ("공연 예매는 어디서 하나요?",
         "각 공연 카드의 ‘예매하기’ 버튼을 누르면 해당 예매처(인터파크·네이버 예약·공연장 등)로 이동합니다."),
        ("어느 지역 공연이 포함되어 있나요?",
         "이번 주 목록에는 " + ", ".join(regions) + " 지역 공연이 포함되어 있습니다."),
    ]
    html_items = "".join(
        f'<details class="faq-item"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in qa
    )
    ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa
        ],
    }
    ld_html = '<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False, indent=2) + "\n</script>"
    return f'<section class="faq"><h2>자주 묻는 질문</h2>{html_items}</section>', ld_html


def build(data: dict, cfg: dict) -> tuple[str, str, dict]:
    gen_date = data.get("generated_at") or date.today().isoformat()
    perfs = data.get("performances", [])
    channel = cfg.get("channel", {})
    blog_name = channel.get("blog_name", "이번 주 공연 추천")
    disclosure = channel.get(
        "footer_disclosure",
        "본 포스팅은 제휴(파트너스) 활동의 일환으로 일정액의 수수료를 제공받을 수 있습니다.",
    )
    genres = sorted({p.get("genre", "") for p in perfs if p.get("genre")})
    regions = sorted({p.get("region", "") for p in perfs if p.get("region")})
    free_cnt = sum(1 for p in perfs if parse_price(p.get("price", ""))[0])

    title = f"[{gen_date}] 이번 주 인기 공연 TOP {len(perfs)} — 예매·관람료·무료공연 총정리"
    desc = (
        f"{gen_date} KOPIS 박스오피스 기준 인기 공연 {len(perfs)}편을 한눈에. "
        f"{', '.join(p.get('title','') for p in perfs[:3])} 등 "
        f"{'·'.join(genres)} 장르, 예매 링크·관람료·공연 시간·출연진까지 정리했습니다."
    )
    tags = ["공연추천", "이번주공연", "뮤지컬추천", "연극추천", "콘서트", "무료공연", "예매정보", blog_name]
    image = next((p.get("poster") for p in perfs if p.get("poster")), "")

    # ---- 본문 HTML ----
    parts: list[str] = []
    parts.append(event_ld(perfs, cfg))
    parts.append(
        f'<p class="lead">이번 주({gen_date} 기준) <strong>{"·".join(regions)}</strong>에서 열리는 '
        f"<strong>{'·'.join(genres)}</strong> 인기 공연 <strong>{len(perfs)}편</strong>을 모았습니다. "
        f"이 중 <strong>{free_cnt}편</strong>은 무료로 관람할 수 있어요. "
        "공연은 좌석이 빠르게 마감되니, 마음에 드는 공연은 서둘러 예매하세요.</p>"
    )
    parts.append("<h2>한눈에 보기</h2>")
    parts.append(summary_table(perfs))
    parts.append("<h2>인기 공연 상세</h2>")
    for p in perfs:
        parts.append(perf_card(p, cfg))
    if free_cnt:
        free_titles = [p.get("title", "") for p in perfs if parse_price(p.get("price", ""))[0]]
        parts.append(
            '<section class="free-callout"><h2>🎁 이번 주 무료 공연</h2><p>'
            + ", ".join(f"<strong>{e(t)}</strong>" for t in free_titles)
            + " — 예매 서둘러 챙기세요!</p></section>"
        )
    faq_html, faq_ld = faq_block(perfs)
    parts.append(faq_html)
    parts.append(faq_ld)
    parts.append(
        f'<p class="outro">매주 <strong>{e(blog_name)}</strong>에서 KOPIS 인기 공연을 자동으로 업데이트합니다. '
        "즐겨찾기 해두고 주말 공연 계획에 활용해 보세요!</p>"
    )
    parts.append('<p class="tags">' + " ".join(f"#{t}" for t in tags) + "</p>")
    parts.append(f'<p class="disclosure">{e(disclosure)}</p>')
    body = "\n".join(parts)

    meta = {"title": title, "description": desc, "date": gen_date, "tags": tags, "image": image}
    return body, gen_date, meta


def render_post(body: str, meta: dict) -> str:
    fm = [
        "---",
        "layout: post",
        f'title: "{meta["title"]}"',
        f'description: "{meta["description"]}"',
        f"date: {meta['date']}",
        f'image: "{meta["image"]}"',
        "tags: [" + ", ".join(meta["tags"]) + "]",
        "---",
        "",
    ]
    return "\n".join(fm) + body + "\n"


def render_html_backup(body: str, meta: dict) -> str:
    css = ""
    if os.path.exists(CSS_PATH):
        with open(CSS_PATH, encoding="utf-8") as f:
            css = f.read()
    return (
        '<!doctype html>\n<html lang="ko-KR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{e(meta['title'])}</title>"
        f'<meta name="description" content="{e(meta["description"])}">'
        f"<style>{css}</style></head><body><main class=\"wrap\"><article class=\"post\">"
        f"<h1>{e(meta['title'])}</h1>\n{body}\n</article></main></body></html>\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--outdir", default=OUT_DIR, help="HTML 백업 출력 디렉터리")
    ap.add_argument("--postsdir", default=POSTS_DIR, help="Jekyll 게시물(_posts) 디렉터리")
    args = ap.parse_args()

    data = load_json(args.data)
    cfg = load_json(args.config, fallback={})
    os.makedirs(args.outdir, exist_ok=True)
    os.makedirs(args.postsdir, exist_ok=True)

    body, gen_date, meta = build(data, cfg)
    stem = f"{gen_date}-weekly-trending"
    md_path = os.path.join(args.postsdir, f"{stem}.md")
    html_path = os.path.join(args.outdir, f"{stem}.html")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_post(body, meta))
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(render_html_backup(body, meta))

    print(f"[ok] 생성 완료:\n  - {md_path} (Jekyll 게시물)\n  - {html_path} (HTML 백업)")
    print(f"[info] 공연 {len(data.get('performances', []))}개 · 구조화 데이터(JSON-LD) 포함")


if __name__ == "__main__":
    main()
