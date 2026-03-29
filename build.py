#!/usr/bin/env python3
"""
Build script for tech-help site.
Takes raw HTML articles from articles_v4/, wraps them in site template,
generates category pages with pagination, index page, sitemap.xml, and robots.txt.

Config-driven: all settings come from config.json.
"""
import os
import re
import json
import math
import shutil
import html
from datetime import datetime
from pathlib import Path

# --- Load config ---
SITE_DIR = Path(__file__).parent
CONFIG_FILE = SITE_DIR / "config.json"

with open(CONFIG_FILE, encoding='utf-8') as f:
    CFG = json.load(f)

# Multi-source article dirs
ARTICLE_DIRS = [
    SITE_DIR / "articles_v4",
]
OUTPUT_DIR = SITE_DIR / "build_v2"
STATIC_DIR = SITE_DIR / "static"

BRAND = CFG.get("brand", "Site")
DOMAIN = CFG.get("domain", "")
SITE_URL = f"https://{DOMAIN}" if DOMAIN else ""
SITE_ICON = CFG.get("icon", "🔧")
SITE_DESC = CFG.get("description", "")
META_TITLE = CFG.get("meta_title", f"{BRAND} — {SITE_DESC}")
META_DESC = CFG.get("meta_description", SITE_DESC)
PER_PAGE = CFG.get("pagination", {}).get("per_page", 30)

BUILD_DATE = datetime.now().strftime("%Y-%m-%d")
MONTH_NAMES = {
    "January": "Январь", "February": "Февраль", "March": "Март",
    "April": "Апрель", "May": "Май", "June": "Июнь",
    "July": "Июль", "August": "Август", "September": "Сентябрь",
    "October": "Октябрь", "November": "Ноябрь", "December": "Декабрь"
}
_raw_month = datetime.now().strftime("%B %Y")
BUILD_DATE_HUMAN = _raw_month
for en, ru in MONTH_NAMES.items():
    BUILD_DATE_HUMAN = BUILD_DATE_HUMAN.replace(en, ru)

# --- Parse metadata from HTML ---
META_RE = re.compile(r'<!--META\s*\n(.*?)\nMETA-->', re.DOTALL)
H2_RE = re.compile(r'<h2[^>]*>(.*?)</h2>', re.IGNORECASE)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


# ============================================================
#  КАТЕГОРИЗАЦИЯ
# ============================================================
def categorize_article(slug, categories):
    """Определяет категорию статьи по ключевым словам в slug."""
    slug_lower = slug.lower()
    for cat in categories:
        for kw in cat.get("keywords", []):
            if kw in slug_lower:
                return cat["slug"]
    return None  # uncategorized


# ============================================================
#  ПАРСИНГ СТАТЕЙ
# ============================================================
def parse_article(filepath, categories):
    """Parse an article HTML file and return metadata + content."""
    try:
        raw = filepath.read_text(encoding='utf-8')
    except:
        try:
            raw = filepath.read_text(encoding='cp1251')
        except:
            return None

    m = META_RE.search(raw)
    if not m:
        return None

    try:
        meta = json.loads(m.group(1).strip())
    except json.JSONDecodeError:
        return None

    title = meta.get('title', '').strip()
    description = meta.get('description', '').strip()
    h1 = meta.get('h1', title).strip()

    if not title:
        return None

    body = META_RE.sub('', raw).strip()
    body = re.sub(r'<p>\s*═+\s*БЛОК\s*\d+:.*?═+\s*</p>', '', body, flags=re.IGNORECASE)

    # TOC
    toc = []
    def add_id_to_h2(match):
        text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        slug = slugify(text)
        if not slug:
            slug = f"section-{len(toc)}"
        toc.append({'id': slug, 'text': text})
        return f'<h2 id="{slug}">{match.group(1)}</h2>'

    body = H2_RE.sub(add_id_to_h2, body)

    # Fix outdated years (LLM hallucinated 2024/2025)
    body = body.replace('2024', '2026').replace('2025', '2026')
    title = title.replace('2024', '2026').replace('2025', '2026')
    h1 = h1.replace('2024', '2026').replace('2025', '2026')
    description = description.replace('2024', '2026').replace('2025', '2026')

    body = process_widgets(body)

    article_slug = filepath.stem
    cat_slug = categorize_article(article_slug, categories)

    return {
        'title': title,
        'h1': h1,
        'description': description,
        'slug': article_slug,
        'body': body,
        'toc': toc,
        'category': cat_slug,
    }


