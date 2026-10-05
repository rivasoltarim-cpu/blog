#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rivasol llms.txt / llms-full.txt üretici.
RSS akışından blog yazılarını çekip iki dosya üretir:
  - llms.txt       : site özeti + ana sayfalar + son yazılar (kısa)
  - llms-full.txt  : tüm yazılar (başlık, tarih, link, kısa özet)
Çıktılar `public/` klasörüne yazılır; siteye kök dizine (/llms.txt) yüklenmelidir.
"""

import html
import re
import sys
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path

import feedparser

SITE = "https://www.rivasol.com.tr"
FEED_URL = f"{SITE}/blog-feed.xml"
USER_AGENT = "Mozilla/5.0 (compatible; RivasolBlogBot/1.0; +https://github.com)"
OUT_DIR = Path("public")
LATEST_COUNT = 30
SUMMARY_MAX = 220

SUMMARY = (
    "Rivasol, Kırmızı Kaliforniya Solucanı (Eisenia fetida) ile organik katı ve sıvı "
    "solucan gübresi üreten, Edirne Keşan merkezli bir tarım markasıdır. Katı ve sıvı "
    "solucan gübresi, humik asit, Kırmızı Kaliforniya solucanı, üretim paketleri, "
    "makine-teçhizat ve solucan gübresi üretimi için hibe/destek bilgileri sunar."
)

CONTACT = [
    "Telefon: +90 507 248 9125",
    "Adres: Rasim Ergene Cad. Mustafa Kemal Paşa Mah. No:85/A Keşan / EDİRNE",
]

SECTIONS = {
    "Ürün kategorileri": [
        ("Tüm ürünler", "/tum-urunler"),
        ("Katı solucan gübresi", "/kati-solucan-gubresi"),
        ("Sıvı solucan gübresi", "/sivi-solucan-gubresi"),
        ("Humik asit", "/humik-asit"),
        ("Kırmızı Kaliforniya solucanı", "/kirmizi-kaliforniya-solucani"),
        ("Solucan maması", "/solucan-mamasi"),
        ("Kombin ürünler", "/kombin-urunler"),
        ("Kampanyalı ürünler", "/kampanyali-urunler"),
    ],
    "Üretim ve girişimcilik": [
        ("Hobi amaçlı üretim paketleri", "/hobi-amacli-uretim-paketleri"),
        ("Ticari amaçlı üretim paketleri", "/ticari-amacli-uretim-paketleri"),
        ("Solucan gübresi üretim kasaları", "/solucan-gubresi-uretim-kasalari"),
        ("Makine ve teçhizatlar", "/makine-ve-techizatlar"),
        ("Solucan gübresi üretimi hibe/destek projeleri", "/solucan-gubresi-uretimi-hibe-destek-projeleri"),
        ("Solucan gübresi üreticisi olun", "/solucan-gubresi-ureticisi-olun-ve-kazanmaya-baslayin"),
    ],
    "Kurumsal": [
        ("Hakkımızda", "/hakkimizda"),
        ("Analizler", "/analizler"),
        ("Lisanslar ve tescil belgeleri", "/lisanslar-ve-tesciller"),
        ("Sıkça sorulan sorular", "/sikca-sorulan-sorular"),
        ("Ödeme ve teslimat", "/odeme-ve-teslimat"),
        ("Garanti ve iade koşulları", "/garanti-ve-iade-kosullari"),
        ("İletişim", "/iletisim"),
    ],
}


def fetch_posts():
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        feed = feedparser.parse(resp.read())
    posts = []
    for entry in feed.entries:
        try:
            date = parsedate_to_datetime(entry.get("published", "")).strftime("%Y-%m-%d")
        except Exception:
            date = ""
        posts.append({
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", "").strip(),
            "date": date,
            "summary": clean_summary(entry.get("summary", "")),
        })
    return posts


def clean_summary(raw):
    """RSS açıklamasından görsel/etiketleri atıp ilk anlamlı cümleleri döndür."""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    text = re.sub(r"\s*(Read More|Devamını oku)\s*$", "", text, flags=re.I)
    if re.search(r"\.\.+$", text):  # RSS özeti kelime ortasında kesilmiş
        text = re.sub(r"\.\.+$", "", text).rsplit(" ", 1)[0].strip() + "…"
    if len(text) > SUMMARY_MAX:
        text = text[:SUMMARY_MAX].rsplit(" ", 1)[0] + "…"
    return text


def header_lines():
    lines = ["# Rivasol", "", f"> {SUMMARY}", "", *CONTACT, f"Web sitesi: {SITE}", ""]
    for title, items in SECTIONS.items():
        lines += [f"## {title}", ""]
        lines += [f"- [{name}]({SITE}{path})" for name, path in items]
        lines.append("")
    return lines


def build_llms(posts):
    lines = header_lines()
    lines += ["## Blog (son yazılar)", ""]
    for p in posts[:LATEST_COUNT]:
        lines.append(f"- [{p['title']}]({p['link']}): {p['date']}")
    lines += [
        "",
        "## Optional",
        "",
        f"- [Tüm blog yazıları (ayrıntılı)]({SITE}/llms-full.txt)",
        f"- [Blog RSS akışı]({FEED_URL})",
        f"- [Site haritası]({SITE}/sitemap.xml)",
        "",
    ]
    return "\n".join(lines)


def build_llms_full(posts):
    lines = header_lines()
    lines += [f"## Blog yazıları ({len(posts)})", ""]
    for p in posts:
        entry = f"- [{p['title']}]({p['link']}) ({p['date']})"
        if p["summary"]:
            entry += f": {p['summary']}"
        lines.append(entry)
    lines.append("")
    return "\n".join(lines)


def main():
    posts = fetch_posts()
    if not posts:
        print("Feed boş, dosyalar üretilmedi")
        sys.exit(0)
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "llms.txt").write_text(build_llms(posts), encoding="utf-8", newline="\n")
    (OUT_DIR / "llms-full.txt").write_text(build_llms_full(posts), encoding="utf-8", newline="\n")
    print(f"{len(posts)} yazı işlendi -> {OUT_DIR}/llms.txt, {OUT_DIR}/llms-full.txt")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
