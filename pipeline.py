#!/usr/bin/env python3
"""
🔧 DORI Pipeline — единый скрипт сборки сайта.

Запускает все этапы в правильном порядке:
  1. Аудит статей (META, структура, битые теги)
  2. Очистка фраз-паразитов (clean_filler)
  3. Автофикс типичных HTML-багов
  4. Сборка сайта (build.py)
  5. Итоговый отчёт

Использование:
  python pipeline.py                  # Dry run (проверяет, ничего не меняет)
  python pipeline.py --apply          # Очистка + фикс + сборка
  python pipeline.py --apply --skip-build  # Только очистка и фикс, без сборки
  python pipeline.py --audit-only     # Только аудит без изменений
"""
import os
import re
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# === КОНФИГ ===
SITE_DIR = Path(__file__).parent
ARTICLE_DIRS = [
    SITE_DIR / "articles_v4",
]

BUILD_SCRIPT = SITE_DIR / "build.py"
CLEAN_SCRIPT = SITE_DIR / "clean_filler.py"

# ВСЕ теги, которые LLM генерирует и build.py обрабатывает
# Блочные — проверяем count открытых vs закрытых
BLOCK_TAGS = ['h2', 'h3', 'p', 'ul', 'ol', 'li', 'table', 'thead', 'tbody',
              'tr', 'th', 'td', 'blockquote', 'details', 'summary', 'pre']
# Инлайн — тоже проверяем
INLINE_TAGS = ['strong', 'em', 'mark', 'code']
# Все теги для проверки
ALL_TAGS = BLOCK_TAGS + INLINE_TAGS
# Теги, для которых проверяем перепутанные закрытия (<h2>...</p> и т.д.)
CROSS_CHECK = [
    ('h2', 'p'), ('h3', 'p'),        # заголовки закрытые как абзацы
    ('ul', 'ol'), ('ol', 'ul'),       # перепутанные списки
    ('td', 'th'), ('th', 'td'),       # перепутанные ячейки таблиц
    ('strong', 'em'), ('em', 'strong'),  # перепутанные инлайн
]


def print_header(title):
    w = 60
    print()
    print("=" * w)
    print(f"  {title}")
    print("=" * w)


def print_step(n, title):
    print(f"\n{'─'*50}")
    print(f"  ШАГ {n}: {title}")
    print(f"{'─'*50}")


# ============================================================
#  ШАГ 1: АУДИТ
# ============================================================
def audit_articles():
    """Полный аудит всех статей: META, структура, битые теги."""
    results = {
        'total': 0,
        'no_meta': 0,
        'no_meta_files': [],
        'low_h2': 0,
        'low_p': 0,
        'no_table': 0,
        'no_faq': 0,
        'no_widgets': 0,
        'bad_tags': 0,
        'bad_tags_files': [],
        'has_doctype': 0,
        'has_class': 0,
        'has_blok': 0,
        'no_blok': 0,
        'dirs': {},
    }

    for d in ARTICLE_DIRS:
        if not d.exists():
            continue

        files = sorted(d.glob("*.html"))
        dir_stats = {'total': len(files), 'no_meta': 0, 'bad_tags': 0}

        for i, fp in enumerate(files):
            if (i + 1) % 1000 == 0:
                print(f"    {d.name}: {i+1}/{len(files)}...", flush=True)

            results['total'] += 1

            try:
                text = fp.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            # META check
            meta_match = re.search(r'<!--META\s*\n(.*?)\nMETA-->', text, re.DOTALL)
            if not meta_match:
                results['no_meta'] += 1
                dir_stats['no_meta'] += 1
                if len(results['no_meta_files']) < 10:
                    results['no_meta_files'].append(f"{d.name}/{fp.name}")
                continue

            body = re.sub(r'<!--META.*?META-->', '', text, flags=re.DOTALL).strip()

            # БЛОК marker
            if re.search(r'═+\s*БЛОК', body):
                results['has_blok'] += 1
            else:
                results['no_blok'] += 1

            # Structure
            h2c = len(re.findall(r'<h2', body, re.I))
            pc = len(re.findall(r'<p', body, re.I))
            tc = len(re.findall(r'<table', body, re.I))
            fc = len(re.findall(r'<details', body, re.I))
            wc = len(re.findall(r'<!--WIDGET:', body))

            if h2c < 4: results['low_h2'] += 1
            if pc < 8: results['low_p'] += 1
            if tc < 1: results['no_table'] += 1
            if fc < 1: results['no_faq'] += 1
            if wc < 2: results['no_widgets'] += 1
            if '<!DOCTYPE' in body.upper(): results['has_doctype'] += 1
            if 'class=' in body: results['has_class'] += 1

            # Битые теги: <h2>...</p> и подобные
            bad = check_mismatched_tags(body)
            if bad:
                results['bad_tags'] += 1
                dir_stats['bad_tags'] += 1
                if len(results['bad_tags_files']) < 10:
                    results['bad_tags_files'].append(
                        f"{d.name}/{fp.name} [{', '.join(bad[:3])}]"
                    )

        results['dirs'][d.name] = dir_stats

    return results