def process_widgets(html_content):
    """Convert <!--WIDGET:...--> comments to actual HTML."""
    def replace_checklist(m):
        title = m.group(1)
        items = m.group(2).split('|')
        items_html = ''.join(f'<label class="check-item"><input type="checkbox"><span>{item.strip()}</span></label>' for item in items)
        return f'<div class="checklist-block"><h4>☑️ {title}</h4>{items_html}<div class="check-progress">Выполнено: <span class="check-count">0</span> / {len(items)}</div></div>'

    html_content = re.sub(r'<!--WIDGET:checklist:(.*?):(.*?)-->', replace_checklist, html_content)

    def replace_spoiler(m):
        title = m.group(1)
        content = m.group(2)
        return f'<details class="faq-item"><summary>{title}</summary><div class="faq-answer"><p>{content}</p></div></details>'

    html_content = re.sub(r'<!--WIDGET:spoiler:(.*?):(.*?)-->', replace_spoiler, html_content, flags=re.DOTALL)

    def replace_keypoint(m):
        return f'<div class="attention-box attention-tip"><span class="attention-icon">💡</span><p>{m.group(1)}</p></div>'
    html_content = re.sub(r'<!--WIDGET:keypoint:(.*?)-->', replace_keypoint, html_content)

    def replace_tip(m):
        return f'<div class="attention-box attention-tip"><span class="attention-icon">💡</span><p>{m.group(1)}</p></div>'
    html_content = re.sub(r'<!--WIDGET:tip:(.*?)-->', replace_tip, html_content)

    def replace_poll(m):
        question = m.group(1)
        options = m.group(2).split('|')
        opts_html = ''.join(f'<li>{opt.strip()}</li>' for opt in options)
        return f'<div class="attention-box attention-info"><div><strong>📊 {question}</strong><ul>{opts_html}</ul></div></div>'
    html_content = re.sub(r'<!--WIDGET:poll:(.*?):(.*?)-->', replace_poll, html_content)

    return html_content


# ============================================================
#  NAV HTML (shared)
# ============================================================
def nav_links_html(categories, active_slug=None):
    """Generate nav links for categories."""
    links = []
    for cat in categories[:6]:  # Show top 6 in nav
        is_active = ' active' if cat['slug'] == active_slug else ''
        links.append(f'<a href="/category/{cat["slug"]}/" class="nav-link{is_active}">{cat["icon"]} {cat["name"]}</a>')
    return '\n'.join(links)


def header_html(categories, active_slug=None):
    return f'''<header class="site-header">
        <div class="container header-inner">
            <a href="/" class="logo">
                <span class="logo-icon">{SITE_ICON}</span>
                <span>{BRAND}</span>
            </a>
            <button class="mobile-menu-btn" aria-label="Меню" id="menuBtn">☰</button>
            <nav class="main-nav" id="mainNav">
                {nav_links_html(categories, active_slug)}
            </nav>
        </div>
    </header>'''


def footer_html(categories):
    year = datetime.now().year
    cat_links = '\n'.join(
        f'<li><a href="/category/{c["slug"]}/">{c["icon"]} {c["name"]}</a></li>'
        for c in categories[:6]
    )
    return f'''<footer class="site-footer-premium">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-col">
                    <div class="footer-brand">{SITE_ICON} {BRAND}</div>
                    <p class="footer-about">{SITE_DESC}</p>
                </div>
                <div class="footer-col">
                    <h4>Разделы</h4>
                    <ul>{cat_links}</ul>
                </div>
                <div class="footer-col">
                    <h4>Информация</h4>
                    <ul>
                        <li><a href="/">Главная</a></li>
                        <li><a href="/about.html">О проекте</a></li>
                        <li><a href="/contact.html">Контакты</a></li>
                        <li><a href="/privacy.html">Конфиденциальность</a></li>
                        <li><a href="/sitemap.xml">Карта сайта</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>© {year} {BRAND}. Все права защищены.</p>
            </div>
        </div>
    </footer>
    <div id="cookie-consent" class="cookie-popup">
        <div class="cookie-inner">
            <span>🍪 Мы используем файлы cookie для улучшения работы сайта.</span>
            <button id="cookie-accept" class="cookie-btn">Принять</button>
        </div>
    </div>'''


