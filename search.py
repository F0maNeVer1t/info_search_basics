import os
import re
import json
from bs4 import BeautifulSoup
import pymorphy3

OUTPUT_DIR = "pages"

# хранит инвертированный индекс
INDEX_FILE = "inverted_index.json"

# Морфологический анализатор (лемматизация)
morph = pymorphy3.MorphAnalyzer()


def extract_text(html):
    # Извлекает чистый текст из HTML.
    soup = BeautifulSoup(html, "html.parser")

    # Удаляем служебные теги
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Возвращаем весь текст страницы
    return soup.get_text(separator=" ")


# Регулярное выражение для выделения русских слов
word_re = re.compile(r"[А-Яа-яЁё]+")


def tokenize_and_lemmatize(text):
    words = word_re.findall(text)

    lemmas = set()

    for w in words:
        w = w.lower()

        # Морфологический разбор слова
        p = morph.parse(w)[0]

        # Отбрасываем предлоги, союзы, частицы, междометия
        if p.tag.POS in {"PREP", "CONJ", "PRCL", "INTJ"}:
            continue

        # Добавляем лемму
        lemmas.add(p.normal_form)

    return lemmas


def build_index():
    """
    Строит инвертированный индекс по HTML-файлам.

    Возвращает:
    inverted_index — словарь {лемма -> множество документов}
    all_docs — множество всех документов
    """
    inverted_index = {}
    all_docs = set()

    for filename in os.listdir(OUTPUT_DIR):
        if not filename.endswith(".html"):
            continue

        doc_id = filename
        all_docs.add(doc_id)

        path = os.path.join(OUTPUT_DIR, filename)

        # Читаем HTML-файл
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()

        text = extract_text(html)
        lemmas = tokenize_and_lemmatize(text)

        # Заполняем инвертированный индекс
        for lemma in lemmas:
            inverted_index.setdefault(lemma, set()).add(doc_id)

    return inverted_index, all_docs


def save_index(inverted_index, all_docs):
    """
    Сохраняет индекс и список документов в JSON-файл.
    inverted_index — словарь {лемма -> set(doc_id)}
    all_docs — множество документов
    """
    data = {
        # set преобразуем в list для JSON
        "index": {k: list(v) for k, v in inverted_index.items()},
        "all_docs": list(all_docs)
    }

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_index():
    """
    Загружает инвертированный индекс из файла.
    Возвращает inverted_index и all_docs.
    """
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # list обратно преобразуем в set
    inverted_index = {k: set(v) for k, v in data["index"].items()}
    all_docs = set(data["all_docs"])

    return inverted_index, all_docs


# Поддерживаемые булевы операторы
OPERATORS = {"AND", "OR", "NOT"}

# Приоритет операторов
PRIORITY = {
    "NOT": 3,
    "AND": 2,
    "OR": 1
}


def normalize_query(query):
    """
    Разбивает строку запроса на токены.
    query — строка пользовательского запроса.
    """
    query = query.replace("(", " ( ").replace(")", " ) ")
    return query.split()


def to_rpn(tokens):
    """
    Преобразует список токенов запроса
    в обратную польскую нотацию (RPN).
    tokens — список токенов запроса.
    """
    output = []
    stack = []

    for token in tokens:
        t = token.upper()

        if t in OPERATORS:
            # Обработка операторов с учётом приоритета
            while stack and stack[-1] in OPERATORS and PRIORITY[stack[-1]] >= PRIORITY[t]:
                output.append(stack.pop())
            stack.append(t)

        elif token == "(":
            stack.append(token)

        elif token == ")":
            # Выгружаем операторы до открывающей скобки
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            stack.pop()

        else:
            # Термин
            output.append(token)

    # Выгружаем оставшиеся операторы
    while stack:
        output.append(stack.pop())

    return output


def term_to_docs(term):
    """
    Преобразует термин запроса в множество документов.
    term — слово из запроса.
    """
    term = term.lower()
    p = morph.parse(term)[0]
    lemma = p.normal_form

    return inverted_index.get(lemma, set())


def eval_rpn(rpn):
    """
    Вычисляет булев запрос в RPN-форме.
    rpn — список токенов в обратной польской нотации.
    """
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
            # Термин
            stack.append(term_to_docs(token))

    return stack.pop() if stack else set()


# Если файла индекса нет — строим его
if not os.path.exists(INDEX_FILE):
    print("Файл индекса не найден. Строим индекс...")

    inverted_index, all_docs = build_index()
    save_index(inverted_index, all_docs)

    print("Индекс построен и сохранён.")

# Иначе загружаем готовый индекс
else:
    print("Загружаем индекс из файла...")
    inverted_index, all_docs = load_index()
    print("Индекс загружен.")


# Основной цикл ввода запросов
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