def check_mismatched_tags(html):
    """Проверяет ВСЕ теги: count мисматч + перепутанные закрытия."""
    issues = []

    # 1. Count: открытых ≠ закрытых
    for tag in ALL_TAGS:
        open_count = len(re.findall(f'<{tag}[\\s>/]', html, re.I))
        close_count = len(re.findall(f'</{tag}>', html, re.I))
        if open_count != close_count:
            issues.append(f"<{tag}> {open_count}≠{close_count}")

    # 2. Перепутанные закрытия: <open_tag>...</close_tag>
    for open_tag, close_tag in CROSS_CHECK:
        pattern = f'<{open_tag}[^>]*>(.*?)</{close_tag}>'
        for m in re.finditer(pattern, html, re.I | re.DOTALL):
            if f'</{open_tag}>' not in m.group(0):
                issues.append(f"<{open_tag}>...</{close_tag}>")
                break  # одного примера достаточно

    return issues


def print_audit_report(r):
    """Выводит отчёт аудита."""
    t = r['total']
    if t == 0:
        print("  ⚠️  Нет статей для проверки!")
        return

    print(f"\n  📊 Всего файлов: {t}")

    # По папкам
    for name, ds in r['dirs'].items():
        print(f"     {name}: {ds['total']} файлов"
              f" (без META: {ds['no_meta']}, битые теги: {ds['bad_tags']})")

    print(f"\n  {'─'*45}")

    # Критичные
    pct = lambda v: f"{v/t*100:.1f}%" if t else "0%"
    print(f"  ❌ Нет META блока:     {r['no_meta']:5d} ({pct(r['no_meta'])})"
          f"  ← build.py пропустит")
    print(f"  ❌ Битые теги:         {r['bad_tags']:5d} ({pct(r['bad_tags'])})"
          f"  ← нужен фикс")

    # Структура
    print(f"\n  ⚠️  Мало H2 (<4):      {r['low_h2']:5d} ({pct(r['low_h2'])})")
    print(f"  ⚠️  Мало P (<8):       {r['low_p']:5d} ({pct(r['low_p'])})")
    print(f"  ⚠️  Нет таблиц:       {r['no_table']:5d} ({pct(r['no_table'])})")
    print(f"  ⚠️  Нет FAQ:           {r['no_faq']:5d} ({pct(r['no_faq'])})")
    print(f"  ⚠️  Мало виджетов:    {r['no_widgets']:5d} ({pct(r['no_widgets'])})")

    # Мусор
    print(f"\n  🧹 DOCTYPE в body:     {r['has_doctype']:5d}")
    print(f"  🧹 class= в body:     {r['has_class']:5d}")

    # Инфо
    print(f"\n  ℹ️  Есть маркер БЛОК:  {r['has_blok']:5d} ({pct(r['has_blok'])})")
    print(f"  ℹ️  Нет маркера БЛОК:  {r['no_blok']:5d} ({pct(r['no_blok'])})")

    if r['no_meta_files']:
        print(f"\n  Примеры без META:")
        for f in r['no_meta_files'][:5]:
            print(f"    • {f}")

    if r['bad_tags_files']:
        print(f"\n  Примеры с битыми тегами:")
        for f in r['bad_tags_files'][:5]:
            print(f"    • {f}")


