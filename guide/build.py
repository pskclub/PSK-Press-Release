#!/usr/bin/env python3
"""Build the PSK Press user guide: guide/pages/*.html -> docs/*.html.

Each page source starts with two lines:
    title: หัวข้อหน้า
    desc: คำอธิบายสั้น (meta description และบรรทัดนำ)
then an HTML body. Shorthands:
    [[ข้อความปุ่ม]]                   -> a label exactly as it appears in the app
    <fig src="x.png" tall>คำอธิบาย</fig> -> a zoomable screenshot from docs/img/
Run: python guide/build.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "guide" / "pages"
OUT = ROOT / "docs"
RELEASES = "https://github.com/pskclub/PSK-Press-Release/releases/latest"

# (group, [(file, menu label)])
NAV = [
    ("เริ่มต้น", [
        ("index", "หน้าแรก"),
        ("install", "ติดตั้งและอัปเดต"),
        ("connect", "เชื่อมเบราว์เซอร์และบัญชี"),
        ("setup", "ตั้งค่าครั้งแรก"),
        ("quickstart", "คลิปแรกใน 10 นาที"),
    ]),
    ("สร้างงาน", [
        ("create-basics", "พื้นฐานหน้าสร้างงาน"),
        ("finish", "การตกแต่งและส่งออก"),
        ("product", "คลิปขายสินค้า"),
        ("ai-clips", "คลิป AI ด้วย Google Flow"),
        ("story", "เรื่องเล่า AI"),
        ("news", "ข่าว"),
        ("podcast", "พอดแคสต์"),
        ("remix", "รีมิกซ์ & ขัดเกลา"),
        ("imageset", "ชุดภาพสินค้า"),
        ("editor", "ตัดต่อเอง"),
    ]),
    ("งาน", [
        ("storyboard", "ตรวจฉาก (storyboard)"),
        ("queue", "คิวงานและบันทึก"),
        ("library", "ผลงาน"),
        ("publish", "โพสต์"),
    ]),
    ("คลัง", [
        ("products", "สินค้า"),
        ("characters", "ตัวละคร"),
        ("audio", "เสียง & เพลง"),
    ]),
    ("ระบบ", [
        ("settings", "ตั้งค่าทั้งหมด"),
        ("prompts", "พรอมต์ระบบ"),
        ("troubleshooting", "แก้ปัญหาที่พบบ่อย"),
        ("faq", "คำถามที่พบบ่อย"),
        ("responsible", "ใช้อย่างรับผิดชอบ"),
    ]),
]
ORDER = [f for _, items in NAV for f, _ in items]
LABEL = {f: l for _, items in NAV for f, l in items}


def nav_html(current):
    out = []
    for group, items in NAV:
        out.append(f"<h4>{html.escape(group)}</h4>")
        for f, label in items:
            cur = ' aria-current="page"' if f == current else ""
            out.append(f'<a href="{f}.html"{cur}>{html.escape(label)}</a>')
    return "\n".join(out)


def expand(body):
    body = re.sub(r"\[\[(.+?)\]\]", lambda m: f'<span class="ui">{m.group(1)}</span>', body)

    def fig(m):
        attrs, cap = m.group(1), m.group(2).strip()
        src = re.search(r'src="([^"]+)"', attrs).group(1)
        tall = " tall" if re.search(r"\btall\b", attrs) else ""
        alt = re.sub(r"<[^>]+>", "", cap) or src
        return (
            f'<figure><a class="shot{tall}" href="img/{src}"><img src="img/{src}" alt="{html.escape(alt)}" '
            f'loading="lazy" width="1440"></a><figcaption>{cap}</figcaption></figure>'
        )

    return re.sub(r"<fig\b([^>]*)>(.*?)</fig>", fig, body, flags=re.S)


def slug_headings(body):
    """Give h2/h3 an id (h-1, h-2…) when they have none."""
    n = 0

    def add(m):
        nonlocal n
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        if "id=" in attrs:
            return m.group(0)
        n += 1
        return f'<{tag}{attrs} id="h-{n}">{inner}</{tag}>'

    return re.sub(r"<(h[23])([^>]*)>(.*?)</\1>", add, body, flags=re.S)


def text_of(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


PAGE = """<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · คู่มือ PSK Press</title>
<meta name="description" content="{desc}">
<link rel="icon" href="assets/icon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans+Thai:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
<script>try{{var t=localStorage.getItem("psk-guide-theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
</head>
<body>
<header class="top">
  <button class="btn icon-btn menu-btn" type="button" aria-label="เมนู" aria-expanded="false" aria-controls="nav">☰</button>
  <a class="brand" href="index.html"><span class="logo">P.</span><span class="name">PSK Press<small>คู่มือการใช้งาน</small></span></a>
  <span class="spacer"></span>
  <div class="search" role="search">
    <input type="search" placeholder="ค้นหาในคู่มือ…" aria-label="ค้นหาในคู่มือ" autocomplete="off">
    <div class="results" role="listbox"></div>
  </div>
  <button class="btn icon-btn theme-btn" type="button" aria-label="สลับธีมสว่าง/มืด">◐</button>
  <a class="btn primary dl" href="{releases}">⭳ <span>ดาวน์โหลด</span></a>
</header>
<div class="layout">
<nav class="nav" id="nav" aria-label="สารบัญคู่มือ">
{nav}
</nav>
<main>
<article class="doc">
{eyebrow}
<h1>{title}</h1>
<p class="lead">{desc}</p>
{body}
{pager}
<footer class="site">PSK Press · คู่มือนี้อธิบายเวอร์ชันล่าสุดในหน้า <a href="{releases}">ดาวน์โหลด</a> · ภาพหน้าจอใช้ข้อมูลตัวอย่าง</footer>
</article>
</main>
<aside class="toc" aria-label="ในหน้านี้"></aside>
</div>
<div class="lightbox" role="dialog" aria-label="ภาพขยาย"><img alt=""></div>
<script src="assets/site.js"></script>
</body>
</html>
"""


def build():
    index = []
    for f in ORDER:
        src = (SRC / f"{f}.html").read_text(encoding="utf-8")
        head, body = src.split("\n\n", 1)
        meta = dict(line.split(": ", 1) for line in head.strip().splitlines())
        title, desc = meta["title"], meta["desc"]
        body = slug_headings(expand(body))
        group = next(g for g, items in NAV if any(x == f for x, _ in items))
        eyebrow = "" if f == "index" else f'<p class="eyebrow">{html.escape(group)}</p>'
        i = ORDER.index(f)
        prev_ = f'<a class="prev" href="{ORDER[i-1]}.html"><small>← ก่อนหน้า</small>{html.escape(LABEL[ORDER[i-1]])}</a>' if i > 0 else "<span></span>"
        next_ = f'<a class="next" href="{ORDER[i+1]}.html"><small>ถัดไป →</small>{html.escape(LABEL[ORDER[i+1]])}</a>' if i + 1 < len(ORDER) else "<span></span>"
        page = PAGE.format(
            title=html.escape(title),
            desc=html.escape(desc),
            body=body,
            nav=nav_html(f),
            eyebrow=eyebrow,
            pager=f'<nav class="pager" aria-label="หน้าก่อนหน้าและถัดไป">{prev_}{next_}</nav>',
            releases=RELEASES,
        )
        (OUT / f"{f}.html").write_text(page, encoding="utf-8", newline="\n")
        # Search entries: the page, then each section with its text.
        index.append({"u": f"{f}.html", "t": title, "s": LABEL[f], "x": text_of(desc)})
        for m in re.finditer(r'<(h[23])[^>]*id="([^"]+)"[^>]*>(.*?)</\1>(.*?)(?=<h[23][ >]|$)', body, flags=re.S):
            index.append({"u": f"{f}.html#{m.group(2)}", "t": text_of(m.group(3)), "s": title, "x": text_of(m.group(4))[:600]})
    (OUT / "assets" / "search.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"built {len(ORDER)} pages, {len(index)} search entries")


if __name__ == "__main__":
    build()
