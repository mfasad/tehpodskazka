import requests
import json
import time
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = os.environ.get("NVIDIA_API_KEY", "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")
BASE_URL = "https://integrate.api.nvidia.com/v1"
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "articles_v4")
CHECK_DIR = os.environ.get("CHECK_DIR", "")  # Additional dir to check for existing files
TOP100_PATH = os.environ.get("TOP100_PATH", r"B:\antigravity\dori\keywords_split\bucket_01.json")
WORKERS = 2
LIMIT = 9620

os.makedirs(OUTPUT_DIR, exist_ok=True)

def make_prompt(query):
    return f"""Напиши экспертную SEO-статью на русском языке на тему: "{query}"

ФОРМАТ ОТВЕТА — строго два блока:

═══ БЛОК 1: МЕТА-ДАННЫЕ (первые строки) ═══
<!--META
{{"title": "SEO-заголовок до 70 символов", "description": "Мета-описание 150-160 символов", "h1": "Заголовок H1 статьи"}}
META-->

═══ БЛОК 2: ТЕЛО СТАТЬИ ═══

СТРУКТУРА:
- 6-8 разделов с заголовками <h2>
- Первый раздел — вводный, БЕЗ заголовка H2 (2-3 абзаца <p>)
- КАЖДЫЙ абзац текста ОБЯЗАТЕЛЬНО оборачивай в тег <p>. Текст вне тегов ЗАПРЕЩЁН.
- В каждом разделе 2-4 абзаца <p>
- 2-3 списка <ul> с <li> — каждый пункт <li> начинается с эмодзи
- 1 таблица <table> с <thead>/<tbody>, 3-5 строк данных
- 2-3 блока предупреждения <blockquote> со знаком ⚠️ и словом Внимание
- FAQ-блок в конце статьи: 3-5 вопросов используя теги <details> и <summary>
- Общий объём: 4000+ символов

РАЗНООБРАЗИЕ ТЕКСТА (ВАЖНО — статья НЕ должна быть монотонной!):
- Чередуй КОРОТКИЕ абзацы (1-2 предложения) с ДЛИННЫМИ (3-4 предложения). Не делай все абзацы одинаковой длины!
- Используй <strong> для ключевых терминов — 3-5 штук на раздел, НЕ в каждом абзаце
- Используй <em> для названий моделей, технических терминов, брендов
- Используй <mark> — ТОЛЬКО 1-2 раза на ВСЮ статью, для самой критичной информации, УНИКАЛЬНОЙ для конкретной темы. НЕ используй шаблонные фразы в <mark>, только факты из контекста статьи
- Чередуй стиль изложения: где-то пиши от второго лица ("вам нужно..."), где-то безличным ("необходимо..."), где-то используй вопрос-ответ

ЗАПРЕЩЁННЫЕ ШАБЛОННЫЕ ФРАЗЫ (НЕ ИСПОЛЬЗОВАТЬ НИКОГДА):
- "ни в коем случае не выключайте питание"
- "важно помнить, что"
- "настоятельно рекомендуем"
- "надеемся, что данная статья помогла"
- "если у вас остались вопросы, задавайте их в комментариях"
- "данная инструкция подходит для"
- "следуя нашим рекомендациям"
Все предупреждения и советы должны быть УНИКАЛЬНЫМИ и КОНКРЕТНЫМИ для темы статьи!

ИНТЕРАКТИВНЫЕ ВИДЖЕТЫ (вставь 4-5 штук в уместных местах статьи):

1. ОПРОС — один на статью, после 2-3 раздела:
<!--WIDGET:poll:Текст вопроса:Вариант 1|Вариант 2|Вариант 3|Вариант 4-->
Пример: <!--WIDGET:poll:Какой марки ваш телевизор?:Samsung|LG|Sony|Xiaomi|Другой-->

2. ЧЕК-ЛИСТ — один на статью, внутри раздела с инструкцией:
<!--WIDGET:checklist:Заголовок чеклиста:Пункт 1|Пункт 2|Пункт 3|Пункт 4-->
Пример: <!--WIDGET:checklist:Подготовка к обновлению:Проверить версию ПО|Подключить USB|Скачать прошивку|Не выключать ТВ-->

3. СПОЙЛЕР — 1-2 штуки, для дополнительной информации:
<!--WIDGET:spoiler:Заголовок спойлера:Скрытый текст с подробностями-->
Пример: <!--WIDGET:spoiler:Что будет если прервать обновление?:При прерывании процесса обновления прошивки телевизор может перестать включаться...-->

4. ПОЛЕЗНЫЙ СОВЕТ — 1-2 штуки:
<!--WIDGET:tip:Текст полезного совета-->
Пример: <!--WIDGET:tip:Перед обновлением сфотографируйте текущие настройки телевизора на телефон — это поможет быстро восстановить их после сброса.-->

5. КЛЮЧЕВОЙ ВЫВОД — 1-2 штуки, важный итог раздела:
<!--WIDGET:keypoint:Главная мысль или важный вывод данного раздела-->
Пример: <!--WIDGET:keypoint:Автоматическое обновление через интернет — самый безопасный способ, но требует стабильного подключения к сети.-->

РАЗРЕШЁННЫЕ HTML-ТЕГИ:
h2, p, ul, ol, li, table, thead, tbody, tr, th, td, blockquote, strong, em, mark, code, pre, details, summary

ОФОРМЛЕНИЕ КОМАНД И КОДА:
- Если в статье упоминаются пути к меню, настройки, команды — оборачивай их в <code> внутри абзаца
- Если команда длинная или это инструкция для ввода — используй отдельный блок <pre><code>команда</code></pre>
Примеры использования:
- Путь в меню: перейдите в <code>Настройки → Система → Обновление ПО</code>
- Команда: <pre><code>adb shell am start -n com.android.tv.settings</code></pre>
- Параметр: разрешение <code>1920×1080</code> при частоте <code>60 Гц</code>
- Последовательность кнопок: нажмите <code>Menu → Settings → All Settings → General</code>

КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО:
- <!DOCTYPE>, <html>, <head>, <body>, <meta>, <title>, <style>, <script>
- CSS-классы (class=) и inline-стили (style=)
- Markdown
- Тег <h1>
- Теги <span>, <div>, <br>, <hr>
- Текст вне HTML-тегов (каждый абзац ОБЯЗАН быть в <p>!)

Ответ начинается СТРОГО с <!--META."""