FOOTER_CSS = '''
    .site-footer-premium {
        margin-top: 60px; padding: 40px 0 0; background: #1e293b; color: #94a3b8;
    }
    .footer-grid {
        display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 40px;
        padding-bottom: 32px; border-bottom: 1px solid #334155;
    }
    .footer-brand { font-size: 1.2rem; font-weight: 700; color: #f1f5f9; margin-bottom: 12px; }
    .footer-about { font-size: 0.9rem; line-height: 1.6; margin-bottom: 8px; }
    .footer-updated { font-size: 0.8rem; color: #64748b; }
    .footer-col h4 { color: #f1f5f9; font-size: 0.95rem; margin-bottom: 16px; }
    .footer-col ul { list-style: none; }
    .footer-col li { margin-bottom: 8px; }
    .footer-col a { color: #94a3b8; font-size: 0.9rem; transition: color 0.2s; }
    .footer-col a:hover { color: #60a5fa; }
    .footer-bottom { padding: 20px 0; text-align: center; font-size: 0.85rem; }
    @media (max-width: 640px) {
        .footer-grid { grid-template-columns: 1fr; gap: 24px; }
    }
    .cookie-popup {
        position: fixed; bottom: -100px; left: 0; right: 0; background: #1e293b; color: #fff;
        padding: 16px; transition: bottom 0.5s ease; z-index: 9999; border-top: 2px solid #2563eb;
    }
    .cookie-popup.visible { bottom: 0; }
    .cookie-inner { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; gap: 16px; font-size: 0.9rem; }
    .cookie-btn { background: #2563eb; color: #fff; border: none; padding: 8px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; white-space: nowrap; }
    .cookie-btn:hover { background: #1d4ed8; }
    @media (max-width: 640px) {
        .cookie-inner { flex-direction: column; text-align: center; }
    }
'''


# ============================================================
#  РЕНДЕР СТРАНИЦЫ СТАТЬИ
# ============================================================
def render_article_page(article, categories, cat_info=None, related_articles=None):
    toc_html = ''
    sidebar_toc = ''
    if article['toc']:
        toc_items = ''.join(f'<li><a href="#{it["id"]}">{it["text"]}</a></li>' for it in article['toc'])
        toc_html = f'<nav class="mobile-toc"><details><summary>📋 Содержание</summary><ul>{toc_items}</ul></details></nav>'
        sidebar_toc = f'<nav class="sidebar-toc" id="sidebarToc"><h3>Содержание</h3><ul>{toc_items}</ul></nav>'

    # Sidebar related (5 items)
    sidebar_related = ''
    if related_articles:
        sidebar_items = related_articles[:5]
        items_html = ''.join(
            f'<li><a href="/{r["slug"]}.html" class="related-card">{html.escape(r["title"])}</a></li>'
            for r in sidebar_items
        )
        sidebar_related = f'<nav class="sidebar-related"><h3>Похожие статьи</h3><ul>{items_html}</ul></nav>'

    # Bottom related (6 items)
    bottom_related = ''
    if related_articles:
        bottom_items = related_articles[:6]
        cards_html = ''.join(
            f'<a href="/{r["slug"]}.html" class="related-bottom-card">'
            f'<span class="related-bottom-title">{html.escape(r["title"])}</span>'
            f'<span class="related-bottom-desc">{html.escape(r.get("description", "")[:100])}</span>'
            f'</a>'
            for r in bottom_items
        )
        bottom_related = f'''<section class="related-bottom">
        <div class="container">
            <h2 class="related-bottom-heading">📖 Читайте также</h2>
            <div class="related-bottom-grid">{cards_html}</div>
        </div>
    </section>'''

    title_esc = html.escape(article['title'])
    desc_esc = html.escape(article['description'])

    # Breadcrumbs
    bc_parts = [f'<a href="/">Главная</a>']
    if cat_info:
        bc_parts.append(f'<span class="breadcrumb-sep">›</span><a href="/category/{cat_info["slug"]}/">{cat_info["name"]}</a>')
    bc_parts.append(f'<span class="breadcrumb-sep">›</span><span class="breadcrumb-current">{title_esc}</span>')
    breadcrumbs = ''.join(bc_parts)

    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_esc} — {BRAND}</title>
    <meta name="description" content="{desc_esc}">
    <link rel="canonical" href="{SITE_URL}/{article['slug']}.html">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title_esc}">
    <meta property="og:description" content="{desc_esc}">
    <meta property="og:locale" content="ru_RU">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
    <style>{FOOTER_CSS}</style>
