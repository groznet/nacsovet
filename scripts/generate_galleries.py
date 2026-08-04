import os
import json
import re

# ==========================================
# SITE CONFIGURATION
# ==========================================
SITE_SLUG = "nacsovet"
MEDIA_SERVER_BASE = "https://files.groznet.com"
CONTENT_SECTION = "news"

# Path setup relative to script execution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, f"../content/{CONTENT_SECTION}"))

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif', '.svg')

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def process_post(post_dir):
    rel_post_path = os.path.relpath(post_dir, CONTENT_DIR).replace('\\', '/')
    post_remote_base = f"{MEDIA_SERVER_BASE}/{SITE_SLUG}/{CONTENT_SECTION}/{rel_post_path}"
    
    featured_img_name = None
    gallery_images = []

    # Scan all files directly inside post_dir
    for entry in os.scandir(post_dir):
        if entry.is_file() and entry.name.lower().endswith(IMAGE_EXTENSIONS):
            name_no_ext, _ = os.path.splitext(entry.name.lower())
            
            # Explicitly match featured image
            if name_no_ext == "featured":
                featured_img_name = entry.name
            else:
                gallery_images.append(entry.name)

    # Fallback: if no "featured.*" exists, use the first image as featured
    if not featured_img_name and gallery_images:
        gallery_images.sort(key=natural_sort_key)
        featured_img_name = gallery_images.pop(0)

    featured_img_url = f"{post_remote_base}/{featured_img_name}" if featured_img_name else ""

    # Generate gallery.json
    if gallery_images or featured_img_url:
        gallery_images.sort(key=natural_sort_key)
        
        output_data = {
            "remote_base_url": f"{post_remote_base}/",
            "featured_image": featured_img_url,
            "images": gallery_images
        }

        json_path = os.path.join(post_dir, "gallery.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)

        print(f"✅ Generated: {CONTENT_SECTION}/{rel_post_path}/gallery.json ({len(gallery_images)} gallery images)")

if __name__ == '__main__':
    print(f"🚀 Scanning local bundle media for site: [{SITE_SLUG}]...")
    
    if not os.path.exists(CONTENT_DIR):
        print(f"❌ Error: Content directory not found at {CONTENT_DIR}")
        exit(1)

    for root, dirs, files in os.walk(CONTENT_DIR):
        if any(f.endswith('.md') and not f.startswith('_index') for f in files):
            process_post(root)