# ============================================================
#  ШАГ 2: ОЧИСТКА ФРАЗ-ПАРАЗИТОВ
# ============================================================
def run_clean_filler(apply=False):
    """Запускает clean_filler.py."""
    if not CLEAN_SCRIPT.exists():
        print("  ⚠️  clean_filler.py не найден, пропуск")
        return

    cmd = [sys.executable, str(CLEAN_SCRIPT)]
    if apply:
        cmd.append("--apply")

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run(cmd, cwd=str(SITE_DIR), capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
    # Показываем только итоговые строки
    if result.stdout:
        for line in result.stdout.split('\n'):
            if any(k in line for k in ['ИТОГО', '✅', '📋', '📝', '💡', '⚡', '🔍']):
                print(f"  {line.strip()}")

    if result.returncode != 0 and result.stderr:
        print(f"  ❌ Ошибка: {result.stderr[:200]}")


# ============================================================
#  ШАГ 3: АВТОФИКС HTML-БАГОВ
# ============================================================
def fix_html_issues(apply=False):
    """Исправляет типичные HTML-баги от LLM — ВСЕ типы тегов."""
    fixed_count = 0
    total_fixes = 0

    for d in ARTICLE_DIRS:
        if not d.exists():
            continue

        files = sorted(d.glob("*.html"))
        dir_fixes = 0

        for fp in files:
            try:
                text = fp.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            original = text
            fixes = 0

            # --- Перепутанные закрытия ---
            # Фикс: <h2>...</p> → <h2>...</h2>
            for open_tag, wrong_close in CROSS_CHECK:
                def make_fixer(ot, wc):
                    def fixer(m):
                        nonlocal fixes
                        if f'</{ot}>' not in m.group(1):
                            fixes += 1
                            return f'<{ot}>{m.group(1)}</{ot}>'
                        return m.group(0)
                    return fixer

                pattern = f'<{open_tag}>([^<]*(?:<(?!/{open_tag}>)[^<]*)*)</{wrong_close}>'
                text = re.sub(pattern, make_fixer(open_tag, wrong_close),
                              text, flags=re.I)

            # --- Незакрытые инлайн-теги ---
            # Фикс: <strong>текст без закрытия до конца абзаца
            for itag in INLINE_TAGS:
                pattern = f'<{itag}>([^<]*)</(p|li|td|th|summary)>'
                def fix_unclosed_inline(m, tag=itag):
                    nonlocal fixes
                    fixes += 1
                    return f'<{tag}>{m.group(1)}</{tag}></{m.group(2)}>'

                text = re.sub(pattern, fix_unclosed_inline, text, flags=re.I)

            # --- Пустые теги ---
            text_cleaned = re.sub(r'<p>\s*</p>', '', text)
            if text_cleaned != text:
                fixes += 1
                text = text_cleaned

            # --- <pre> без <code> ---
            def fix_pre(m):
                nonlocal fixes
                content = m.group(1)
                if '<code>' not in content:
                    fixes += 1
                    return f'<pre><code>{content.strip()}</code></pre>'
                return m.group(0)

            text = re.sub(r'<pre>((?:(?!</pre>).)*)</pre>',
                          fix_pre, text, flags=re.DOTALL)

            if text != original:
                fixed_count += 1
                dir_fixes += fixes
                total_fixes += fixes
                if apply:
                    fp.write_text(text, encoding='utf-8')

        if dir_fixes > 0:
            verb = "исправлено" if apply else "нужно исправить"
            print(f"  {d.name}: {dir_fixes} проблем {verb}")

    return fixed_count, total_fixes


# ============================================================
#  ШАГ 4: СБОРКА
# ============================================================
def run_build():
    """Запускает build.py."""
    if not BUILD_SCRIPT.exists():
        print("  ❌ build.py не найден!")
        return False

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        cwd=str(SITE_DIR),
        capture_output=True, text=True, encoding='utf-8', errors='replace', env=env
    )

    if result.stdout:
        for line in result.stdout.split('\n'):
            if line.strip():
                print(f"  {line.strip()}")

    if result.returncode != 0:
        print(f"  ❌ Build failed!")
        if result.stderr:
            print(f"  {result.stderr[:300]}")
        return False

    return True


# ============================================================
#  MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="DORI Build Pipeline")
    parser.add_argument('--apply', action='store_true',
                        help='Применить очистку, фиксы и запустить сборку')
    parser.add_argument('--skip-build', action='store_true',
                        help='Пропустить сборку (только очистка и фикс)')
    parser.add_argument('--audit-only', action='store_true',
                        help='Только аудит, без изменений')
    args = parser.parse_args()

    start = time.time()

    print_header("🔧 DORI Pipeline")
    print(f"  Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.audit_only:
        print("  Режим: 🔍 ТОЛЬКО АУДИТ")
    elif args.apply:
        print("  Режим: ⚡ ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ")
    else:
        print("  Режим: 🔍 DRY RUN (добавь --apply для применения)")

    # --- ШАГ 1: АУДИТ ---
    print_step(1, "АУДИТ СТАТЕЙ")
    audit = audit_articles()
    print_audit_report(audit)

    if args.audit_only:
        elapsed = time.time() - start
        print(f"\n⏱️  Аудит завершён за {elapsed:.0f}с")
        return

    # --- ШАГ 2: ОЧИСТКА ФРАЗ ---
    print_step(2, "ОЧИСТКА ФРАЗ-ПАРАЗИТОВ")
    run_clean_filler(apply=args.apply)

    # --- ШАГ 3: АВТОФИКС HTML ---
    print_step(3, "АВТОФИКС HTML-БАГОВ")
    fixed_files, total_fixes = fix_html_issues(apply=args.apply)
    if total_fixes == 0:
        print("  ✅ Битых тегов не найдено")
    else:
        verb = "Исправлено" if args.apply else "Найдено"
        print(f"  📊 {verb}: {total_fixes} проблем в {fixed_files} файлах")

    # --- ШАГ 4: СБОРКА ---
    if not args.skip_build and args.apply:
        print_step(4, "СБОРКА САЙТА")
        success = run_build()
        if success:
            print("\n  ✅ Сайт собран!")
    elif not args.apply:
        print(f"\n  💡 Добавь --apply чтобы применить изменения и собрать сайт")
    else:
        print(f"\n  ⏭️  Сборка пропущена (--skip-build)")

    # --- ИТОГО ---
    elapsed = time.time() - start
    print_header(f"✅ ГОТОВО ({elapsed:.0f}с)")
    print(f"  Статей проверено: {audit['total']}")
    print(f"  Без META (пропущены): {audit['no_meta']}")
    print(f"  Битые теги: {audit['bad_tags']}"
          f" → {'исправлены' if args.apply else 'нужен --apply'}")
    if not args.apply:
        print(f"\n  👉 python pipeline.py --apply")


if __name__ == '__main__':
    main()
