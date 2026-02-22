import os
import re
from bs4 import BeautifulSoup
import pymorphy3

OUTPUT_DIR = "pages"

morph = pymorphy3.MorphAnalyzer()

tokens_set = set()

# разрешаем только русские слова
word_re = re.compile(r"^[а-яё]+$", re.IGNORECASE)


def extract_from_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    # удаляем скрипты и стили
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return soup.get_text(separator=" ")


# ---------- ШАГ 1. Токенизация ----------

for filename in os.listdir(OUTPUT_DIR):
    if not filename.endswith(".html"):
        continue

    path = os.path.join(OUTPUT_DIR, filename)

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    text = extract_from_html(html)

    words = re.findall(r"[А-Яа-яЁё]+", text)

    for w in words:
        w = w.lower()

        # отсекаем мусор
        if not word_re.match(w):
            continue

        parse = morph.parse(w)[0]

        '''
        PREP — предлог
        CONJ — союз
        PRCL — частица
        INTJ — междометие
        '''
        if parse.tag.POS in {"PREP", "CONJ", "PRCL", "INTJ"}:
            continue

        tokens_set.add(w)


# группируем по леммам
lemmas = {}

for token in tokens_set:
    p = morph.parse(token)[0]
    lemma = p.normal_form

    if lemma not in lemmas:
        lemmas[lemma] = []

    lemmas[lemma].append(token)


# сохраняем результаты
with open("tokens.txt", "w", encoding="utf-8") as f:
    for token in sorted(tokens_set):
        f.write(token + "\n")


with open("lemmas.txt", "w", encoding="utf-8") as f:
    for lemma in sorted(lemmas):
        tokens = sorted(lemmas[lemma])
        line = lemma + " " + " ".join(tokens)
        f.write(line + "\n")


print("Готово.")
print(f"Количество уникальных токенов: {len(tokens_set)}")
print(f"Количество лемм: {len(lemmas)}")