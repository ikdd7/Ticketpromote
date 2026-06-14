#!/usr/bin/env python3
"""공연 데이터 -> 카카오 오픈채팅용 발송 메시지(<=200자) 자동 작성.

카카오톡은 오픈채팅 자동 발송 API가 없으므로:
  1) 이 스크립트로 발송 메시지를 자동 작성
  2) '나에게 보내기'(MemoChat)로 본인 카톡에 전송
  3) 사용자가 오픈채팅방에 1탭 전달(붙여넣기)

출력: products/broadcast-<날짜>.txt (그리고 표준출력)
"""
from __future__ import annotations

import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA = os.path.join(ROOT, "data", "performances.json")
CONFIG_YML = os.path.join(ROOT, "_config.yml")
OUT_DIR = os.path.join(ROOT, "products")
LIMIT = 200


def site_url() -> str:
    """_config.yml 의 url + baseurl 로 사이트 주소 구성."""
    url, base = "https://ikdd7.github.io", ""
    try:
        txt = open(CONFIG_YML, encoding="utf-8").read()
        m = re.search(r'^url:\s*"?([^"\n]+)"?', txt, re.M)
        b = re.search(r'^baseurl:\s*"?([^"\n]*)"?', txt, re.M)
        if m:
            url = m.group(1).strip()
        if b:
            base = b.group(1).strip()
    except OSError:
        pass
    return (url.rstrip("/") + "/" + base.strip("/")).rstrip("/") + "/"


def is_free(price: str) -> bool:
    return "무료" in (price or "")


def short_title(t: str) -> str:
    """[지역] 같은 꼬리표 제거해 짧게."""
    return re.sub(r"\s*\[[^\]]*\]\s*", "", t).strip()


def build_message(data: dict, url: str) -> str:
    perfs = data.get("performances", [])
    gen = (data.get("generated_at") or "").replace("-", ".")[5:]  # MM.DD
    free = [short_title(p["title"]) for p in perfs if is_free(p.get("price", ""))]
    urgent = [p for p in perfs if (p.get("days_left") or 99) <= 2]

    lines = [f"🎭 이번 주 인기 공연 ({gen})"]
    for p in perfs[:3]:
        tag = "(무료)" if is_free(p.get("price", "")) else f"({p.get('region','')[:2]})"
        lines.append(f"{p.get('rank')}. {short_title(p.get('title',''))}{tag}")
    if free:
        lines.append("🎁 무료: " + ", ".join(free[:3]))
    if urgent:
        lines.append(f"⏰ 마감임박 {len(urgent)}편! 서둘러요")
    lines.append(f"👉 전체 가이드+예매 {url}")

    msg = "\n".join(lines)
    if len(msg) > LIMIT:
        # 링크는 보존하고 중간을 줄임
        link = lines[-1]
        head = "\n".join(lines[:-1])
        room = LIMIT - len(link) - 2
        msg = head[: max(0, room)].rstrip() + "\n" + link
    return msg[:LIMIT]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--outdir", default=OUT_DIR)
    ap.add_argument("--url", default=None, help="가이드 링크(미지정 시 _config 에서 구성)")
    args = ap.parse_args()

    data = json.load(open(args.data, encoding="utf-8"))
    url = args.url or site_url()
    msg = build_message(data, url)

    os.makedirs(args.outdir, exist_ok=True)
    gen_date = data.get("generated_at") or ""
    out = os.path.join(args.outdir, f"broadcast-{gen_date}.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(msg + "\n")

    print(msg)
    print(f"\n[ok] {len(msg)}자 / {LIMIT}자 · 저장: {out}")


if __name__ == "__main__":
    main()
