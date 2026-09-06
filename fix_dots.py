#!/usr/bin/env python3
"""
Приводит слаги Hugo к чистому виду слово-слово-слово.

Зачем: Hugo делает слаг из заголовка и сохраняет в нём пунктуацию. Пути вида
.../заголовок-../ или .../ответ:-да/ либо не создаются в Windows, либо дают
некрасивые URL. Скрипт прописывает slug явно.

Гарантии для слага:
  - только буквы, цифры и одиночные дефисы
  - никаких точек, скобок, кавычек, двоеточий, эмодзи
  - не начинается и не заканчивается дефисом
  - кириллица сохраняется, чтобы URL остались узнаваемыми

Два режима:
  --mode slug   (по умолчанию) заголовок не трогает, добавляет поле slug
  --mode strip  чистит сам заголовок (хвостовая пунктуация)

Файлы _index.md пропускаются: у них slug меняет адрес целого раздела.
По умолчанию ничего не пишет — только предпросмотр. Для записи --apply.
"""

import argparse
import re
import sys
from pathlib import Path

# title = "..." или title = '...'; внутри двойных кавычек допустимы \" и \\
TITLE_RE = re.compile(
    r"^(\s*title\s*=\s*)(\"((?:[^\"\\]|\\.)*)\"|'([^']*)')\s*$")
SLUG_RE = re.compile(r"^\s*slug\s*=", re.IGNORECASE)
SLUG_VALUE_RE = re.compile(
    r"^(\s*slug\s*=\s*)(\"((?:[^\"\\]|\\.)*)\"|'([^']*)')\s*$", re.IGNORECASE)

# всё, что не буква, не цифра, не пробел и не дефис — в слаге не место
UNSAFE_RE = re.compile(r"[^\w\s-]", re.UNICODE)
# хвостовая пунктуация и пробелы для режима strip
TAIL_RE = re.compile(r"[^\w)\]]+$|[.\u2026\s]+$", re.UNICODE)


def split_front_matter(text):
    """Возвращает (строки_фронтматтера, строки_остального) для TOML +++."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "+++":
        return None, None
    for i in range(1, len(lines)):
        if lines[i].strip() == "+++":
            return lines[1:i], lines[i + 1:]
    return None, None


def make_slug(title):
    """Чистый слаг: буквы, цифры, одиночные дефисы. Может вернуть ''."""
    # снимаем TOML-экранирование: \" \\ \n и т.п.
    slug = re.sub(r"\\(.)", r"\1", title)
    slug = slug.lower()
    slug = slug.replace("ё", "е")
    # подчёркивания и любые пробелы считаем разделителями
    slug = re.sub(r"[\s_]+", "-", slug)
    # пунктуация тоже разделитель, иначе "2.0" склеится в "20"
    slug = UNSAFE_RE.sub("-", slug)
    # схлопываем дефисы и срезаем по краям
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug


def needs_slug(title):
    """Нужен ли явный slug: в заголовке есть пунктуация или лишние пробелы."""
    if UNSAFE_RE.search(title):
        return True
    if title != title.strip():
        return True
    if re.search(r"\s{2,}|^-|-$", title):
        return True
    return False


def fallback_slug(path):
    """Если из заголовка слаг не собрался — берём имя папки поста."""
    slug = make_slug(path.parent.name)
    return slug or "post"


def process(path, mode):
    """Возвращает (новый_текст, старый_заголовок, результат) или None."""
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

        if mode == "strip":
            cleaned = TAIL_RE.sub("", value).strip()
            if not cleaned or cleaned == value:
                return None
            fm[idx] = f"{prefix}{quote}{cleaned}{quote}\n"
            note = cleaned
        else:
            # если slug уже есть — чистим его, а не пропускаем файл
            for sidx, sline in enumerate(fm):
                sm = SLUG_VALUE_RE.match(sline.rstrip("\n"))
                if not sm:
                    continue
                sprefix, squoted = sm.group(1), sm.group(2)
                svalue = sm.group(3) if sm.group(3) is not None else sm.group(4)
                clean = make_slug(svalue) or fallback_slug(path)
                if clean == svalue:
                    return None  # уже чистый
                fm[sidx] = f"{sprefix}{squoted[0]}{clean}{squoted[0]}\n"
                return ("+++\n" + "".join(fm) + "+++\n" + "".join(body),
                        f"slug: {svalue}", clean)

            if not needs_slug(value):
                return None
            slug = make_slug(value) or fallback_slug(path)
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
    ap.add_argument("--include-index", action="store_true",
                    help="обрабатывать также _index.md (меняет URL разделов)")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        sys.exit(f"Не найден каталог: {root}")

    changed = skipped_index = 0
    for path in sorted(root.glob(args.glob)):
        if path.name.startswith("_index.") and not args.include_index:
            skipped_index += 1
            continue
        result = process(path, args.mode)
        if result is None:
            continue
        new_text, old_title, note = result
        changed += 1
        print(f"\n{path}")
        print(f"  было:  {old_title}")
        print(f"  {'стало' if args.mode == 'strip' else 'slug '}: {note}")
        if args.apply:
            path.write_text(new_text, encoding="utf-8")

    print(f"\n{'Изменено' if args.apply else 'Будет изменено'} файлов: {changed}")
    if skipped_index:
        print(f"Пропущено _index.md: {skipped_index}")
    if changed and not args.apply:
        print("Это предпросмотр. Для записи запустите с --apply")


if __name__ == "__main__":
    main()