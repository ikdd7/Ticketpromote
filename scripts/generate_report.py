#!/usr/bin/env python3
"""공연 데이터(JSON) -> 판매용 '주간 공연 가이드' 제품(A4 인쇄용 HTML) 생성기.

표준 라이브러리만 사용 (의존성 없음).
산출물: products/weekly-guide-<날짜>.html
    → 브라우저에서 열고 '인쇄 > PDF로 저장' 하면 판매용 PDF 완성.
    → Gumroad / 크몽 / 부스트 등에 업로드해 판매.

차별점(=돈 주고 살 이유):
    - 큐레이션(데이트·가족·무료·마감임박)으로 '고르는 수고'를 대신
    - 예매 링크·관람료·회차·출연진을 한 장에 정리
    - 매주 자동 갱신 → 정기 상품화 가능
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA = os.path.join(ROOT, "data", "performances.json")
OUT_DIR = os.path.join(ROOT, "products")


def e(s) -> str:
    return html.escape(str(s), quote=True)


def parse_price(price: str) -> tuple[bool, int | None]:
    if not price:
        return False, None
    if "무료" in price:
        return True, 0
    m = re.search(r"([\d,]+)\s*원", price)
    return (False, int(m.group(1).replace(",", ""))) if m else (False, None)


def min_age(age: str) -> int:
    """관람 가능 최소 나이(숫자). '전체 관람가'->0, '만 13세'->13, 불명->99."""
    if not age:
        return 99
    if "전체" in age:
        return 0
    m = re.search(r"(\d+)", age)
    return int(m.group(1)) if m else 99


def curate(perfs: list[dict]) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = {"무료": [], "마감임박": [], "가족": [], "데이트": []}
    for p in perfs:
        is_free, _ = parse_price(p.get("price", ""))
        if is_free:
            buckets["무료"].append(p)
        if (p.get("days_left") or 99) <= 2:
            buckets["마감임박"].append(p)
        if min_age(p.get("age", "")) <= 7:
            buckets["가족"].append(p)
        else:
            buckets["데이트"].append(p)
    return buckets


CSS = """
@page { size: A4; margin: 16mm 14mm; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Apple SD Gothic Neo", "Pretendard", "Malgun Gothic", sans-serif;
  color: #1c1e26; line-height: 1.6; margin: 0; word-break: keep-all; }
.page { page-break-after: always; }
.page:last-child { page-break-after: auto; }
.cover { display:flex; flex-direction:column; justify-content:center; min-height: 250mm; text-align:center; }
.cover .kicker { color:#ff4d6d; font-weight:800; letter-spacing:.15em; }
.cover h1 { font-size: 34px; margin: 10px 0; line-height:1.25; }
.cover .sub { color:#666; font-size: 15px; }
.cover .meta { margin-top: 28px; color:#888; font-size: 13px; }
h2 { font-size: 20px; border-left: 5px solid #ff4d6d; padding-left: 10px; margin: 26px 0 12px; }
table { width:100%; border-collapse: collapse; font-size: 12.5px; }
th { background:#f3f4f7; text-align:left; padding:7px 8px; }
td { padding:7px 8px; border-top:1px solid #e6e8ee; }
.free { color:#2a7; font-weight:700; }
.pick { display:flex; gap:8px; flex-wrap:wrap; margin: 8px 0 4px; }
.pick .tag { background:#fff0f3; color:#ff4d6d; border-radius:999px; padding:3px 10px; font-size:12px; font-weight:700; }
.card { display:grid; grid-template-columns: 34mm 1fr; gap: 10px; border:1px solid #e6e8ee; border-radius:10px;
  padding:10px; margin:10px 0; page-break-inside: avoid; }
.card img { width:100%; aspect-ratio:3/4; object-fit:cover; border-radius:6px; background:#eee; }
.card h3 { margin:0 0 6px; font-size:15px; }
.card ul { margin:0; padding-left: 16px; font-size:12.5px; }
.badge { display:inline-block; background:#eef; color:#446; border-radius:6px; padding:1px 7px; font-size:11px; margin-left:4px; }
.note { background:#f7f8fb; border:1px solid #e6e8ee; border-radius:10px; padding:12px 14px; font-size:13px; }
a { color:#3355cc; text-decoration:none; }
.footer { color:#aaa; font-size:11px; text-align:center; margin-top:18px; }
"""


def cover(gen_date: str, n: int, brand: str) -> str:
    return f"""<section class="page cover">
  <div class="kicker">WEEKLY PERFORMANCE GUIDE</div>
  <h1>이번 주 전국 인기 공연<br>완전정복 가이드</h1>
  <div class="sub">KOPIS 박스오피스 기준 인기 공연 {n}편 · 예매링크·관람료·무료공연·큐레이션</div>
  <div class="meta">{gen_date} 기준 · {brand}</div>
</section>"""


def overview(perfs: list[dict]) -> str:
    rows = []
    for p in perfs:
        is_free, _ = parse_price(p.get("price", ""))
        price = '<span class="free">무료</span>' if is_free else e(p.get("price", "-"))
        rows.append(
            f"<tr><td>{p.get('rank','')}</td><td>{e(p.get('title',''))}</td>"
            f"<td>{e(p.get('genre',''))}</td><td>{e(p.get('region',''))}</td>"
            f"<td>{price}</td><td>D-{p.get('days_left','-')}</td></tr>"
        )
    return (
        '<section class="page"><h2>이번 주 한눈에 보기</h2><table>'
        "<tr><th>#</th><th>공연명</th><th>장르</th><th>지역</th><th>관람료</th><th>마감</th></tr>"
        + "".join(rows)
        + "</table>"
        + picks(perfs)
        + "</section>"
    )


def picks(perfs: list[dict]) -> str:
    b = curate(perfs)
    def names(lst):
        return ", ".join(e(p.get("title", "")) for p in lst) or "해당 없음"
    return f"""<h2>큐레이션 PICK</h2>
<div class="note">
  <p>🎁 <b>무료로 즐기기</b> — {names(b['무료'])}</p>
  <p>⏰ <b>마감 임박(서둘러요)</b> — {names(b['마감임박'])}</p>
  <p>👨‍👩‍👧 <b>가족·아이와 함께</b> — {names(b['가족'])}</p>
  <p>💕 <b>데이트·친구와</b> — {names(b['데이트'])}</p>
</div>"""


def detail_pages(perfs: list[dict]) -> str:
    cards = []
    for p in perfs:
        is_free, _ = parse_price(p.get("price", ""))
        booking = p.get("booking", [])
        book = (
            f'<li>🎟️ 예매: <a href="{e(booking[0]["url"])}">{e(booking[0]["name"])}</a></li>'
            if booking else ""
        )
        cast = f"<li>🎬 출연: {e(', '.join(p['cast']))}</li>" if p.get("cast") else ""
        price = '<span class="free">전석무료</span>' if is_free else e(p.get("price", "-"))
        poster = f'<img src="{e(p.get("poster",""))}" alt="">' if p.get("poster") else "<div></div>"
        cards.append(f"""<div class="card">
  {poster}
  <div>
    <h3>{p.get('rank','')}. {e(p.get('title',''))} <span class="badge">{e(p.get('genre',''))}</span></h3>
    <ul>
      <li>📍 {e(p.get('region',''))} · {e(p.get('venue',''))}</li>
      <li>📅 {e(p.get('period_start',''))} ~ {e(p.get('period_end',''))} (D-{p.get('days_left','-')})</li>
      <li>💰 {price} · ⏱️ {e(p.get('running_time','-'))} · 🔞 {e(p.get('age','-'))}</li>
      <li>🕒 {e(p.get('showtimes','-'))}</li>
      {cast}
      {book}
    </ul>
  </div>
</div>""")
    return '<section class="page"><h2>공연 상세 정보</h2>' + "".join(cards) + "</section>"


def guide_page(brand: str) -> str:
    return f"""<section class="page">
<h2>예매 가이드 & 활용 팁</h2>
<div class="note">
  <p><b>1. 예매처 바로가기</b> — 각 공연의 ‘예매’ 링크를 누르면 인터파크·네이버 예약·공연장 페이지로 이동합니다.</p>
  <p><b>2. 무료 공연은 빨리</b> — 무료/마감임박 공연은 좌석이 가장 먼저 동납니다. 큐레이션 PICK을 먼저 확인하세요.</p>
  <p><b>3. 매주 업데이트</b> — 이 가이드는 매주 자동 갱신됩니다. 정기 구독으로 받아보세요.</p>
</div>
<p class="footer">데이터 출처: KOPIS 공연예술통합전산망 · 본 자료는 {brand}가 자동 정리한 큐레이션 가이드입니다.
공연 정보는 변경될 수 있으니 예매 전 공식 페이지에서 최종 확인하세요.</p>
</section>"""


def build(data: dict, brand: str) -> str:
    gen_date = data.get("generated_at") or date.today().isoformat()
    perfs = data.get("performances", [])
    body = (
        cover(gen_date, len(perfs), brand)
        + overview(perfs)
        + detail_pages(perfs)
        + guide_page(brand)
    )
    return (
        '<!doctype html><html lang="ko-KR"><head><meta charset="utf-8">'
        f"<title>이번 주 공연 가이드 {gen_date}</title><style>{CSS}</style></head>"
        f"<body>{body}</body></html>\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--outdir", default=OUT_DIR)
    ap.add_argument("--brand", default="위클리 공연 가이드")
    args = ap.parse_args()

    data = json.load(open(args.data, encoding="utf-8"))
    os.makedirs(args.outdir, exist_ok=True)
    gen_date = data.get("generated_at") or date.today().isoformat()
    out = os.path.join(args.outdir, f"weekly-guide-{gen_date}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build(data, args.brand))
    print(f"[ok] 제품 생성: {out}")
    print(f"[info] 공연 {len(data.get('performances', []))}편 · 브라우저에서 '인쇄 > PDF로 저장'으로 판매용 PDF 완성")


if __name__ == "__main__":
    main()
