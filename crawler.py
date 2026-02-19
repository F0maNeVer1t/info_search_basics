import requests
import os

INPUT_FILE = "urls.txt"
OUTPUT_DIR = "pages"
INDEX_FILE = "index.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
}

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

file_number = 1

with open(INDEX_FILE, "w", encoding="utf-8") as downloaded_pages:
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)

            content_type = r.headers.get("Content-Type", "")

            if "text/html" not in content_type:
                print(f"Пропущено (не html): {url}")
                continue

            filename = os.path.join(OUTPUT_DIR, f"{file_number}_page.html")

            with open(filename, "wb") as f_out:
                f_out.write(r.content)

            downloaded_pages.write(f"{file_number}_page {url}\n")

            print(f"OK: {file_number} -> {url}")

            file_number += 1

        except Exception as e:
            print(f"Ошибка: {url} : {e}")