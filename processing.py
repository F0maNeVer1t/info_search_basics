import os
import re
from bs4 import BeautifulSoup
import pymorphy3

PAGES_DIR = "pages"
TOKENS_DIR = "tokens"
LEMMAS_DIR = "lemmas"

os.makedirs(TOKENS_DIR, exist_ok=True)
os.makedirs(LEMMAS_DIR, exist_ok=True)

# Морфологический анализатор (лемматизация)
morph = pymorphy3.MorphAnalyzer()

# разрешаем только русские слова
word_re = re.compile(r"^[а-яё]+$", re.IGNORECASE)


def extract_from_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    # удаляем скрипты и стили
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Возвращаем весь текст страницы
    return soup.get_text(separator=" ")


# обработка каждого HTML-файла отдельно
for filename in os.listdir(PAGES_DIR):

    if not filename.endswith(".html"):
        continue

    path = os.path.join(PAGES_DIR, filename)

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    text = extract_from_html(html)

    words = re.findall(r"[А-Яа-яЁё]+", text)

    # токены только для одной страницы
    tokens_set = set()

    for w in words:
        w = w.lower()

        # отсекаем мусор
        if not word_re.match(w):
            continue

        parse = morph.parse(w)[0]

        """
        PREP — предлог
        CONJ — союз
        PRCL — частица
        INTJ — междометие
        """
        if parse.tag.POS in {"PREP", "CONJ", "PRCL", "INTJ"}:
            continue

        tokens_set.add(w)

    # группировка токенов по леммам для данной страницы
    lemmas = {}

    for token in tokens_set:
        p = morph.parse(token)[0]
        lemma = p.normal_form

        if lemma not in lemmas:
            lemmas[lemma] = []

        lemmas[lemma].append(token)

    base_name = os.path.splitext(filename)[0]

    tokens_path = os.path.join(TOKENS_DIR, base_name + "_tokens.txt")
    lemmas_path = os.path.join(LEMMAS_DIR, base_name + "_lemmas.txt")

    # сохраняем токены страницы
    with open(tokens_path, "w", encoding="utf-8") as f:
        for token in sorted(tokens_set):
            f.write(token + "\n")

    # сохраняем леммы страницы
    with open(lemmas_path, "w", encoding="utf-8") as f:
        for lemma in sorted(lemmas):
            tokens = sorted(lemmas[lemma])
            line = lemma + " " + " ".join(tokens)
            f.write(line + "\n")

    print(f"{filename} — готово. Токенов: {len(tokens_set)}, лемм: {len(lemmas)}")

print("Обработка завершена.")