This script `generate-gallery-remote.js` is a **pre-processor** for your Hugo static site generator. Since you want to keep large image files off GitHub and your local machine, the script acts as a bridge: it "looks" at your remote storage, sees what is there, and writes a local "map" (`gallery.json`) so Hugo knows how to link those remote files.

---

## 🛠 How the Script Works (The Logic)

The script follows a 4-step process to automate your workflow:

### 1. The Local Walk

The script starts at `content/news`. Instead of scanning every single folder (which takes time), it looks at the immediate subdirectories.

* **Filtering:** If you set `TARGET_YEAR = "2026"`, it immediately ignores folders like `2024` or `2025`.
* **Identification:** It uses `os.walk` to find "Post Folders." It identifies a post folder by checking if it contains an `.md` file (your Hugo content).

### 2. URL Construction

Once it finds a post, e.g., `content/news/2026/03/my-new-event`, it calculates the matching remote URL:
`https://files.groznet.com/poiskchr/news/2026/03/my-new-event/images/`

### 3. Remote Scraping (The "Bot" Phase)

The script "visits" that URL using the `requests` library.

* It reads the HTML code returned by your server (the Directory Index).
* It uses **BeautifulSoup** to find every `<a>` (link) tag.
* It filters these links to only keep files ending in `.jpg`, `.png`, etc., while ignoring system links like `../` (Parent Directory).

### 4. JSON Generation

Finally, it takes that list of filenames and writes a `gallery.json` file **locally** inside your post folder.

* **Natural Sorting:** It ensures `2.jpg` comes before `10.jpg`.
* **Metadata:** It includes the `remote_base_url` and a direct link to the `feature.jpg`.

---

## 🚀 How to Use It

### Regular Workflow

1. **Upload Media:** Upload your `feature.jpg` and `images/` folder to your server (`files.groznet.com`).
2. **Create Post:** Create your Hugo post locally (e.g., `hugo new news/2026/03/my-post/index.md`).
3. **Run Script:** Execute the Python script:
```bash
python scripts/generate_gallery.py

```


4. **Build/Deploy:** Run `hugo` and push to GitHub. Your site now "knows" where the images are.

### Changing the Focus

* **To update everything:** Set `TARGET_YEAR = None` and `FORCE_REFRESH = True`.
* **To update only today's work:** Set `TARGET_YEAR = "2026"` and `FORCE_REFRESH = False`. This will only process new posts that don't have a JSON file yet.

---

## 📑 Summary of the `gallery.json` Structure

After running, your Hugo templates can access the data like this:

| Key | Value Description |
| --- | --- |
| `remote_base_url` | The full path to the remote images folder. |
| `featured_image` | The full path to the main post image. |
| `images` | An array (list) of all filenames found in the remote gallery. |

---

## 🛡 Security Note

Because the script relies on **Directory Indexing**, anyone who guesses the URL can see the list of your files. As we discussed, you can mitigate this by:

* Using **IP Whitelisting** on your Nginx/Apache server to only allow your IP to see the directory list.
* Using **randomized folder names** for highly sensitive content.

Would you like me to write the **Hugo Shortcode** now? This would be the actual HTML/Go template code you paste into your site so the gallery actually appears on the page.