</head>
<body>
    {header_html(categories)}

    <nav class="breadcrumbs" aria-label="Навигация">
        <div class="container">{breadcrumbs}</div>
    </nav>

    <main class="site-main">
        <div class="container">
            <div class="article-layout">
                <article class="article-main">
                    <h1>{html.escape(article['h1'])}</h1>
                    {toc_html}
                    <div class="article-body">{article['body']}</div>

                </article>
                <aside class="article-sidebar"><nav class="sidebar-search"><div class="sidebar-search-box"><input type="text" id="globalSearchInput" placeholder="🔍 Поиск статей..." autocomplete="off"><div class="search-dropdown" id="globalSearchDropdown"></div></div></nav>{sidebar_toc}{sidebar_related}</aside>
            </div>
        </div>
    </main>

    {bottom_related}

    {footer_html(categories)}
    <script src="/static/js/main.js"></script>
    <script>
        (function() {{
            const popup = document.getElementById('cookie-consent');
            const btn = document.getElementById('cookie-accept');
            if (popup && btn && !localStorage.getItem('cookie-accepted')) {{
                popup.classList.add('visible');
                btn.onclick = () => {{
                    localStorage.setItem('cookie-accepted', 'true');
                    popup.classList.remove('visible');
                }};
            }}
        }})();
    </script>
