import os
import re
import math
from collections import Counter, defaultdict
from bs4 import BeautifulSoup
import pymorphy3

PAGES_DIR = "pages"

# Директории для выходных файлов
OUT_TERMS_DIR = "tfidf_terms"
OUT_LEMMAS_DIR = "tfidf_lemmas"

os.makedirs(OUT_TERMS_DIR, exist_ok=True)
os.makedirs(OUT_LEMMAS_DIR, exist_ok=True)

# Морфологический анализатор
morph = pymorphy3.MorphAnalyzer()

# Регулярное выражение для проверки, что токен — русское слово
word_re = re.compile(r"^[а-яё]+$", re.IGNORECASE)


def extract_from_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    # удаляем скрипты и стили
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Возвращаем весь текст страницы
    return soup.get_text(separator=" ")


# 1. Считывание документов и подсчёт частот

# Счётчик терминов по документам
docs_tokens = {}

# Счётчик лемм по документам
docs_lemmas = {}

# Общее число терминов в документе
docs_len = {}

# Документные частоты (df)
df_terms = defaultdict(set)
df_lemmas = defaultdict(set)

for filename in os.listdir(PAGES_DIR):

    if not filename.endswith(".html"):
        continue

    path = os.path.join(PAGES_DIR, filename)

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    # Извлекаем чистый текст страницы
    text = extract_from_html(html)

    # Выделяем все потенциальные слова
    words = re.findall(r"[А-Яа-яЁё]+", text)

    token_counter = Counter()
    lemma_counter = Counter()

    total_terms = 0

    for w in words:
        w = w.lower()

        # Проверяем, что токен состоит только из русских букв
        if not word_re.match(w):
            continue

        # Морфологический разбор
        p = morph.parse(w)[0]

        # Отбрасываем служебные части речи
        if p.tag.POS in {"PREP", "CONJ", "PRCL", "INTJ"}:
            continue

        lemma = p.normal_form

        # Увеличиваем счётчики
        token_counter[w] += 1
        lemma_counter[lemma] += 1
        total_terms += 1

    # Сохраняем результаты для документа
    docs_tokens[filename] = token_counter
    docs_lemmas[filename] = lemma_counter
    docs_len[filename] = total_terms

    # Обновляем df для терминов
    for t in token_counter:
        df_terms[t].add(filename)

    # Обновляем df для лемм
    for l in lemma_counter:
        df_lemmas[l].add(filename)


# 2. Подсчёт idf

# Общее число документов
N = len(docs_tokens)

idf_terms = {}
idf_lemmas = {}

for term, docs in df_terms.items():
    idf_terms[term] = math.log(N / len(docs))

for lemma, docs in df_lemmas.items():
    idf_lemmas[lemma] = math.log(N / len(docs))

# 3. Запись tf-idf для каждого документа

for doc in docs_tokens:

    base = os.path.splitext(doc)[0]

    # Термины
    out_terms_path = os.path.join(
        OUT_TERMS_DIR,
        base + "_terms_tfidf.txt"
    )

    with open(out_terms_path, "w", encoding="utf-8") as f:

        total = docs_len[doc]

        # Если документ пустой после фильтрации
        if total == 0:
            continue

        for term, cnt in docs_tokens[doc].items():
            # tf = относительная частота термина в документе
            tf = cnt / total

            # idf термина
            idf = idf_terms[term]

            # tf-idf
            tfidf = tf * idf

            # Формат как было сказано в задании
            f.write(f"{term} {idf} {tfidf}\n")

    # Леммы
    out_lemmas_path = os.path.join(
        OUT_LEMMAS_DIR,
        base + "_lemmas_tfidf.txt"
    )

    with open(out_lemmas_path, "w", encoding="utf-8") as f:

        total = docs_len[doc]

        if total == 0:
            continue

        for lemma, cnt in docs_lemmas[doc].items():
            """
            tf для леммы — сумма всех вхождений её словоформ,
            делённая на общее число терминов документа
            """
            tf = cnt / total

            # idf леммы
            idf = idf_lemmas[lemma]

            # tf-idf
            tfidf = tf * idf

            # Тот же самый формат
            f.write(f"{lemma} {idf} {tfidf}\n")

print("Задание выполнено.")
