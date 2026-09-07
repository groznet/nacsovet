#!/usr/bin/env python3

import argparse
import json
import logging
import os
import shutil
import sys
import urllib.error
import urllib.request


# --- CONFIGURATION ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:latest"
CONTENT_DIR = "content/news"
BACKUP_DIR = "backups"
LOG_FILE = "taxonomy_generation.log"
MAX_BODY_CHARS = 8000

DEFAULT_CATEGORIES = [
    "Новости",
    "Мероприятия",
    "Интерактивные игры",
    "Проекты",
    "Конкурсы",
    "Форумы и съезды",
    "Образование и обучение",
    "Патриотическое воспитание",
    "Волонтёрство",
    "Международное сотрудничество",
    "Объявления",
]

GENERIC_TAGS_BLACKLIST = {
    "новости",
    "новость",
    "событие",
    "события",
    "информация",
    "статья",
    "публикация",
    "материал",
    "мероприятие",
}


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)


def create_backup(file_path: str):
    rel_path = os.path.relpath(file_path)
    backup_path = os.path.join(BACKUP_DIR, rel_path)

    if os.path.exists(backup_path):
        return

    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(file_path, backup_path)


def build_prompt(title: str, content: str) -> str:
    categories = ", ".join(DEFAULT_CATEGORIES)

    return f"""Ты классифицируешь новостные публикации для сайта nacsovet.ru —
сайта Межрегиональной Ассоциации общественных объединений
«Национальный совет молодёжных и детских объединений».

Проанализируй заголовок и текст публикации.

КАТЕГОРИИ:

Выбери ОДНУ или максимум ДВЕ категории.

Основной список:
{categories}

Правила:
- Категории должны быть широкими и универсальными.
- Используй категории из списка выше, если они подходят.
- Новую категорию создавай только если публикация явно не подходит ни под одну.
- Не используй название проекта, мероприятия, игры, сезона, города,
  региона, организации или человека как категорию.
- Если достаточно одной категории, выбери только одну.

ТЕГИ:

Выбери от 3 до 8 тегов.

Правила:
- Все теги на русском языке и в нижнем регистре.
- Используй конкретику из текста публикации.
- Можно использовать названия проектов, мероприятий, игр, организаций,
  города, регионы, темы, направления, аудитории, имена и фамилии.
- Не используй #.
- Не используй дубликаты.
- Не используй выбранные категории как теги.
- Не используй общие теги: новости, новость, событие, события,
  информация, статья, публикация, материал, мероприятие.
- Не придумывай теги, которых нет в тексте или которые нельзя
  обоснованно вывести из содержания.

ФОРМАТ ОТВЕТА:

Верни ТОЛЬКО JSON без Markdown и пояснений.

{{
  "categories": ["Категория"],
  "tags": ["тег 1", "тег 2", "тег 3"]
}}

ЗАГОЛОВОК:
{title}

ТЕКСТ ПУБЛИКАЦИИ:
{content}
"""


def query_ollama(prompt: str) -> dict:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1
        },
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )
    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Cannot connect to Ollama at {OLLAMA_URL}: {error}"
        ) from error

    raw_response = result.get("response", "").strip()

    if not raw_response:
        raise RuntimeError("Ollama returned an empty response")

    return json.loads(raw_response)


def validate_response(data: dict) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Response is not a JSON object"

    categories = data.get("categories")
    tags = data.get("tags")

    if not isinstance(categories, list) or not (1 <= len(categories) <= 2):
        return False, "Categories must contain 1 or 2 items"

    if not isinstance(tags, list) or not (3 <= len(tags) <= 8):
        return False, "Tags must contain 3 to 8 items"

    categories = [
        c.strip()
        for c in categories
        if isinstance(c, str) and c.strip()
    ]

    tags = [
        t.strip().lower()
        for t in tags
        if isinstance(t, str) and t.strip()
    ]

    if len(categories) < 1 or len(categories) > 2:
        return False, "Invalid categories"

    if len(tags) < 3 or len(tags) > 8:
        return False, "Invalid tags"

    if len(set(categories)) != len(categories):
        return False, "Duplicate categories"

    if len(set(tags)) != len(tags):
        return False, "Duplicate tags"

    if any(t.startswith("#") for t in tags):
        return False, "Hashtags are not allowed"

    if any(t in GENERIC_TAGS_BLACKLIST for t in tags):
        return False, "Contains generic tag"

    category_lower = {c.lower() for c in categories}

    if any(t in category_lower for t in tags):
        return False, "Tag duplicates category"

    return True, ""