def clean_output(text):
    """Постобработка: убираем мусор и оборачиваем голый текст в <p>"""
    text = text.strip()
    
    # Убираем markdown-обёртки
    if text.startswith("```"):
        lines = text.split("\n")
        start_idx = 1
        end_idx = len(lines)
        for i in range(len(lines)-1, 0, -1):
            if lines[i].strip() == "```":
                end_idx = i
                break
        text = "\n".join(lines[start_idx:end_idx])
    
    # Сохраняем META-блок
    meta_match = re.search(r'<!--META\s*\n?(.*?)\n?\s*META-->', text, re.DOTALL)
    meta_json_str = meta_match.group(1).strip() if meta_match else None
    
    # Получаем тело
    body = text[meta_match.end():] if meta_match else text
    
    # Убираем DOCTYPE, html, head, body, style
    body = re.sub(r'<!DOCTYPE[^>]*>', '', body, flags=re.IGNORECASE)
    body = re.sub(r'</?html[^>]*>', '', body, flags=re.IGNORECASE)
    body = re.sub(r'<head>.*?</head>', '', body, flags=re.IGNORECASE | re.DOTALL)
    body = re.sub(r'</?body[^>]*>', '', body, flags=re.IGNORECASE)
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.IGNORECASE | re.DOTALL)
    body = re.sub(r'<title>.*?</title>', '', body, flags=re.IGNORECASE | re.DOTALL)
    body = re.sub(r'<meta[^>]*/?>', '', body, flags=re.IGNORECASE)
    body = re.sub(r'</meta>', '', body, flags=re.IGNORECASE)
    
    # Убираем class="..." и style="..."
    body = re.sub(r'\s+class="[^"]*"', '', body)
    body = re.sub(r'\s+style="[^"]*"', '', body)
    
    # Убираем section, div, span обёртки
    body = re.sub(r'</?section[^>]*>', '', body, flags=re.IGNORECASE)
    body = re.sub(r'</?div[^>]*>', '', body, flags=re.IGNORECASE)
    body = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', body, flags=re.IGNORECASE)
    
    # Убираем h1
    body = re.sub(r'<h1[^>]*>.*?</h1>', '', body, flags=re.IGNORECASE | re.DOTALL)
    
    # Убираем HTML-комментарии КРОМЕ WIDGET маркеров
    body = re.sub(r'<!--(?!WIDGET)(?!META).*?-->', '', body, flags=re.DOTALL)
    
    # === ОБОРАЧИВАЕМ ГОЛЫЙ ТЕКСТ В <p> ===
    lines = body.split('\n')
    result_lines = []
    # Теги которые являются "блочными" — текст рядом с ними не нужно оборачивать
    block_tags = re.compile(r'^\s*<(/?)(?:h[1-6]|p|ul|ol|li|table|thead|tbody|tr|th|td|blockquote|details|summary|!--WIDGET)', re.IGNORECASE)
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result_lines.append('')
            continue
        if block_tags.match(stripped):
            result_lines.append(line)
            continue
        if stripped.startswith('<!--WIDGET'):
            result_lines.append(line)
            continue
        # Это голый текст — оборачиваем в <p>
        if not stripped.startswith('<'):
            result_lines.append(f'<p>{stripped}</p>')
        else:
            result_lines.append(line)
    
    body = '\n'.join(result_lines)
    
    # Убираем пустые строки подряд
    body = re.sub(r'\n{3,}', '\n\n', body)
    body = body.strip()
    
    # Собираем
    if meta_json_str:
        result = f"<!--META\n{meta_json_str}\nMETA-->\n\n{body}"
    else:
        result = body
    
    return result