</body>
</html>'''


# ============================================================
#  РЕНДЕР СТРАНИЦЫ КАТЕГОРИИ
# ============================================================
def render_category_page(cat_info, articles, page, total_pages, categories, total_in_cat=0):
    title = f'{cat_info["name"]} — {BRAND}'
    if page > 1:
        title = f'{cat_info["name"]} — страница {page} — {BRAND}'

    cards = ''
    for i, a in enumerate(articles):
        desc_short = html.escape(a['description'][:120]) if a['description'] else ''
        # Estimate read time from body length
        body_len = len(a.get('body', ''))
        read_min = max(2, body_len // 1200)
        cards += f'''
            <a href="/{a['slug']}.html" class="article-home-card">
                <div class="card-top">
                    <span class="card-icon">{cat_info['icon']}</span>
                    <span class="card-read-time">⏱ {read_min} мин</span>
                </div>
                <div class="article-home-title">{html.escape(a['title'])}</div>
                <div class="article-home-desc">{desc_short}</div>
                <div class="card-footer">
                    <span class="card-read-more">Читать →</span>
                </div>
            </a>'''

    # Pagination
    pag = ''
    if total_pages > 1:
        pag = '<nav class="pagination" aria-label="Страницы">'
        base = f'/category/{cat_info["slug"]}'
        # First page
        if page > 2:
            pag += f'<a href="{base}/" class="pag-link pag-edge" title="В начало">«</a>'
        if page > 1:
            prev_url = f'{base}/' if page == 2 else f'{base}/page/{page-1}/'
            pag += f'<a href="{prev_url}" class="pag-link">← Назад</a>'

        # Page numbers
        for p in range(1, total_pages + 1):
            if abs(p - page) > 3 and p != 1 and p != total_pages:
                if abs(p - page) == 4:
                    pag += '<span class="pag-dots">…</span>'
                continue
            url = f'{base}/' if p == 1 else f'{base}/page/{p}/'
            cls = ' pag-active' if p == page else ''
            pag += f'<a href="{url}" class="pag-link{cls}">{p}</a>'

        if page < total_pages:
            pag += f'<a href="{base}/page/{page+1}/" class="pag-link">Далее →</a>'
        if page < total_pages - 1:
            pag += f'<a href="{base}/page/{total_pages}/" class="pag-link pag-edge" title="В конец">»</a>'
        pag += '</nav>'

    # Benefits per category
    CATEGORY_BENEFITS = {
        'televizory': [('⚡', 'Пошаговые инструкции'), ('🔧', 'Все марки ТВ'), ('✅', 'Проверено экспертами')],
        'android':    [('⚡', 'Быстрые решения'), ('🛡️', 'Безопасные методы'), ('📋', 'Пошаговые гайды')],
        'prilozheniya': [('📥', 'Установка и настройка'), ('🐛', 'Устранение ошибок'), ('🔄', 'Обновления')],
        'windows':    [('💡', 'Простые инструкции'), ('🛠️', 'Диагностика проблем'), ('🚀', 'Оптимизация ПК')],
        'pristavki':  [('📡', 'Все операторы'), ('⚙️', 'Настройка каналов'), ('🔑', 'Коды активации')],
        'internet':   [('📶', 'Усиление сигнала'), ('🔒', 'Безопасность сети'), ('⚡', 'Повышение скорости')],
        'kinoteatry': [('🎥', 'Все сервисы'), ('💰', 'Бесплатные способы'), ('📱', 'Для всех устройств')],
        'pulti':      [('🔋', 'Коды устройств'), ('📖', 'Инструкции настройки'), ('🔄', 'Сброс и ремонт')],
        'iptv':       [('📺', 'Бесплатные плейлисты'), ('📲', 'Smart TV приложения'), ('⚙️', 'Простая настройка')],
        'audio':      [('🎵', 'Настройка звука'), ('🔊', 'Подключение колонок'), ('🎧', 'Bluetooth-устройства')],
        'drugoe':     [('📖', 'Понятные инструкции'), ('✅', 'Проверенные решения'), ('⚡', 'Без лишних слов')],
    }
    benefits = CATEGORY_BENEFITS.get(cat_info['slug'], CATEGORY_BENEFITS['drugoe'])
    benefits_html = '<div class="cat-benefits">' + ''.join(
        f'<div class="cat-benefit"><span class="benefit-icon">{icon}</span><span>{text}</span></div>'
        for icon, text in benefits
    ) + '</div>'
    page_indicator = f' · страница {page} из {total_pages}' if page > 1 else ''

    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <meta name="description" content="{html.escape(cat_info['description'])}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
    <style>
        .cat-hero {{
            background: linear-gradient(135deg, #1e293b 0%, #334155 50%, #1e3a5f 100%);
            border-bottom: none;
            padding: 48px 0 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .cat-hero::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 30% 40%, rgba(37,99,235,0.15) 0%, transparent 50%),
                        radial-gradient(circle at 70% 60%, rgba(139,92,246,0.1) 0%, transparent 50%);
            animation: heroShimmer 8s ease-in-out infinite alternate;
        }}
        @keyframes heroShimmer {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(3deg); }}
        }}
        .cat-hero .container {{ position: relative; z-index: 1; }}
        .cat-hero-icon {{
            font-size: 3.5rem; display: block; margin-bottom: 16px;
            filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3));
        }}
        .cat-hero h1 {{
            font-size: 2rem; font-weight: 800; color: #f1f5f9;
            margin-bottom: 10px; letter-spacing: -0.02em;
        }}
        .cat-hero p {{
            color: #94a3b8; font-size: 1.05rem; max-width: 600px;
            margin: 0 auto; line-height: 1.6;
        }}
        .cat-benefits {{
            display: flex; justify-content: center; gap: 12px;
            margin-top: 24px; flex-wrap: wrap;
        }}
        .cat-benefit {{
            display: flex; align-items: center; gap: 8px;
            background: rgba(255,255,255,0.08); backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 10px; padding: 8px 18px;
            font-size: 0.88rem; color: #e2e8f0; font-weight: 500;
            transition: all 0.25s;
        }}
        .cat-benefit:hover {{
            background: rgba(255,255,255,0.15);
            border-color: rgba(255,255,255,0.25);
            transform: translateY(-2px);
        }}
        .benefit-icon {{ font-size: 1.15em; }}

        .cat-grid {{
            display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 16px; padding: 32px 0 24px;
        }}
        .article-home-card {{
            background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
            padding: 0; text-decoration: none; color: #1e293b;
            transition: all 0.25s ease; display: flex; flex-direction: column;
            overflow: hidden; position: relative;
        }}
        .article-home-card:hover {{
            border-color: #bfdbfe;
            box-shadow: 0 8px 24px rgba(37,99,235,0.1);
            transform: translateY(-4px);
        }}
        .card-top {{
            display: flex; justify-content: space-between; align-items: center;
            padding: 14px 20px 0;
        }}
        .card-icon {{
            font-size: 1.4em;
            background: linear-gradient(135deg, #eff6ff, #e0f2fe);
            width: 36px; height: 36px; border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 2px 6px rgba(37,99,235,0.1);
        }}
        .card-read-time {{
            font-size: 0.78rem; color: #94a3b8; font-weight: 500;
        }}
        .article-home-title {{
            font-weight: 600; font-size: 0.97rem; line-height: 1.4;
            padding: 12px 20px 0; transition: color 0.2s;
        }}
        .article-home-card:hover .article-home-title {{ color: #2563eb; }}
        .article-home-desc {{
            font-size: 0.84rem; color: #64748b; line-height: 1.5;
            padding: 6px 20px 0; flex: 1;
        }}
        .card-footer {{
            display: flex; justify-content: flex-end; align-items: center;
            padding: 12px 20px; margin-top: auto;
            border-top: 1px solid #f1f5f9;
        }}
        .card-read-more {{
            font-size: 0.82rem; font-weight: 600; color: #94a3b8;
            transition: all 0.2s;
        }}
        .article-home-card:hover .card-read-more {{
            color: #2563eb; letter-spacing: 0.02em;
        }}

        .pagination {{
            display: flex; justify-content: center; gap: 6px;
            padding: 8px 0 48px; flex-wrap: wrap; align-items: center;
        }}
        .pag-link {{
            padding: 10px 16px; border-radius: 10px; border: 1px solid #e2e8f0;
            color: #64748b; font-size: 0.9rem; text-decoration: none;
            transition: all 0.2s; font-weight: 500;
        }}
        .pag-link:hover {{ border-color: #2563eb; color: #2563eb; background: #eff6ff; }}
        .pag-active {{
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            color: #fff !important; border-color: #2563eb;
            box-shadow: 0 3px 10px rgba(37,99,235,0.3);
        }}
        .pag-edge {{ font-size: 1rem; font-weight: 700; }}
        .pag-dots {{ color: #94a3b8; padding: 0 4px; }}

        {FOOTER_CSS}
        @media (max-width: 640px) {{
            .cat-grid {{ grid-template-columns: 1fr; }}
            .cat-hero h1 {{ font-size: 1.5rem; }}
        }}
    </style>
</head>
<body>
    {header_html(categories, cat_info['slug'])}

    <nav class="breadcrumbs" aria-label="Навигация">
        <div class="container">
            <a href="/">Главная</a>
            <span class="breadcrumb-sep">›</span>
            <span class="breadcrumb-current">{html.escape(cat_info['name'])}</span>
        </div>
    </nav>

    <section class="cat-hero">
        <div class="container">
            <span class="cat-hero-icon">{cat_info['icon']}</span>
            <h1>{html.escape(cat_info['name'])}</h1>
            <p>{html.escape(cat_info['description'])}{page_indicator}</p>
            {benefits_html}
        </div>
    </section>

    <main class="site-main">
        <div class="container">
            <div class="cat-grid">{cards}</div>
            {pag}
        </div>
    </main>

    {footer_html(categories)}
    <script>
    (function() {{
        document.getElementById('menuBtn')?.addEventListener('click', () => {{
            document.getElementById('mainNav')?.classList.toggle('open');
        }});
        
        const popup = document.getElementById('cookie-consent');
        const btn = document.getElementById('cookie-accept');
        if (popup && btn && !localStorage.getItem('cookie-accepted')) {{
            popup.classList.add('visible');
            btn.onclick = () => {{
                localStorage.setItem('cookie-accepted', 'true');
                popup.classList.remove('visible');
            }};
        }}
    }})();
    </script>
</body>
</html>'''