def find_posts(root_dir: str) -> list[str]:
    posts = []

    for root, _, files in os.walk(root_dir):
        if "index.md" in files:
            posts.append(os.path.join(root, "index.md"))

    return sorted(posts)


def update_taxonomies(file_path: str, categories: list[str], tags: list[str]):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_categories = "categories = [\n"
    for category in categories:
        new_categories += f'    "{category}",\n'
    new_categories += "]"

    new_tags = "tags = [\n"
    for tag in tags:
        new_tags += f'    "{tag}",\n'
    new_tags += "]"

    if "categories = []" not in content:
        raise ValueError(
            "Could not find 'categories = []' in front matter"
        )

    if "tags = []" not in content:
        raise ValueError(
            "Could not find 'tags = []' in front matter"
        )

    content = content.replace(
        "categories = []",
        new_categories,
        1,
    )

    content = content.replace(
        "tags = []",
        new_tags,
        1,
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(
        description="Generate categories and tags for NacSovet Hugo posts via Ollama."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without modifying files or creating backups",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of posts to process (0 = all)",
    )

    args = parser.parse_args()

    posts = find_posts(CONTENT_DIR)

    if args.limit > 0:
        posts = posts[:args.limit]

    total = len(posts)

    print(f"Found {total} posts to process.\n")

    processed = 0
    updated = 0
    skipped = 0
    errors = 0

    for index, path in enumerate(posts, 1):
        print(f"[{index}/{total}] {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                file_content = f.read()

            # Extract TOML front matter between +++ markers.
            if not file_content.startswith("+++"):
                print("  ✗ Skipped — no TOML front matter")
                skipped += 1
                continue

            parts = file_content.split("+++", 2)

            if len(parts) != 3:
                print("  ✗ Skipped — invalid front matter")
                skipped += 1
                continue

            front_matter = parts[1]
            body = parts[2].strip()

            title = ""

            for line in front_matter.splitlines():
                if line.startswith("title ="):
                    title = line.split("=", 1)[1].strip().strip('"')
                    break

            if not body:
                print("  ✗ Skipped — empty post content")
                skipped += 1
                continue

            body_for_ai = body[:MAX_BODY_CHARS]

            prompt = build_prompt(
                title,
                body_for_ai,
            )

            llm_res = query_ollama(prompt)

            valid, error_message = validate_response(llm_res)

            if not valid:
                print(f"  ✗ LLM error — {error_message}")

                logging.error(
                    "Validation failed for %s: %s. Response: %s",
                    path,
                    error_message,
                    llm_res,
                )

                errors += 1
                continue

            categories = [
                c.strip()
                for c in llm_res["categories"]
            ]

            tags = [
                t.strip().lower()
                for t in llm_res["tags"]
            ]

            print(
                f"  Categories: {', '.join(categories)}"
            )

            print(
                f"  Tags:       {', '.join(tags)}"
            )

            processed += 1

            if args.dry_run:
                print("  ✓ Dry run — file not modified\n")
                updated += 1
                continue

            create_backup(path)

            update_taxonomies(
                path,
                categories,
                tags,
            )

            print("  ✓ Updated\n")

            updated += 1

        except Exception as error:
            print(f"  ✗ Error — {error}\n")

            logging.exception(
                "Unhandled error processing %s",
                path,
            )

            errors += 1

    print("-" * 40)
    print("Processing complete\n")
    print(f"Total posts:      {total}")
    print(f"Processed:        {processed}")
    print(f"Updated:          {updated}")
    print(f"Skipped:          {skipped}")
    print(f"Errors:           {errors}")
    print("-" * 40)


if __name__ == "__main__":
    main()