def parse_meta(text):
    """Извлекаем мета-данные"""
    match = re.search(r'<!--META\s*\n?(.*?)\n?\s*META-->', text, re.DOTALL)
    if not match:
        return None
    try:
        raw = match.group(1).strip().replace('\n', ' ')
        return json.loads(raw)
    except:
        return None


def validate_output(text, slug):
    """Проверяем качество"""
    issues = []
    
    meta = parse_meta(text)
    if meta is None:
        issues.append("NO_META")
    else:
        for key in ['title', 'description', 'h1']:
            if key not in meta:
                issues.append(f"NO_{key.upper()}")
    
    body = re.sub(r'<!--META.*?META-->', '', text, flags=re.DOTALL).strip()
    
    if '<!DOCTYPE' in body.upper(): issues.append("DOCTYPE")
    if '<style' in body.lower(): issues.append("STYLE")
    if 'style=' in body: issues.append("INLINE_STYLE")
    if 'class=' in body: issues.append("CSS_CLASS")
    if '<h1' in body.lower(): issues.append("H1_IN_BODY")
    
    h2 = len(re.findall(r'<h2', body, re.IGNORECASE))
    p = len(re.findall(r'<p', body, re.IGNORECASE))
    li = len(re.findall(r'<li', body, re.IGNORECASE))
    tbl = len(re.findall(r'<table', body, re.IGNORECASE))
    bq = len(re.findall(r'<blockquote', body, re.IGNORECASE))
    faq = len(re.findall(r'<details', body, re.IGNORECASE))
    
    # Widget counts
    poll = len(re.findall(r'<!--WIDGET:poll:', body))
    checklist = len(re.findall(r'<!--WIDGET:checklist:', body))
    spoiler = len(re.findall(r'<!--WIDGET:spoiler:', body))
    tip = len(re.findall(r'<!--WIDGET:tip:', body))
    widgets = poll + checklist + spoiler + tip
    
    if h2 < 4: issues.append(f"LOW_H2({h2})")
    if p < 8: issues.append(f"LOW_P({p})")
    if li < 4: issues.append(f"LOW_LI({li})")
    if tbl < 1: issues.append("NO_TABLE")
    if faq < 1: issues.append("NO_FAQ")
    if widgets < 2: issues.append(f"LOW_WIDGETS({widgets})")
    
    return issues, {
        "h2": h2, "p": p, "li": li, "tbl": tbl, "bq": bq,
        "faq": faq, "widgets": widgets,
        "meta": "OK" if meta else "FAIL"
    }


