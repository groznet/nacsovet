# CLAUDE.md

Instructions for Claude when importing new VK posts into this Hugo site as news posts. **Text only**: media is handled manually by the user.

## Source

- VK page: **https://vk.ru/id196339167**
- Individual posts: `https://vk.ru/wall196339167_<post_id>`
- Use the Claude in Chrome browser tools. The user's Chrome is already logged in to vk.ru, so don't log in or ask for credentials.
- **If no browser tool is available, stop right away** and tell the user. Don't fall back to WebFetch.
- Import only this page's own wall posts. Ignore ads, recommendations, other profiles and communities.

## Scope: text only

- Create only the post folder and its `index.md` (front matter + text).
- **Don't** download, save or reference images, videos or any other media.
- **Don't** create `media.json` or run `scripts/generate_media_json.py`. The user creates these manually.
- **Don't** add `![](...)` image lines or video placeholders to the body.

## Existing format: always match it

New posts must look exactly like the posts already on the site. Before creating anything, open 2–3 of the most recent existing `index.md` files and copy their format exactly.

- **Folder:** `content/news/YYYY/MM/DD_HH-MM_196339167_<post_id>/index.md`
  - Example: `content/news/2026/09/10_18-58_196339167_10291/index.md`
  - `DD_HH-MM` is the VK publish day and time. `<post_id>` is the VK post id.
- **Front matter:** use the same fields, field order, date format and timezone offset as the existing posts, including `author = "Муса Дунаев"`. Don't add new fields or change the offset.
- **Slug:** don't write it by hand. `scripts/add_slugs.py` adds it.
- **Body:** the cleaned-up post text only.
  - No `[Источник](...)` link.
  - No `vk.ru/wall...` URLs.
- Never edit `_index.md` files.

## Step 1: Find the cutoff on the site

1. In `content/news/`, go to the highest year folder, then the highest month folder inside it.
2. Read the `date` of every `index.md` in that month and take the most recent one. Don't trust folder order alone. If the month looks empty or incomplete, check the previous month too.
3. This is the **cutoff post**. Note its date, the first lines of its text, and the VK post id from its folder name (for example, `10291` in `10_18-58_196339167_10291`).

## Step 2: Find the cutoff post on VK

1. Open https://vk.ru/id196339167 and go to the wall.
2. Skip the **pinned post** at the top, because it's out of date order.
3. Scroll down until you reach the cutoff post. Match it by post id (in the post's link), and confirm the match with its date and text.
4. Posts **above** it are new and need importing. The cutoff post itself and everything below it are already on the site, so don't import them again.
5. If you scroll past the cutoff date without finding it, stop and tell the user.

## Step 3: Import new posts (text only)

Work **oldest first**, from the post just above the cutoff up to the newest post. Process at most ~10 posts per run, then report and let the user start the next batch.

For each post:

1. **Open the post itself** (`https://vk.ru/wall196339167_<id>`) to get the full text. Don't use the truncated wall preview ("Показать ещё").
2. **Date and time:** get the exact publish time from the post by hovering or opening the timestamp. VK shows forms like `сегодня в 14:05`, `вчера в 9:12`, `26 сен в 10:00` or a full date. Convert it to the site's existing date format.
3. **Folder:** create `content/news/YYYY/MM/DD_HH-MM_196339167_<id>/index.md`. If the folder already exists, skip the post and list it for the user.
4. **Front matter:** match the existing posts (see above). Write a short, natural `title` that summarizes the post, in the post's language.
5. **Text:** clean it up into Markdown (paragraphs, lists). Don't change the meaning or add facts. Remove VK leftovers such as likes, views, "Показать ещё" and timestamps.

Skip these posts and list them for the user:
- reposts of other people's or communities' posts;
- posts with no text (media-only posts);
- anything you're unsure about.

## Step 4: Slugs and git

Only after the batch has been imported successfully, run this from the site root:

```bash
python scripts/add_slugs.py
```

- If the script fails, **stop**. Show the error and don't commit.
- Run `git status` and confirm that only the expected new `index.md` files changed. If other files changed unexpectedly, stop and tell the user.

Then:

```bash
git add .
git commit -m "Add new posts"
git push
```

## When finished

Report briefly:
- the posts imported (date, title and folder for each), so the user knows where to add media;
- anything skipped (reposts, media-only posts, already existing folders);
- the script result and whether the push succeeded;
- whether more new posts are left for the next batch.

## Things NOT to do

- Don't import posts at or before the cutoff.
- Don't download or handle any media.
- Don't create `media.json` or run `generate_media_json.py`.
- Don't change the existing folder naming, front matter format, timezone offset or author.
- Don't write `slug` by hand.
- Don't put source links or VK wall URLs in the body.
- Don't use WebFetch as a substitute for the browser.
- Don't commit if the script failed or `git status` shows unexpected changes.
- Don't hand-edit `_index.md` files.
- Don't make up dates, titles or text.