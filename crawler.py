import requests
import os

# файл со списком ссылок
INPUT_FILE = "urls.txt"

# папка, куда будут сохраняться страницы
OUTPUT_DIR = "pages"

# файл с индексом (номер файла -> ссылка)
INDEX_FILE = "index.txt"

# создаём папку pages, если её ещё нет
os.makedirs(OUTPUT_DIR, exist_ok=True)

# заголовки запроса (чтобы выглядеть как обычный браузер)
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
}

# читаем все ссылки
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

# счётчик файлов
file_number = 1

# записываем в index.txt
with open(INDEX_FILE, "w", encoding="utf-8") as downloaded_pages:
    for url in urls:
        try:
            # HTTP-запрос
            r = requests.get(url, headers=headers, timeout=15)

            # получаем тип содержимого ответа
            content_type = r.headers.get("Content-Type", "")

            # если не HTML — скип
            if "text/html" not in content_type:
                print(f"Пропущено (не html): {url}")
                continue

            # имя файла странички
            filename = os.path.join(OUTPUT_DIR, f"{file_number}_page.html")

            # сохраняем HTML-страницу в файл
            with open(filename, "wb") as f_out:
                f_out.write(r.content)

            # соответствие номера файла и ссылки
            downloaded_pages.write(f"{file_number}_page {url}\n")

            print(f"OK: {file_number} -> {url}")
            file_number += 1

        except Exception as e:
            # если скачать страницу не удалось - ошибка
            print(f"Ошибка: {url} : {e}")