from flask import Flask, render_template, request, jsonify, send_from_directory
import vector_search
from bs4 import BeautifulSoup
import os

app = Flask(__name__)


def load_urls():
    """
    Загружает список URL из файла urls.txt.
    Каждая строка файла соответствует одному документу.
    """

    urls = []

    with open("urls.txt", "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if url:
                urls.append(url)

    return urls


def extract_text_from_html(path):
    """
    Извлекает чистый текст из HTML страницы.
    """

    if not os.path.exists(path):
        return ""

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # удаляем служебные теги
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")

    return text


def build_snippet(doc_id, query):
    """
    Возвращает фрагмент текста страницы, где встречается слово запроса.
    """

    page_path = os.path.join("pages", f"{doc_id}_page.html")

    text = extract_text_from_html(page_path)

    text_lower = text.lower()
    query_words = query.lower().split()

    for word in query_words:

        pos = text_lower.find(word)

        if pos != -1:

            start = max(0, pos - 80)
            end = min(len(text), pos + 80)

            snippet = text[start:end]

            return "..." + snippet + "..."

    return text[:160] + "..."


print("Загрузка индекса...")
document_vectors = vector_search.load_document_vectors()
idf_table = vector_search.load_idf_table()

print("Загрузка списка URL...")
urls = load_urls()

print("Документов:", len(document_vectors))


@app.route("/pages/<path:filename>")
def serve_page(filename):
    return send_from_directory("pages", filename)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search")
def search_api():

    query = request.args.get("q", "")

    if not query:
        return jsonify([])

    results = vector_search.search(query, document_vectors, idf_table)

    data = []

    for doc, score in results:

        # получаем номер документа
        doc_id = int(doc.split("_")[0])

        # получаем URL из списка
        if 1 <= doc_id <= len(urls):
            url = urls[doc_id - 1]
        else:
            url = "#"

        snippet = build_snippet(doc_id, query)
        data.append({
            "doc": f"Документ {doc_id}",
            "url": url,
            "score": score,
            "snippet": snippet
        })

    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)