#!/usr/bin/env python3
"""
Приводит слаги Hugo к чистому и стабильному виду слово-слово-слово.

Hugo строит адрес страницы из имени файла или из поля slug и сохраняет в нём
пунктуацию как есть. Пути вида .../заголовок-../ не создаются в Windows,
а .../ответ:-да/ даёт некорректный URL. Скрипт прописывает slug явно.

Что делается со слагом:
  - Unicode-нормализация NFKC (полноширинные символы, лигатуры, № )
  - удаление невидимок: BOM, zero-width, мягкий перенос, LRM/RLM, управляющие
  - любые пробелы, включая неразрывные и тонкие, считаются разделителем
  - вся пунктуация тоже разделитель, чтобы "2.0" не склеилось в "20"
  - комбинирующие диакритические знаки отбрасываются
  - ё приводится к е
  - схлопывание повторных дефисов, обрезка по краям
  - длина ограничена, обрезка по границе слова (лимит пути в Windows)
  - зарезервированные в Windows имена (con, nul, com1...) обезвреживаются
  - коллизии внутри одного раздела разводятся суффиксом -2, -3

Режимы:
  --mode slug   (по умолчанию) заголовок не трогает, прописывает slug
  --mode strip  чистит хвостовую пунктуацию в самом заголовке

Файлы _index.md пропускаются: у них slug меняет адрес целого раздела.
По умолчанию только предпросмотр. Для записи --apply.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

# title = "..." или title = '...'; внутри двойных кавычек допустимы \" и \\
TITLE_RE = re.compile(
    r"^(\s*title\s*=\s*)(\"((?:[^\"\\]|\\.)*)\"|'([^']*)')\s*$")
SLUG_VALUE_RE = re.compile(
    r"^(\s*slug\s*=\s*)(\"((?:[^\"\\]|\\.)*)\"|'([^']*)')\s*$", re.IGNORECASE)

# невидимые символы: мягкий перенос, zero-width, направление текста, BOM
INVISIBLE_RE = re.compile(
    "[\u00ad\u200c\u200d\u200e\u200f\u2060\ufeff]")
# любой невидимый символ, из-за которого заголовку нужен явный слаг
INVISIBLE_ANY_RE = re.compile(
    "[\u00ad\u200b\u200c\u200d\u200e\u200f\u2028\u2029\u2060\ufeff]")
# всё, что не буква, не цифра, не пробел и не дефис
UNSAFE_RE = re.compile(r"[^\w\s-]", re.UNICODE)
# хвостовая пунктуация для режима strip
TAIL_RE = re.compile(r"[^\w)\]]+$", re.UNICODE)

# имена устройств, недопустимые как имена папок в Windows
RESERVED = {"con", "prn", "aux", "nul"}
RESERVED |= {f"com{i}" for i in range(10)}
RESERVED |= {f"lpt{i}" for i in range(10)}

MAX_SLUG_LEN = 80


def split_front_matter(text):
    """Возвращает (строки_фронтматтера, строки_остального) для TOML +++."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "+++":
        return None, None
    for i in range(1, len(lines)):
        if lines[i].strip() == "+++":
            return lines[1:i], lines[i + 1:]
    return None, None


def make_slug(raw):
    """Строит безопасный слаг. Может вернуть '' — тогда нужен запасной."""
    if not raw:
        return ""

    # снимаем TOML-экранирование: \" \\ и прочее
    s = re.sub(r"\\(.)", r"\1", raw)

    # приводим совместимые формы: лигатуры, полноширинные цифры, №
    s = unicodedata.normalize("NFKC", s)

    # zero-width пробел и разделители строк — это границы слов
    s = re.sub("[\u200b\u2028\u2029]", " ", s)
    # остальные невидимки просто удаляем
    s = INVISIBLE_RE.sub("", s)

    # любые пробельные символы, включая \t и \n, приводим к обычному пробелу
    s = re.sub(r"\s", " ", s)
    # только теперь убираем управляющие символы
    s = "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

    # й и ё — самостоятельные буквы, разложение Unicode их бы разрушило
    s = s.replace("й", "\x01").replace("Й", "\x01")
    s = s.replace("ё", "\x02").replace("Ё", "\x02")

    # отбрасываем комбинирующие знаки: é -> e
    s = "".join(ch for ch in unicodedata.normalize("NFD", s)
                if unicodedata.category(ch) != "Mn")
    s = unicodedata.normalize("NFC", s)

    s = s.replace("\x01", "й").replace("\x02", "е")
    s = s.lower()

    # разделители: пробелы любого вида и подчёркивания, затем вся пунктуация
    s = re.sub(r"[\s_]+", "-", s)
    s = UNSAFE_RE.sub("-", s)

    s = re.sub(r"-{2,}", "-", s).strip("-")

    # ограничиваем длину по границе слова
    if len(s) > MAX_SLUG_LEN:
        s = s[:MAX_SLUG_LEN]
        if "-" in s:
            s = s[:s.rindex("-")]
        s = s.strip("-")

    if s in RESERVED:
        s = f"{s}-post"

    return s


