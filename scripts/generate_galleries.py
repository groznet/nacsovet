import os
import json
import re

# ==========================================
# SITE CONFIGURATION
# ==========================================
SITE_SLUG = "nacsovet"
MEDIA_SERVER_BASE = "https://files.groznet.com"
CONTENT_SECTION = "news"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, f"../content/{CONTENT_SECTION}"))

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif', '.svg')

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def scan_images_in_dir(target_dir):
    """Scans a directory for images (non-recursive). Returns list of filenames."""
    if not os.path.exists(target_dir):
        return []
    images = []
    for entry in os.scandir(target_dir):
        if entry.is_file() and entry.name.lower().endswith(IMAGE_EXTENSIONS):
            images.append(entry.name)
    return images

def process_post(post_dir):
    rel_post_path = os.path.relpath(post_dir, CONTENT_DIR).replace('\\', '/')
    
    # Check for direct root images and nested images/ folder
    root_images = scan_images_in_dir(post_dir)
    images_subdir = os.path.join(post_dir, "images")
    sub_images = scan_images_in_dir(images_subdir)

    featured_img_name = None
    gallery_images = []
    has_sub_images = len(sub_images) > 0

    # 1. Look for explicit featured image in the post root
    for img in root_images:
        name_no_ext, _ = os.path.splitext(img.lower())
        if name_no_ext == "featured":
            featured_img_name = img
            break

    # 2. Determine gallery images & fallback featured image
    if has_sub_images:
        # Gallery images live inside images/ folder
        gallery_images = sub_images
        # If no explicit featured image in root, pick the first image from images/
        if not featured_img_name and gallery_images:
            gallery_images.sort(key=natural_sort_key)
            featured_img_name = f"images/{gallery_images.pop(0)}"
    else:
        # Gallery images live directly in post root
        for img in root_images:
            if img != featured_img_name:
                gallery_images.append(img)
        
        # Fallback if no explicit featured image was found
        if not featured_img_name and gallery_images:
            gallery_images.sort(key=natural_sort_key)
            featured_img_name = gallery_images.pop(0)

    # 3. Build remote URLs with proper paths
    post_remote_base = f"{MEDIA_SERVER_BASE}/{SITE_SLUG}/{CONTENT_SECTION}/{rel_post_path}"
    
    if has_sub_images:
        remote_base_url = f"{post_remote_base}/images/"
    else:
        remote_base_url = f"{post_remote_base}/"

    featured_img_url = f"{post_remote_base}/{featured_img_name}" if featured_img_name else ""

    gallery_images.sort(key=natural_sort_key)

    output_data = {
        "remote_base_url": remote_base_url,
        "featured_image": featured_img_url,
        "images": gallery_images
    }

    # 4. Read existing media.json if present to check for changes
    json_path = os.path.join(post_dir, "media.json")
    existing_data = None
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            existing_data = None

    # Write/Update file if missing or content changed
    if existing_data != output_data:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"🔄 Updated: {CONTENT_SECTION}/{rel_post_path}/media.json ({len(gallery_images)} images)")
    else:
        print(f"✔️ Up to date: {CONTENT_SECTION}/{rel_post_path}/media.json")

if __name__ == '__main__':
    print(f"🚀 Scanning local bundle media for site: [{SITE_SLUG}]...")
    
    if not os.path.exists(CONTENT_DIR):
        print(f"❌ Error: Content directory not found at {CONTENT_DIR}")
        exit(1)

    for root, dirs, files in os.walk(CONTENT_DIR):
        if any(f.endswith('.md') and not f.startswith('_index') for f in files):
            process_post(root)