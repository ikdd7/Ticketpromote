#!/usr/bin/env python3
"""공연 데이터(JSON) -> 발행용 블로그 글(Markdown + HTML) 자동 생성기.

표준 라이브러리만 사용합니다 (별도 설치 불필요).

흐름:
    1) data/performances.json  (ArtBridge/KOPIS 수집 결과)
    2) config/affiliate.json   (사용자가 제휴 ID / 리다이렉트 / UTM 설정)
    3) -> content/<날짜>-weekly-trending.md  (티스토리/워드프레스 붙여넣기용)
       -> content/<날짜>-weekly-trending.html (HTML 직접 붙여넣기용)

사용:
    python scripts/generate_post.py
    python scripts/generate_post.py --data data/performances.json
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
POSTS_DIR = os.path.join(ROOT, "_posts")  # Jekyll(GitHub Pages) 게시물 디렉터리


def load_json(path: str, fallback: dict | None = None) -> dict:
    if not os.path.exists(path):
        if fallback is not None:
            return fallback
        raise SystemExit(f"[error] 파일이 없습니다: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def affiliate_link(url: str, cfg: dict) -> str:
    """예매 원본 URL에 UTM/제휴 설정을 적용해 '환전 가능한' 링크로 변환."""
    if not url:
        return url
    aff = cfg.get("affiliate", {})
    utm = aff.get("utm", {})

    # 1) UTM 파라미터 부착
    target = url
    if utm:
        sep = "&" if "?" in target else "?"
        target = f"{target}{sep}{urlencode(utm)}"

    # 2) 도메인별 제휴 래퍼(있으면 우선 적용) - {url} 토큰을 치환
    host = urlsplit(url).netloc.lower()
    overrides = aff.get("domain_overrides", {}) or {}
    for dom, template in overrides.items():
        if dom and dom.lower() in host and template:
            return template.replace("{url}", quote(target, safe=""))

    # 3) 공통 리다이렉트 베이스(있으면 적용) - 예: https://내도메인/go?u=
    base = aff.get("redirect_base", "")
    if base:
        return f"{base}{quote(target, safe='')}"

    return target


def slugify(text: str) -> str:
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return re.sub(r"[^0-9A-Za-z가-힣\-]", "", text)


def build_markdown(data: dict, cfg: dict) -> tuple[str, str]:
    gen_date = data.get("generated_at") or date.today().isoformat()
    perfs = data.get("performances", [])
    channel = cfg.get("channel", {})
    blog_name = channel.get("blog_name", "이번 주 공연 추천")
    disclosure = channel.get(
        "footer_disclosure",
        "본 포스팅은 제휴(파트너스) 활동의 일환으로 일정액의 수수료를 제공받을 수 있습니다.",
    )

    title = f"[{gen_date}] 이번 주 인기 공연 TOP {len(perfs)} — 지금 예매 가능한 추천작"
    desc = (
        "KOPIS 박스오피스 기준 이번 주 인기 공연을 한눈에. "
        + ", ".join(p.get("title", "") for p in perfs[:3])
        + " 등 예매 정보·관람료·공연장까지 정리했습니다."
    )
    tags = ["공연추천", "이번주공연", "뮤지컬", "연극", "콘서트", "예매정보", blog_name]

    lines: list[str] = []
    # YAML front matter (Jekyll/워드프레스/티스토리 메타로 재활용)
    lines.append("---")
    lines.append("layout: post")
    lines.append(f'title: "{title}"')
    lines.append(f'description: "{desc}"')
    lines.append(f"date: {gen_date}")
    lines.append("tags: [" + ", ".join(tags) + "]")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(
        f"> {gen_date} 기준 · 출처: {data.get('source', 'KOPIS')} · "
        "공연은 조기 마감될 수 있으니 예매 전 잔여 좌석을 확인하세요."
    )
    lines.append("")

    for p in perfs:
        rank = p.get("rank", "")
        lines.append(f"## {rank}. {p.get('title', '제목 미상')}")
        lines.append("")
        if p.get("poster"):
            lines.append(f"![포스터]({p['poster']})")
            lines.append("")
        bullet = []
        if p.get("genre"):
            bullet.append(f"- 🎭 **장르**: {p['genre']}")
        if p.get("region"):
            bullet.append(f"- 📍 **지역**: {p['region']}")
        if p.get("venue"):
            bullet.append(f"- 🏛️ **공연장**: {p['venue']}")
        if p.get("period_start"):
            bullet.append(
                f"- 📅 **기간**: {p.get('period_start','')} ~ {p.get('period_end','')}"
            )
        if p.get("price"):
            bullet.append(f"- 💰 **관람료**: {p['price']}")
        if p.get("running_time"):
            bullet.append(f"- ⏱️ **공연시간**: {p['running_time']}")
        if p.get("days_left") is not None:
            bullet.append(f"- ⏰ **마감까지**: {p['days_left']}일")
        lines.extend(bullet)
        lines.append("")
        for b in p.get("booking", []):
            link = affiliate_link(b.get("url", ""), cfg)
            lines.append(f"👉 **[{b.get('name', '예매하기')}로 예매하기]({link})**")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.append(f"### 🔖 더 많은 공연 정보는 *{blog_name}* 에서")
    lines.append("")
    lines.append("매주 인기 공연을 자동으로 업데이트합니다. 즐겨찾기 해두세요!")
    lines.append("")
    lines.append("태그: " + " ".join(f"#{t}" for t in tags))
    lines.append("")
    lines.append(f"<sub>{disclosure}</sub>")
    md = "\n".join(lines)

    # 간단 HTML 변환 (직접 붙여넣기용)
    html_out = markdown_to_html(md, title)
    return md, html_out


def markdown_to_html(md: str, title: str) -> str:
    body: list[str] = []
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("---") and len(line) <= 4:
            continue
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            body.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("!["):
            m = re.match(r"!\[(.*?)\]\((.*?)\)", line)
            if m:
                body.append(
                    f'<p><img src="{m.group(2)}" alt="{html.escape(m.group(1))}" '
                    'style="max-width:100%"></p>'
                )
        elif line.startswith("> "):
            body.append(f"<blockquote>{inline_html(line[2:])}</blockquote>")
        elif line.startswith("- "):
            body.append(f"<li>{inline_html(line[2:])}</li>")
        elif line.strip() == "":
            continue
        else:
            body.append(f"<p>{inline_html(line)}</p>")
    return (
        "<!doctype html>\n<html lang=\"ko\"><head><meta charset=\"utf-8\">"
        f"<title>{html.escape(title)}</title></head><body>\n"
        + "\n".join(body)
        + "\n</body></html>\n"
    )


def inline_html(text: str) -> str:
    text = re.sub(
        r"\[(.*?)\]\((.*?)\)", r'<a href="\2" target="_blank" rel="nofollow sponsored">\1</a>', text
    )
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    return text


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

    md, html_out = build_markdown(data, cfg)
    gen_date = data.get("generated_at") or date.today().isoformat()
    stem = f"{gen_date}-weekly-trending"
    md_path = os.path.join(args.postsdir, f"{stem}.md")  # GitHub Pages가 자동 발행
    html_path = os.path.join(args.outdir, f"{stem}.html")  # 타 채널용 백업
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"[ok] 생성 완료:\n  - {md_path} (Jekyll 게시물)\n  - {html_path} (HTML 백업)")
    print(f"[info] 공연 {len(data.get('performances', []))}개 반영")


if __name__ == "__main__":
    main()
