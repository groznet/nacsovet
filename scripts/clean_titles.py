import os
import re

content_dir = r"content"

for root, _, files in os.walk(content_dir):
    for file in files:
        if file.endswith(".md"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Target the title line safely across raw text
            match = re.search(r'^title\s*=\s*["\'](.*?)["\']?\s*$', content, re.MULTILINE)
            if match:
                raw_title = match.group(1)

                # 1. Clean internal backslashes and quotes
                clean_title = raw_title.replace(r'\"', '"').replace('"', '"')
                
                # 2. Strip trailing dots, spaces, and harmful Windows symbols from the end
                clean_title = re.sub(r'[\s\.\!\?\)\(\[\]\{\}\"\'\,\:\;\-\_\~\#\%\&\*\+\=\<\>\/\@\^\$\`]+$', '', clean_title)

                # 3. Format using single quotes so internal quotes don't break TOML
                old_line = match.group(0)
                new_line = f"title = '{clean_title}'"

                if old_line != new_line:
                    new_content = content.replace(old_line, new_line)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Fixed: {file}")