# ============================================================
#  SITEMAP & ROBOTS
# ============================================================
def generate_sitemap(articles, cat_pages):
    urls = [f'  <url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>']
    for cp in cat_pages:
        urls.append(f'  <url><loc>{SITE_URL}{cp}</loc><priority>0.8</priority></url>')
    for a in articles:
        urls.append(f'  <url><loc>{SITE_URL}/{a["slug"]}.html</loc><lastmod>{BUILD_DATE}</lastmod></url>')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''


def generate_robots():
    return f'''User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml'''


# ============================================================
#  MAIN
# ============================================================
def main():
    categories = CFG.get("categories", [])
    uncat = CFG.get("uncategorized", {"slug": "drugoe", "name": "Другое", "icon": "📁", "description": "Прочие статьи"})

    print(f"🔧 Building {BRAND}...")
    print(f"📂 Article dirs: {[d.name for d in ARTICLE_DIRS if d.exists()]}")
    print(f"📦 Categories: {len(categories)}")

    # Clean output (preserve static + index.html + about.html + contact.html + privacy.html)
    for item in OUTPUT_DIR.glob("*"):
        if item.name in ("static", "index.html", "about.html", "contact.html", "privacy.html"):
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Copy static files if not present
    out_static = OUTPUT_DIR / "static"
    if not out_static.exists():
        shutil.copytree(STATIC_DIR, out_static)
        print(f"📁 Copied static files")
    else:
        # Update CSS
        src_css = STATIC_DIR / "css" / "style.css"
        dst_css = out_static / "css" / "style.css"
        if src_css.exists():
            shutil.copy2(src_css, dst_css)

    # Parse all articles from all dirs
    articles = []
    errors = 0
    seen_slugs = set()

    for d in ARTICLE_DIRS:
        if not d.exists():
            continue
        html_files = sorted(d.glob("*.html"))
        for i, f in enumerate(html_files):
            if f.stem in seen_slugs:
                continue
            result = parse_article(f, categories)
            if result:
                articles.append(result)
                seen_slugs.add(f.stem)
            else:
                errors += 1

    print(f"✅ Parsed {len(articles)} articles ({errors} skipped)")

    # ============================================================
    #  SCHEDULED PUBLISHING
    # ============================================================
    from datetime import timedelta
    SCHEDULE_FILE = SITE_DIR / "publish_schedule.json"
    PUBLISH_START = datetime(2026, 3, 29)  # Start scheduling from tomorrow
    IMMEDIATE_COUNT = max(0, len(articles) - 730)  # Publish most immediately

    if SCHEDULE_FILE.exists():
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            schedule = json.load(f)
        print(f"📅 Loaded publish schedule ({len(schedule)} entries)")
    else:
        # Generate schedule: first IMMEDIATE_COUNT get today's date,
        # remaining 730 get spread over 2 years (730 days)
        import random as _rnd
        _rnd.seed(42)  # Deterministic shuffle
        shuffled_slugs = [a['slug'] for a in articles]
        _rnd.shuffle(shuffled_slugs)

        schedule = {}
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Immediate batch
        for slug in shuffled_slugs[:IMMEDIATE_COUNT]:
            schedule[slug] = today_str

        # Scheduled batch — spread over 730 days (0-2 per day)
        scheduled_slugs = shuffled_slugs[IMMEDIATE_COUNT:]
        day_offset = 0
        idx = 0
        _rnd.seed(123)
        while idx < len(scheduled_slugs):
            # 0-2 articles per day (weighted: 30% 0, 40% 1, 30% 2)
            r = _rnd.random()
            if r < 0.30:
                count = 0
            elif r < 0.70:
                count = 1
            else:
                count = 2
            pub_date = (PUBLISH_START + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            for _ in range(count):
                if idx >= len(scheduled_slugs):
                    break
                schedule[scheduled_slugs[idx]] = pub_date
                idx += 1
            day_offset += 1

        # Save schedule
        with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
            json.dump(schedule, f, ensure_ascii=False, indent=2)
        print(f"📅 Created new publish schedule: {IMMEDIATE_COUNT} immediate + {len(scheduled_slugs)} scheduled")

    # Determine published articles
    today_str = datetime.now().strftime("%Y-%m-%d")
    published_slugs = set()
    scheduled_count = 0
    for slug, pub_date in schedule.items():
        if pub_date <= today_str:
            published_slugs.add(slug)
        else:
            scheduled_count += 1

    # Handle new articles not in schedule (publish immediately)
    for a in articles:
        if a['slug'] not in schedule:
            published_slugs.add(a['slug'])

    all_articles = articles
    published_articles = [a for a in articles if a['slug'] in published_slugs]
    print(f"📢 Published: {len(published_articles)} | 🕐 Scheduled: {scheduled_count}")

    # Categorize (only published articles for categories/related)
    cat_articles = {}
    for cat in categories:
        cat_articles[cat['slug']] = []
    cat_articles[uncat['slug']] = []

    for a in published_articles:
        cat_slug = a.get('category') or uncat['slug']
        if cat_slug not in cat_articles:
            cat_slug = uncat['slug']
        cat_articles[cat_slug].append(a)

    print(f"\n📊 Распределение по категориям (опубликованные):")
    for cat in categories:
        count = len(cat_articles[cat['slug']])
        if count > 0:
            print(f"  {cat['icon']} {cat['name']}: {count}")
    uncat_count = len(cat_articles[uncat['slug']])
    print(f"  {uncat['icon']} {uncat['name']}: {uncat_count}")

    # Build article pages (flat: /slug.html) — ALL articles (including scheduled)
    all_cats_map = {c['slug']: c for c in categories}
    all_cats_map[uncat['slug']] = uncat

    # Pre-build related index by category
    import random
    for i, article in enumerate(all_articles):
        if (i + 1) % 1000 == 0:
            print(f"  🏗️  Built {i+1}/{len(all_articles)}...")

        cat_slug = article.get('category') or uncat['slug']
        cat_info = all_cats_map.get(cat_slug, uncat)

        # Find related articles from same category (excluding self, only PUBLISHED)
        same_cat = [a for a in cat_articles.get(cat_slug, []) if a['slug'] != article['slug']]
        related = random.sample(same_cat, min(6, len(same_cat))) if same_cat else []

        page_html = render_article_page(article, categories, cat_info, related)
        out_file = OUTPUT_DIR / f"{article['slug']}.html"
        out_file.write_text(page_html, encoding='utf-8')

    print(f"🏗️  Built {len(all_articles)} article pages")

    # Build category pages with pagination (only published)
    cat_page_urls = []
    all_cat_list = categories + [uncat]

    for cat in all_cat_list:
        arts = cat_articles.get(cat['slug'], [])
        if not arts:
            continue

        total_pages = math.ceil(len(arts) / PER_PAGE)
        cat_dir = OUTPUT_DIR / "category" / cat['slug']
        cat_dir.mkdir(parents=True, exist_ok=True)

        for page in range(1, total_pages + 1):
            start = (page - 1) * PER_PAGE
            page_arts = arts[start:start + PER_PAGE]

            page_html = render_category_page(cat, page_arts, page, total_pages, categories, len(arts))

            if page == 1:
                (cat_dir / "index.html").write_text(page_html, encoding='utf-8')
                cat_page_urls.append(f"/category/{cat['slug']}/")
            else:
                page_dir = cat_dir / "page" / str(page)
                page_dir.mkdir(parents=True, exist_ok=True)
                (page_dir / "index.html").write_text(page_html, encoding='utf-8')
                cat_page_urls.append(f"/category/{cat['slug']}/page/{page}/")

    print(f"📂 Built {len(cat_page_urls)} category pages")

    # popular_articles.json pool (6 from each category, only published)
    popular_pool = []
    for cat in all_cat_list:
        arts = cat_articles.get(cat['slug'], [])
        if arts:
            for a in arts[:10]:
                popular_pool.append({
                    "title": a["title"],
                    "slug": a["slug"],
                    "desc": a["description"][:120] + "...",
                    "cat": cat["name"],
                    "icon": cat["icon"]
                })
    
    popular_file = OUTPUT_DIR / "static" / "js" / "popular_articles.json"
    popular_file.parent.mkdir(parents=True, exist_ok=True)
    with open(popular_file, 'w', encoding='utf-8') as f:
        json.dump(popular_pool, f, ensure_ascii=False, indent=2)
    print(f"🔥 Generated popular articles pool ({len(popular_pool)} items)")

    # Search index (title + slug, only published)
    search_index = []
    for a in published_articles:
        cat_slug = a.get('category') or uncat['slug']
        cat_info = all_cats_map.get(cat_slug, uncat)
        search_index.append({
            "s": a["slug"],
            "t": a["title"],
            "i": cat_info["icon"]
        })
    search_file = OUTPUT_DIR / "static" / "js" / "search-index.json"
    with open(search_file, 'w', encoding='utf-8') as f:
        json.dump(search_index, f, ensure_ascii=False)
    print(f"🔍 Generated search index ({len(search_index)} articles)")

    # NOTE: index.html is maintained manually in build_v2/ — don't overwrite it

    # Sitemap + Robots (only published articles!)
    (OUTPUT_DIR / "sitemap.xml").write_text(generate_sitemap(published_articles, cat_page_urls), encoding='utf-8')
    (OUTPUT_DIR / "robots.txt").write_text(generate_robots(), encoding='utf-8')
    print(f"🗺️  Generated sitemap.xml ({len(published_articles) + len(cat_page_urls)} URLs)")
    print(f"🤖 Generated robots.txt")

    print(f"\n✨ Build complete! {len(all_articles)} articles ({len(published_articles)} published + {scheduled_count} scheduled) + {len(cat_page_urls)} category pages")
    print(f"🚀 Run: python -m http.server 8080 -d {OUTPUT_DIR}")


if __name__ == '__main__':
    main()

