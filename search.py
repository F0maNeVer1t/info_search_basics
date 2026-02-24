import os
import json
import pymorphy3

LEMMAS_DIR = "lemmas"
INDEX_FILE = "inverted_index.json"

morph = pymorphy3.MorphAnalyzer()

OPERATORS = {"AND", "OR", "NOT"}

PRIORITY = {
    "NOT": 3,
    "AND": 2,
    "OR": 1
}


def build_index_from_lemmas():
    """
    Строит инвертированный индекс по файлам *_lemmas.txt
    Формат строки:
    <lemma> <token1> <token2> ...

    Возвращает:
    inverted_index — словарь {лемма -> множество документов}
    all_docs — множество всех документов
    """

    inverted_index = {}
    all_docs = set()

    for filename in os.listdir(LEMMAS_DIR):

        if not filename.endswith("_lemmas.txt"):
            continue

        doc_id = filename
        all_docs.add(doc_id)

        path = os.path.join(LEMMAS_DIR, filename)

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()

                if not parts:
                    continue

                lemma = parts[0]

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


def normalize_query(query):
    query = query.replace("(", " ( ").replace(")", " ) ")
    return query.split()


def to_rpn(tokens):
    """
    Преобразует список токенов запроса в обратную польскую нотацию (RPN).
    RPN - форма записи выражений без скобок, в которой порядок вычислений задаётся положением операторов.
    tokens — список терминов, операторов и скобок.
    """

    output = []
    stack = []

    for token in tokens:

        t = token.upper()

        # обработка логических операторов
        if t in OPERATORS:
            while stack and stack[-1] in OPERATORS and PRIORITY[stack[-1]] >= PRIORITY[t]:
                output.append(stack.pop())
            stack.append(t)

        # открывающая скобка
        elif token == "(":
            stack.append(token)

        # закрывающая скобка
        elif token == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            stack.pop()

        # термин запроса
        else:
            output.append(token)

    # перенос оставшихся операторов
    while stack:
        output.append(stack.pop())

    return output


def term_to_docs(term):
    """
    Приводит термин запроса к лемме
    и возвращает множество документов,
    в которых эта лемма встречается.

    term - слово из запроса
    """

    term = term.lower()
    p = morph.parse(term)[0]
    lemma = p.normal_form

    return inverted_index.get(lemma, set())


def eval_rpn(rpn):
    """
    Вычисление булевого выражения в RPN
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
            stack.append(term_to_docs(token))

    return stack.pop() if stack else set()


# запуск
if not os.path.exists(INDEX_FILE):
    print("Файл индекса не найден. Строим индекс по lemmas/...")

    inverted_index, all_docs = build_index_from_lemmas()
    save_index(inverted_index, all_docs)

    print("Индекс построен и сохранён.")

else:
    print("Загружаем индекс...")
    inverted_index, all_docs = load_index()
    print("Индекс загружен.")


while True:

    query = input("\nВведите запрос (для выхода нажмите enter дважды): ")

    if not query.strip():
        break

    tokens = normalize_query(query)
    rpn = to_rpn(tokens)

    result = eval_rpn(rpn)

    print("Найдено документов:", len(result))

    for doc in sorted(result):
        print(" ", doc)