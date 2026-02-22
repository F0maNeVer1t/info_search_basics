import os
import re
import json
from bs4 import BeautifulSoup
import pymorphy3

PAGES_DIR = "pages"
INDEX_FILE = "inverted_index.json"

morph = pymorphy3.MorphAnalyzer()


def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator=" ")


word_re = re.compile(r"[А-Яа-яЁё]+")


def tokenize_and_lemmatize(text):
    words = word_re.findall(text)

    lemmas = set()

    for w in words:
        w = w.lower()
        p = morph.parse(w)[0]

        if p.tag.POS in {"PREP", "CONJ", "PRCL", "INTJ"}:
            continue

        lemmas.add(p.normal_form)

    return lemmas


def build_index():
    inverted_index = {}
    all_docs = set()

    for filename in os.listdir(PAGES_DIR):
        if not filename.endswith(".html"):
            continue

        doc_id = filename
        all_docs.add(doc_id)

        path = os.path.join(PAGES_DIR, filename)

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()

        text = extract_text(html)
        lemmas = tokenize_and_lemmatize(text)

        for lemma in lemmas:
            inverted_index.setdefault(lemma, set()).add(doc_id)

    return inverted_index, all_docs


def save_index(inverted_index, all_docs):
    data = {
        "index": {k: list(v) for k, v in inverted_index.items()},
        "all_docs": list(all_docs)
    }

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_index():
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    inverted_index = {k: set(v) for k, v in data["index"].items()}
    all_docs = set(data["all_docs"])

    return inverted_index, all_docs


OPERATORS = {"AND", "OR", "NOT"}

PRIORITY = {
    "NOT": 3,
    "AND": 2,
    "OR": 1
}


def normalize_query(query):
    query = query.replace("(", " ( ").replace(")", " ) ")
    return query.split()


def to_rpn(tokens):
    output = []
    stack = []

    for token in tokens:
        t = token.upper()

        if t in OPERATORS:
            while stack and stack[-1] in OPERATORS and PRIORITY[stack[-1]] >= PRIORITY[t]:
                output.append(stack.pop())
            stack.append(t)

        elif token == "(":
            stack.append(token)

        elif token == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            stack.pop()

        else:
            output.append(token)

    while stack:
        output.append(stack.pop())

    return output


def term_to_docs(term):
    term = term.lower()
    p = morph.parse(term)[0]
    lemma = p.normal_form
    return inverted_index.get(lemma, set())


def eval_rpn(rpn):
    stack = []

    for token in rpn:
        t = token.upper()

        if t == "AND":
            b = stack.pop()
            a = stack.pop()
            stack.append(a & b)

        elif t == "OR":
            b = stack.pop()
            a = stack.pop()
            stack.append(a | b)

        elif t == "NOT":
            a = stack.pop()
            stack.append(all_docs - a)

        else:
            stack.append(term_to_docs(token))

    return stack.pop() if stack else set()


if not os.path.exists(INDEX_FILE):
    print("Файл индекса не найден. Строим индекс...")

    inverted_index, all_docs = build_index()
    save_index(inverted_index, all_docs)

    print("Индекс построен и сохранён.")

else:
    print("Загружаем индекс из файла...")
    inverted_index, all_docs = load_index()
    print("Индекс загружен.")


while True:
    query = input("\nВведите запрос (пустая строка — выход): ")

    if not query.strip():
        break

    tokens = normalize_query(query)
    rpn = to_rpn(tokens)

    result = eval_rpn(rpn)

    print("Найдено документов:", len(result))

    for doc in sorted(result):
        print(" ", doc)
