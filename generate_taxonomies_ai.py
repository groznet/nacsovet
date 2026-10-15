#!/usr/bin/env python3
"""
Generate Hugo taxonomies (tags / categories / projects / locations) for markdown
articles using a local Ollama model.

Design notes
------------
* All taxonomy values pass through a single controlled vocabulary
  (CANONICAL_SYNONYMS) so that "ЧР", "Чеченская република" and "Чечня" all end
  up as one term: "Чеченская Республика".
* Matching is done on a normalized key (case-folded, ё→е, punctuation and
  quote-insensitive), while the *output* keeps the canonical casing.
* Every file is processed inside its own try/except, so a single bad file never
  aborts a 7000-file batch.
* Files are written atomically (temp file + os.replace) — an interrupted run
  cannot leave a half-written article behind.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

# --------------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:latest"
CONTENT_DIR = "content/news"
LOG_FILE = "taxonomies_generation.log"

MAX_BODY_CHARS = 8000
OVERWRITE_EXISTING = False   # True = regenerate even if taxonomies exist
REQUEST_TIMEOUT = 300
REQUEST_RETRIES = 3
RETRY_BACKOFF = 5            # seconds, multiplied by attempt number
DEFAULT_WORKERS = 1          # raise only if OLLAMA_NUM_PARALLEL > 1 on the server

TAXONOMY_KEYS = ("tags", "categories", "projects", "locations")

# Hard caps keep the vocabulary tight instead of letting the model sprawl.
MAX_ITEMS = {"tags": 8, "categories": 3, "projects": 5, "locations": 5}
MAX_TERM_LENGTH = 70

# Closed-ish rubric list handed to the model — the single strongest lever for
# category consistency across thousands of articles.
PREFERRED_CATEGORIES = [
    "Общество",
    "Образование",
    "Культура",
    "Спорт",
    "Молодёжь",
    "Волонтёрство",
    "Благотворительность",
    "Здравоохранение",
    "Экономика",
    "Наука и технологии",
    "Религия",
    "Экология",
    "Безопасность",
    "Туризм",
    "Сельское хозяйство",
    "Транспорт",
    "Политика",
    "История",
    "Мероприятия",
]

# --------------------------------------------------------------------------
# CONTROLLED VOCABULARY
# --------------------------------------------------------------------------
# key   = any variation the model or old front matter might emit
# value = the one canonical string that ends up in the front matter
#
# Keys are matched case-insensitively, ё/е-insensitively and ignoring quotes,
# dashes and trailing punctuation — so you only need to list genuinely
# different wordings, not every casing.

CANONICAL_SYNONYMS: dict[str, str] = {
    # ---- Locations: republic / country -----------------------------------
    "чр": "Чеченская Республика",
    "чри": "Чеченская Республика",
    "чечня": "Чеченская Республика",
    "чечне": "Чеченская Республика",
    "чечни": "Чеченская Республика",
    "чеченская република": "Чеченская Республика",
    "чеченская респ": "Чеченская Республика",
    "чеченская республика": "Чеченская Республика",
    "республика чечня": "Чеченская Республика",
    "рф": "Россия",
    "россии": "Россия",
    "российская федерация": "Россия",
    "россия": "Россия",
    "скфо": "Северо-Кавказский федеральный округ",
    "северный кавказ": "Северный Кавказ",
    "кавказ": "Северный Кавказ",
    # ---- Locations: cities (declensions → nominative) ---------------------
    "грозном": "Грозный",
    "в грозном": "Грозный",
    "грозного": "Грозный",
    "г. грозный": "Грозный",
    "город грозный": "Грозный",
    "аргуне": "Аргун",
    "аргуна": "Аргун",
    "гудермесе": "Гудермес",
    "гудермеса": "Гудермес",
    "шали": "Шали",
    "урус мартан": "Урус-Мартан",
    "урус-мартане": "Урус-Мартан",
    "ачхой мартан": "Ачхой-Мартан",
    "курчалое": "Курчалой",
    "москве": "Москва",
    "москвы": "Москва",
    "санкт петербург": "Санкт-Петербург",
    "спб": "Санкт-Петербург",
    "питер": "Санкт-Петербург",
    # ---- Projects & organizations ----------------------------------------
    "хаар time": "Хаар-Time",
    "хаар тайм": "Хаар-Time",
    "haar time": "Хаар-Time",
    "хаартайм": "Хаар-Time",
    "я и весь мир": "Я и весь мир",
    "lady квиз": "Lady-Квиз",
    "леди квиз": "Lady-Квиз",
    "ледиквиз": "Lady-Квиз",
    "что где когда": "Что? Где? Когда?",
    "чгк": "Что? Где? Когда?",
    "даймохк": "БФ «Даймохк»",
    "бф даймохк": "БФ «Даймохк»",
    "фонд даймохк": "БФ «Даймохк»",
    "благотворительный фонд даймохк": "БФ «Даймохк»",
    # ---- Tags / categories: plural & near-duplicate collapsing ------------
    "волонтеры": "Волонтёрство",
    "волонтёры": "Волонтёрство",
    "волонтерство": "Волонтёрство",
    "добровольцы": "Волонтёрство",
    "молодежь": "Молодёжь",
    "молодые люди": "Молодёжь",
    "школьники": "Школьники",
    "школьник": "Школьники",
    "студенты": "Студенты",
    "студент": "Студенты",
    "дети": "Дети",
    "ребенок": "Дети",
    "благотворительность": "Благотворительность",
    "интеллектуальные игры": "Интеллектуальные игры",
    "интеллектуальная игра": "Интеллектуальные игры",
    "соревнования": "Соревнования",
    "соревнование": "Соревнования",
    "турниры": "Соревнования",
    "турнир": "Соревнования",
    "конкурсы": "Конкурс",
    "конкурс": "Конкурс",
    "мероприятия": "Мероприятия",
    "мероприятие": "Мероприятия",
    "образование": "Образование",
    "спорт": "Спорт",
    "культура": "Культура",
    "общество": "Общество",
}

# --------------------------------------------------------------------------
# LOGGING
# --------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("taxonomies")

# --------------------------------------------------------------------------
# NORMALIZATION HELPERS
# --------------------------------------------------------------------------

_DASHES = str.maketrans({"–": "-", "—": "-", "‑": "-", "−": "-"})
_QUOTES_RE = re.compile(r'[«»"“”„‟\'’‘`]')
_WS_RE = re.compile(r"\s+")
_TRAILING_PUNCT_RE = re.compile(r"[\s.,;:!]+$")


def norm_key(value: str) -> str:
    """Matching key: lowercase, ё→е, no quotes/punctuation, collapsed spaces."""
    if not value:
        return ""
    key = value.strip().lower().replace("ё", "е")
    key = key.translate(_DASHES)
    key = _QUOTES_RE.sub("", key)
    key = re.sub(r"[?!.,;:]", " ", key)
    key = key.replace("-", " ")
    return _WS_RE.sub(" ", key).strip()


def tidy(value: str) -> str:
    """Light cleanup for terms that are not in the controlled vocabulary."""
    cleaned = _WS_RE.sub(" ", value.strip().translate(_DASHES))
    cleaned = cleaned.strip("«»\"'“”„ ")
    cleaned = _TRAILING_PUNCT_RE.sub("", cleaned)
    return cleaned.strip()


# canonical values must also map to themselves
SYNONYM_LOOKUP: dict[str, str] = {}
for _raw, _canonical in CANONICAL_SYNONYMS.items():
    SYNONYM_LOOKUP[norm_key(_raw)] = _canonical
    SYNONYM_LOOKUP[norm_key(_canonical)] = _canonical
for _category in PREFERRED_CATEGORIES:
    SYNONYM_LOOKUP.setdefault(norm_key(_category), _category)


def canonicalize(value: str) -> Optional[str]:
    """Map one raw term to its canonical form, or None if it should be dropped."""
    if not isinstance(value, str):
        return None
    cleaned = tidy(value)
    if not cleaned or len(cleaned) > MAX_TERM_LENGTH:
        return None
    if cleaned.isdigit():
        return None
    return SYNONYM_LOOKUP.get(norm_key(cleaned), cleaned)


def normalize_items(*item_groups, limit: Optional[int] = None) -> list[str]:
    """
    Merge several lists of terms into one canonical, case-insensitively
    deduplicated list. Order is preserved: existing front-matter values first,
    then new AI values.
    """
    result: list[str] = []
    seen: set[str] = set()

    for group in item_groups:
        for item in group or []:
            canonical = canonicalize(item)
            if not canonical:
                continue
            key = norm_key(canonical)
            if key in seen:
                continue
            seen.add(key)
            result.append(canonical)
            if limit and len(result) >= limit:
                return result
    return result


# --------------------------------------------------------------------------
# OLLAMA
# --------------------------------------------------------------------------


def call_ollama(
    prompt: str,
    url: str = OLLAMA_URL,
    model: str = MODEL,
    retries: int = REQUEST_RETRIES,
    timeout: int = REQUEST_TIMEOUT,
) -> str:
    """POST a prompt to Ollama and return the raw response string ("" on failure)."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},  # low temperature = stable vocabulary
    }
    data = json.dumps(payload).encode("utf-8")

    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
                return body.get("response", "")
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            socket.timeout,
            ConnectionError,
            json.JSONDecodeError,
        ) as exc:
            log.warning("Ollama attempt %s/%s failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(RETRY_BACKOFF * attempt)
    log.error("Ollama call failed after %s attempts.", retries)
    return ""


def build_prompt(title: str, body: str) -> str:
    categories_hint = ", ".join(f'"{c}"' for c in PREFERRED_CATEGORIES)
    projects_hint = ", ".join(
        f'"{p}"' for p in sorted({v for v in CANONICAL_SYNONYMS.values() if "?" in v or "-" in v or "«" in v})
    )
    return f"""Ты — контент-менеджер новостного сайта. Проанализируй статью и верни 4 таксономии.

1. "tags" — до {MAX_ITEMS['tags']} ключевых слов: общие, короткие, во множественном числе или как устойчивый термин.
2. "categories" — от 1 до {MAX_ITEMS['categories']} рубрик. Выбирай ТОЛЬКО из списка: {categories_hint}.
3. "projects" — до {MAX_ITEMS['projects']} названий проектов, игр, турниров, программ, фондов или организаций.
   Известные названия пиши строго так: {projects_hint}.
4. "locations" — до {MAX_ITEMS['locations']} населённых пунктов, регионов или стран.

СТРОГИЕ ПРАВИЛА:
- Локации только в ИМЕНИТЕЛЬНОМ падеже: "Грозный", а не "в Грозном"; "Чеченская Республика", а не "в Чечне"; "Россия", а не "РФ".
- Теги и рубрики — обобщённые и лаконичные. Не придумывай узкие или редкие формулировки, если подходит общий термин.
- Не создавай почти одинаковых терминов ("волонтёр" и "волонтёры" — выбери один общий).
- Не выдумывай проекты и места, которых нет в тексте. Если ничего не найдено — верни пустой массив [].
- Никаких пояснений, markdown или текста вне JSON.

Формат ответа:
{{"tags": [], "categories": [], "projects": [], "locations": []}}

Заголовок: {title}

Текст статьи:
{body[:MAX_BODY_CHARS]}
"""


_JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")


def parse_ai_response(raw: str) -> Optional[dict]:
    """Parse the model output, tolerating code fences or surrounding prose."""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = _JSON_OBJECT_RE.search(text)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None
    return {key: data.get(key) or [] for key in TAXONOMY_KEYS}


# --------------------------------------------------------------------------
# FRONT MATTER
# --------------------------------------------------------------------------

FRONT_MATTER_RE = re.compile(r"^\s*\+\+\+[ \t]*\r?\n(.*?)\r?\n\+\+\+[ \t]*\r?\n?", re.DOTALL)


def parse_front_matter(content: str) -> tuple[Optional[str], Optional[str]]:
    """Split the leading TOML front matter from the body."""
    match = FRONT_MATTER_RE.match(content.lstrip("\ufeff"))
    if not match:
        return None, None
    return match.group(1), content.lstrip("\ufeff")[match.end():]


def extract_title(front_matter: str) -> str:
    match = re.search(r'^[ \t]*title[ \t]*=[ \t]*(.+)$', front_matter, re.MULTILINE)
    if not match:
        return ""
    raw = match.group(1).strip()
    quoted = re.match(r'^"((?:[^"\\]|\\.)*)"', raw) or re.match(r"^'([^']*)'", raw)
    if quoted:
        return quoted.group(1).replace('\\"', '"').replace("\\\\", "\\").strip()
    return raw.strip()


def _array_pattern(key: str) -> re.Pattern:
    return re.compile(
        rf'^[ \t]*{re.escape(key)}[ \t]*=[ \t]*\[[^\]]*\][ \t]*$',
        re.MULTILINE,
    )


def extract_existing_taxonomy(front_matter: str, key: str) -> list[str]:
    """Read an existing TOML array, unescaping the string values."""
    match = _array_pattern(key).search(front_matter)
    if not match:
        return []
    raw = match.group(0).split("=", 1)[1]
    items = re.findall(r'"((?:[^"\\]|\\.)*)"', raw)
    return [item.replace('\\"', '"').replace("\\\\", "\\") for item in items]


def has_all_taxonomies(front_matter: str) -> bool:
    """True only if all four keys exist AND are non-empty (tags = [] fails)."""
    return all(extract_existing_taxonomy(front_matter, key) for key in TAXONOMY_KEYS)


def escape_toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def format_toml_array(items: list[str], indent: str = "\t") -> str:
    if not items:
        return "[]"
    lines = [f'{indent}"{escape_toml_string(item)}",' for item in items]
    return "[\n" + "\n".join(lines) + "\n]"


def update_front_matter(front_matter: str, taxonomies: dict[str, list[str]], indent: str = "\t") -> str:
    """Replace each taxonomy array in place, appending only if it was missing."""
    result = front_matter.rstrip()
    for key in TAXONOMY_KEYS:
        block = f"{key} = {format_toml_array(taxonomies.get(key, []), indent)}"
        pattern = _array_pattern(key)
        if pattern.search(result):
            result = pattern.sub(lambda _m, b=block: b, result, count=1)
        else:
            result = f"{result}\n{block}"
    return result.strip()


# --------------------------------------------------------------------------
# FILE PROCESSING
# --------------------------------------------------------------------------


class Stats:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.updated = 0
        self.skipped = 0
        self.failed = 0

    def bump(self, field: str) -> None:
        with self._lock:
            setattr(self, field, getattr(self, field) + 1)


def write_atomic(path: Path, content: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8", newline="")
    os.replace(tmp, path)


def process_file(path: Path, args, stats: Stats) -> None:
    content = path.read_text(encoding="utf-8")
    front_matter, body = parse_front_matter(content)
    if front_matter is None:
        log.warning("Skipping %s: no valid TOML front matter.", path)
        stats.bump("skipped")
        return

    if not args.overwrite and has_all_taxonomies(front_matter):
        log.info("Skipped %s (taxonomies already present).", path)
        stats.bump("skipped")
        return

    existing = {key: extract_existing_taxonomy(front_matter, key) for key in TAXONOMY_KEYS}

    prompt = build_prompt(extract_title(front_matter), body)
    raw = call_ollama(prompt, url=args.url, model=args.model, timeout=args.timeout,
                      retries=args.retries)
    data = parse_ai_response(raw)
    if data is None:
        log.error("Unusable AI response for %s. Raw: %.300s", path, raw)
        stats.bump("failed")
        return

    taxonomies = {
        key: normalize_items(existing[key], data[key], limit=MAX_ITEMS[key])
        for key in TAXONOMY_KEYS
    }

    if not any(taxonomies.values()):
        log.warning("No taxonomies produced for %s; leaving file unchanged.", path)
        stats.bump("skipped")
        return

    new_front_matter = update_front_matter(front_matter, taxonomies, indent=args.indent)
    new_content = f"+++\n{new_front_matter}\n+++\n{body.lstrip(chr(10))}"

    if args.dry_run:
        log.info("[dry-run] %s -> %s", path, taxonomies)
        stats.bump("updated")
        return

    write_atomic(path, new_content)
    stats.bump("updated")
    log.info("Updated %s (%s)", path, ", ".join(f"{k}:{len(v)}" for k, v in taxonomies.items()))


def process_file_safe(path: Path, index: int, total: int, args, stats: Stats) -> None:
    """Never let one file kill the batch."""
    log.info("[%s/%s] Checking: %s", index, total, path)
    try:
        process_file(path, args, stats)
    except Exception as exc:  # noqa: BLE001 - batch resilience is the point
        stats.bump("failed")
        log.exception("Failed to process %s: %s", path, exc)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def collect_files(root: Path) -> list[Path]:
    return sorted(
        f for f in root.rglob("*.md")
        if not f.name.startswith("._") and f.name != "_index.md"
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract 4 Hugo taxonomies using a local Ollama model."
    )
    parser.add_argument("--dir", default=CONTENT_DIR, help="Content directory path")
    parser.add_argument("--url", default=OLLAMA_URL, help="Ollama generate endpoint")
    parser.add_argument("--model", default=MODEL, help="Ollama model name")
    parser.add_argument("--timeout", type=int, default=REQUEST_TIMEOUT, help="Request timeout, seconds")
    parser.add_argument("--retries", type=int, default=REQUEST_RETRIES, help="Retries per request")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help="Parallel files (needs OLLAMA_NUM_PARALLEL > 1 to help)")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N files")
    parser.add_argument("--indent", default="\t", help="Indent used inside TOML arrays")
    parser.add_argument("--dry-run", action="store_true", help="Log results without writing files")
    parser.add_argument("--overwrite", action="store_true", default=OVERWRITE_EXISTING,
                        help="Regenerate even if taxonomies are already present")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()

    root = Path(args.dir)
    if not root.is_dir():
        log.error("Directory %s does not exist.", root)
        sys.exit(1)

    files = collect_files(root)
    if args.limit:
        files = files[: args.limit]
    total = len(files)
    log.info("Found %s markdown files in %s", total, root)

    stats = Stats()
    started = time.time()

    if args.workers > 1:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [
                pool.submit(process_file_safe, path, i, total, args, stats)
                for i, path in enumerate(files, 1)
            ]
            for future in as_completed(futures):
                future.result()
    else:
        for i, path in enumerate(files, 1):
            process_file_safe(path, i, total, args, stats)

    log.info(
        "Finished in %.1fs — updated: %s, skipped: %s, failed: %s",
        time.time() - started, stats.updated, stats.skipped, stats.failed,
    )


if __name__ == "__main__":
    main()