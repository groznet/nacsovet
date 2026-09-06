#!/usr/bin/env python3
"""
Чинит заголовки Hugo, оканчивающиеся на серию точек.

Точки в конце title превращаются в слаг с точками на конце, а такой каталог
невозможно создать в Windows — сборка падает.

Два режима:
  --mode slug   (по умолчанию) заголовок не трогает, добавляет поле slug
                без точек. URL чинится, авторский текст сохраняется.
  --mode strip  убирает точки из самого заголовка.

По умолчанию ничего не пишет — только показывает, что будет изменено.
Для записи добавьте --apply.
"""

import argparse
import re
import sys
from pathlib import Path

# title = "..."  или  title = '...'
TITLE_RE = re.compile(r"^(\s*title\s*=\s*)(\"([^\"]*)\"|'([^']*)')\s*$")
SLUG_RE = re.compile(r"^\s*slug\s*=", re.IGNORECASE)
# точки/пробелы в конце строки
TRAILING_DOTS_RE = re.compile(r"[.\u2026\s]+$")
# проблемный заголовок: 2+ точки подряд где угодно, либо точка/пробел в конце
NEEDS_FIX_RE = re.compile(r"\.{2,}|\u2026|[.\s]$")


def split_front_matter(text):
    """Возвращает (строки_фронтматтера, строки_остального) для TOML +++."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "+++":
        return None, None
    for i in range(1, len(lines)):
        if lines[i].strip() == "+++":
            return lines[1:i], lines[i + 1:]
    return None, None


def needs_fix(value):
    """Ломает ли этот заголовок путь публикации."""
    return bool(NEEDS_FIX_RE.search(value))


def strip_tail(value):
    """Убирает хвостовые точки и пробелы."""
    return TRAILING_DOTS_RE.sub("", value)


def make_slug(title):
    """Слаг в стиле Hugo urlize: нижний регистр, пробелы в дефисы.

    Кириллица сохраняется — так URL остаются совместимы с уже
    существующими ссылками, меняются только точки.
    """
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "-", slug.strip())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug


def process(path, mode):
    """Возвращает (новый_текст, старый_заголовок, что_добавлено) или None."""
    text = path.read_text(encoding="utf-8")
    fm, body = split_front_matter(text)
    if fm is None:
        return None

    for idx, line in enumerate(fm):
        m = TITLE_RE.match(line.rstrip("\n"))
        if not m:
            continue

        prefix, quoted = m.group(1), m.group(2)
        value = m.group(3) if m.group(3) is not None else m.group(4)
        quote = quoted[0]

        if not needs_fix(value):
            return None

        if mode == "strip":
            cleaned = strip_tail(value)
            if not cleaned or cleaned == value:
                return None
            fm[idx] = f"{prefix}{quote}{cleaned}{quote}\n"
            note = cleaned
        else:
            if any(SLUG_RE.match(l) for l in fm):
                return None  # slug уже задан вручную — не трогаем
            slug = make_slug(value)
            if not slug:
                return None
            fm[idx] = line if line.endswith("\n") else line + "\n"
            fm.insert(idx + 1, f'slug = "{slug}"\n')
            note = slug

        return "+++\n" + "".join(fm) + "+++\n" + "".join(body), value, note

    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="корень content/, например ./content")
    ap.add_argument("--mode", choices=["slug", "strip"], default="slug")
    ap.add_argument("--apply", action="store_true", help="записать изменения")
    ap.add_argument("--glob", default="**/*.md")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        sys.exit(f"Не найден каталог: {root}")

    changed = 0
    for path in sorted(root.glob(args.glob)):
        result = process(path, args.mode)
        if result is None:
            continue
        new_text, old_title, note = result
        changed += 1
        print(f"\n{path}")
        print(f"  было:  {old_title}")
        if args.mode == "strip":
            print(f"  стало: {note}")
        else:
            print(f"  slug:  {note}")
        if args.apply:
            path.write_text(new_text, encoding="utf-8")

    print(f"\n{'Изменено' if args.apply else 'Будет изменено'} файлов: {changed}")
    if changed and not args.apply:
        print("Это предпросмотр. Для записи запустите с --apply")


if __name__ == "__main__":
    main()