def needs_slug(title):
    """Нужен ли явный slug для этого заголовка."""
    if UNSAFE_RE.search(title) or INVISIBLE_ANY_RE.search(title):
        return True
    if title != title.strip():
        return True
    if re.search(r"\s{2,}|^-|-$", title):
        return True
    if len(title) > MAX_SLUG_LEN:
        return True
    if make_slug(title) in RESERVED:
        return True
    return False


def fallback_slug(path):
    """Если из заголовка слаг не собрался — берём имя папки или файла."""
    base = path.parent.name if path.stem == "index" else path.stem
    return make_slug(base) or "post"


def section_of(path):
    """Каталог, в котором Hugo разместит страницу — область уникальности."""
    return path.parent.parent if path.stem == "index" else path.parent


def plan(path, mode):
    """Готовит изменение файла, не фиксируя окончательный слаг."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        print(f"  !! пропущен {path}: {e}", file=sys.stderr)
        return None

    fm, body = split_front_matter(text)
    if fm is None:
        return None

    title_m = title_idx = None
    for idx, line in enumerate(fm):
        m = TITLE_RE.match(line.rstrip("\n"))
        if m:
            title_idx, title_m = idx, m
            break
    if title_m is None:
        return None

    title_val = title_m.group(3) if title_m.group(3) is not None else title_m.group(4)

    if mode == "strip":
        cleaned = TAIL_RE.sub("", title_val).strip()
        if not cleaned or cleaned == title_val:
            return None
        prefix, quoted = title_m.group(1), title_m.group(2)
        q = quoted[0]
        fm = list(fm)
        fm[title_idx] = f"{prefix}{q}{cleaned}{q}\n"
        return ("strip", title_val, cleaned, fm, body, None)

    # режим slug: сначала смотрим, есть ли уже поле slug
    for sidx, sline in enumerate(fm):
        sm = SLUG_VALUE_RE.match(sline.rstrip("\n"))
        if not sm:
            continue
        svalue = sm.group(3) if sm.group(3) is not None else sm.group(4)
        clean = make_slug(svalue) or fallback_slug(path)
        if clean == svalue:
            return None  # уже чистый
        return ("slug-fix", f"slug: {svalue}", clean, fm, body, sidx)

    if not needs_slug(title_val):
        return None
    new = make_slug(title_val) or fallback_slug(path)
    return ("slug-add", title_val, new, fm, body, title_idx)


def render(fm, body, slug, action, idx):
    """Собирает итоговый текст файла с окончательным слагом."""
    fm = list(fm)
    if action == "slug-fix":
        m = SLUG_VALUE_RE.match(fm[idx].rstrip("\n"))
        prefix, quoted = m.group(1), m.group(2)
        fm[idx] = f"{prefix}{quoted[0]}{slug}{quoted[0]}\n"
    elif action == "slug-add":
        line = fm[idx]
        fm[idx] = line if line.endswith("\n") else line + "\n"
        fm.insert(idx + 1, f'slug = "{slug}"\n')
    return "+++\n" + "".join(fm) + "+++\n" + "".join(body)


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

    all_files = sorted(root.glob(args.glob))
    files = [p for p in all_files
             if args.include_index or not p.name.startswith("_index.")]
    skipped_index = len(all_files) - len(files)

    # занятые слаги — в том числе у файлов, которые мы не трогаем
    taken = {}
    plans = []
    for path in files:
        p = plan(path, args.mode)
        if p is None:
            taken.setdefault(section_of(path), set()).add(fallback_slug(path))
        else:
            plans.append((path, p))

    changed = collisions = 0
    for path, (action, old, new, fm, body, idx) in plans:
        if action == "strip":
            text = "+++\n" + "".join(fm) + "+++\n" + "".join(body)
            slug = new
        else:
            sec = taken.setdefault(section_of(path), set())
            slug, n = new, 1
            while slug in sec:
                n += 1
                slug = f"{new}-{n}"
            if slug != new:
                collisions += 1
            sec.add(slug)
            text = render(fm, body, slug, action, idx)

        changed += 1
        print(f"\n{path}")
        print(f"  было:  {old}")
        print(f"  {'стало' if action == 'strip' else 'slug '}: {slug}")
        if args.apply:
            path.write_text(text, encoding="utf-8")

    print(f"\n{'Изменено' if args.apply else 'Будет изменено'} файлов: {changed}")
    if collisions:
        print(f"Разведено совпадений суффиксом: {collisions}")
    if skipped_index:
        print(f"Пропущено _index.md: {skipped_index}")
    if changed and not args.apply:
        print("Это предпросмотр. Для записи запустите с --apply")


if __name__ == "__main__":
    main()