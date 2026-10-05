#!/usr/bin/env python3 
# -*- coding: utf-8 -*-
"""
Rivasol Blog RSS Otomasyonu
Bu script, Rivasol blog'undan son yazıları çeker ve README.md'ye ekler
"""

import feedparser
import sys
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from datetime import datetime

# Blog RSS Feed URL
RSS_FEED_URL = "https://www.rivasol.com.tr/blog-feed.xml"
USER_AGENT = "Mozilla/5.0 (compatible; RivasolBlogBot/1.0; +https://github.com)"


def read_readme():
    """README.md dosyasını oku"""
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
            print("✅ README.md dosyası okundu")
            return content
    except FileNotFoundError:
        print("❌ README.md dosyası bulunamadı!")
        return ""
    except Exception as e:
        print(f"❌ Dosya okuma hatası: {e}")
        return ""


def write_readme(content):
    """README.md dosyasını yaz"""
    try:
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ README.md dosyası yazıldı")
        return True
    except Exception as e:
        print(f"❌ Dosya yazma hatası: {e}")
        return False


def fetch_blog_posts(limit=None):
    """
    RSS Feed'den blog yazılarını çek.
    limit=None -> tümünü getir
    limit=N    -> ilk N yazıyı getir
    """
    print(f"🔍 RSS Feed çekiliyor: {RSS_FEED_URL}")
    
    try:
        req = urllib.request.Request(RSS_FEED_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            feed = feedparser.parse(resp.read())
        
        # Feed kontrolü
        if feed.bozo:
            print(f"⚠️ RSS Feed parse hatası: {feed.bozo_exception}")
            # Yine de devam et, bazı feed'ler bozo olsa da çalışır
        
        if not feed.entries:
            print("❌ RSS Feed'de yazı bulunamadı!")
            return []
        
        print(f"✅ Feed'de toplam {len(feed.entries)} blog yazısı bulundu")
        
        # Limit uygulanacaksa burada uygula
        entries = feed.entries
        if limit is not None:
            entries = entries[:limit]
            print(f"➡️ İşlenecek yazı sayısı: {len(entries)} (limit={limit})")
        else:
            print(f"➡️ İşlenecek yazı sayısı: {len(entries)} (tümü)")
        
        posts = []
        for entry in entries:
            # Başlık temizleme
            title = entry.get('title', 'Başlıksız Yazı').strip()
            
            # Link al
            link = entry.get('link', '#')
            
            # Tarih parse et
            published = entry.get('published', '')
            if published:
                try:
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(published)
                    published_str = dt.strftime('%d %B %Y')
                except Exception:
                    published_str = published
            else:
                published_str = 'Tarih belirtilmemiş'
            
            post = {
                'title': title,
                'link': link,
                'published': published_str
            }
            posts.append(post)
            print(f"  📝 {title}")
        
        return posts
        
    except Exception as e:
        print(f"❌ RSS Feed çekme hatası: {e}")
        import traceback
        traceback.print_exc()
        return []


def format_posts_as_markdown(posts):
    """Blog yazılarını Markdown formatına çevir"""
    if not posts:
        return "<!-- BLOG-POST-LIST:START -->\n<!-- Blog yazıları yüklenemedi -->\n<!-- BLOG-POST-LIST:END -->"
    
    markdown = "<!-- BLOG-POST-LIST:START -->\n"
    for post in posts:
        # Emoji ve tarih ile daha güzel görünüm
        markdown += f"- 📌 [{post['title']}]({post['link']}) - *{post['published']}*\n"
    markdown += "<!-- BLOG-POST-LIST:END -->"
    
    return markdown


def update_readme():
    """README'yi güncelle"""
    print("\n" + "=" * 60)
    print("🤖 Rivasol Blog Otomasyonu Başlatıldı")
    print("=" * 60 + "\n")
    
    # README'yi oku
    readme_content = read_readme()
    if not readme_content:
        print("❌ README.md bulunamadı veya okunamadı!")
        sys.exit(1)
    
    # Blog yazılarını çek (TÜMÜ)
    posts = fetch_blog_posts(limit=None)  # <= artık tüm yazılar
    if not posts:
        print("⚠️ Blog yazısı çekilemedi, güncelleme yapılmadı")
        sys.exit(0)
    
    # Yeni blog bölümünü oluştur
    new_blog_section = format_posts_as_markdown(posts)
    
    # START ve END marker'ları
    start_marker = "<!-- BLOG-POST-LIST:START -->"
    end_marker = "<!-- BLOG-POST-LIST:END -->"
    
    # Marker'ları kontrol et
    if start_marker not in readme_content or end_marker not in readme_content:
        print("\n⚠️ README.md'de marker'lar bulunamadı!")
        print("Lütfen README.md dosyanıza şu satırları ekleyin:\n")
        print("## 📝 Son Blog Yazılarım\n")
        print("<!-- BLOG-POST-LIST:START -->")
        print("<!-- Blog yazıları buraya otomatik olarak eklenecek -->")
        print("<!-- BLOG-POST-LIST:END -->\n")
        
        # Yine de README'nin sonuna ekle
        new_content = readme_content + "\n\n## 📝 Son Blog Yazılarım\n\n" + new_blog_section
    else:
        # Mevcut blog bölümünü bul ve değiştir
        start_idx = readme_content.find(start_marker)
        end_idx = readme_content.find(end_marker) + len(end_marker)
        
        old_section = readme_content[start_idx:end_idx]
        
        # Değişiklik kontrolü
        if old_section == new_blog_section:
            print("\n✨ Blog yazıları zaten güncel, değişiklik yok!")
            sys.exit(0)
        
        new_content = (
            readme_content[:start_idx] +
            new_blog_section +
            readme_content[end_idx:]
        )
    
    # README'yi yaz
    if write_readme(new_content):
        print(f"\n✅ README başarıyla güncellendi!")
        print(f"📊 {len(posts)} blog yazısı eklendi")
        print(f"⏰ Güncelleme zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print("\n" + "=" * 60)
    else:
        print("\n❌ README güncellenemedi!")
        sys.exit(1)


if __name__ == "__main__":
    try:
        update_readme()
    except KeyboardInterrupt:
        print("\n\n⚠️ İşlem kullanıcı tarafından iptal edildi")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