def generate_article(item):
    query = item["query"]
    slug = item["slug"]
    item_id = item["id"]
    
    output_file = os.path.join(OUTPUT_DIR, f"{slug}.html")
    
    if os.path.exists(output_file):
        return f"[{item_id}] SKIP: {slug}"
    
    # Also check base dir for existing files
    if CHECK_DIR and os.path.exists(os.path.join(CHECK_DIR, f"{slug}.html")):
        return f"[{item_id}] SKIP(base): {slug}"
    
    # Check other keys' folders
    extra_dirs = os.environ.get("CHECK_EXTRA_DIRS", "")
    if extra_dirs:
        for extra in extra_dirs.split(";"):
            if extra and os.path.exists(os.path.join(extra, f"{slug}.html")):
                return f"[{item_id}] SKIP(other): {slug}"
    
    start = time.time()
    
    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen/qwen3.5-122b-a10b",
                    "messages": [{"role": "user", "content": make_prompt(query)}],
                    "max_tokens": 8192,
                    "temperature": 0.7,
                    "stream": True
                },
                stream=True,
                timeout=300
            )
            
            if resp.status_code == 429:
                if attempt < max_retries:
                    wait = 30 * (2 ** attempt)  # 30s, 60s, 120s
                    time.sleep(wait)
                    continue
                return f"[{item_id}] ERROR 429 (after {max_retries} retries): {slug}"
            
            if resp.status_code != 200:
                return f"[{item_id}] ERROR {resp.status_code}: {slug}"
            
            break  # success, exit retry loop
        
        except Exception as e:
            if attempt < max_retries:
                time.sleep(30)
                continue
            return f"[{item_id}] EXCEPTION: {slug} - {str(e)[:100]}"
    
    # Process response (outside retry loop, after successful request)
    try:
        full_text = []
        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str.strip() == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                delta = chunk["choices"][0]["delta"]
                if "content" in delta:
                    full_text.append(delta["content"])
            except:
                pass
        
        raw_article = "".join(full_text)
        article = clean_output(raw_article)
        elapsed = time.time() - start
        issues, stats = validate_output(article, slug)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(article)
        
        status = "OK" if not issues else f"WARN({','.join(issues)})"
        s = stats
        stats_str = f"meta={s['meta']} h2={s['h2']} p={s['p']} li={s['li']} tbl={s['tbl']} bq={s['bq']} faq={s['faq']} w={s['widgets']}"
        return f"[{item_id}] {status} ({elapsed:.0f}s, {len(article)}ch, {stats_str}): {slug[:35]}"
    
    except Exception as e:
        return f"[{item_id}] EXCEPTION: {slug} - {str(e)[:100]}"


# Load queries
with open(TOP100_PATH, "r", encoding="utf-8") as f:
    queries = json.load(f)

batch = queries[:LIMIT]

# Sharding: split work across multiple processes
SHARD_ID = int(os.environ.get("SHARD_ID", "0"))
SHARD_TOTAL = int(os.environ.get("SHARD_TOTAL", "1"))
if SHARD_TOTAL > 1:
    batch = [item for i, item in enumerate(batch) if i % SHARD_TOTAL == SHARD_ID]

print(f"=== BATCH GENERATION V4 (META + Widgets + FAQ) ===")
print(f"Articles: {len(batch)} (shard {SHARD_ID+1}/{SHARD_TOTAL})")
print(f"Workers: {WORKERS}")
print(f"Output: {OUTPUT_DIR}")
print(f"Model: qwen/qwen3.5-122b-a10b (max_tokens=8192)")
print(f"Features: META + poll/checklist/spoiler/tip + FAQ + strict <p>")
print(f"===================================================\n")

total_start = time.time()
completed = 0

with ThreadPoolExecutor(max_workers=WORKERS) as executor:
    futures = {executor.submit(generate_article, item): item for item in batch}
    
    for future in as_completed(futures):
        completed += 1
        result = future.result()
        print(f"[{completed}/{len(batch)}] {result}")

total_elapsed = time.time() - total_start
print(f"\n=== TOTAL: {total_elapsed:.0f}s ({total_elapsed/60:.1f} min) ===")
print(f"Speed: {len(batch)/total_elapsed*3600:.0f} articles/hour")
