import os
import math
import pymorphy3

TFIDF_DIR = "tfidf_lemmas"

morph = pymorphy3.MorphAnalyzer()


def load_document_vectors():
    """
    Загружает tf-idf векторы документов.

    Возвращает:
        dict[str, dict[str, float]]
        doc_id -> { term -> tfidf }
    """

    vectors = {}

    for filename in os.listdir(TFIDF_DIR):

        if not filename.endswith("_lemmas_tfidf.txt"):
            continue

        doc_id = filename
        path = os.path.join(TFIDF_DIR, filename)

        vec = {}

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()

                if len(parts) != 3:
                    continue

                term = parts[0]
                tfidf = float(parts[2])

                vec[term] = tfidf

        vectors[doc_id] = vec

    return vectors


def load_idf_table():
    """
    Из векторов документов извлекает idf каждого термина.

    Используется для построения вектора запроса.

    Возвращает:
        dict[str, float]
        term -> idf
    """

    idf = {}

    for filename in os.listdir(TFIDF_DIR):

        if not filename.endswith("_lemmas_tfidf.txt"):
            continue

        path = os.path.join(TFIDF_DIR, filename)

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 3:
                    continue

                term = parts[0]
                term_idf = float(parts[1])

                idf[term] = term_idf

    return idf


def normalize_term(word: str) -> str:
    """
    Приводит слово запроса к нормальной форме (лемме).
    """

    word = word.lower()
    return morph.parse(word)[0].normal_form


def build_query_vector(query, idf_table):
    """
    Строит tf-idf вектор запроса.

    tf считается внутри запроса.
    idf берётся из коллекции документов.
    """

    words = []
    for w in query.split():
        w = normalize_term(w)
        words.append(w)

    tf = {}
    for w in words:
        tf[w] = tf.get(w, 0) + 1

    total = len(words)

    vec = {}

    for term, cnt in tf.items():

        if term not in idf_table:
            continue

        tf_norm = cnt / total
        vec[term] = tf_norm * idf_table[term]

    return vec


def vector_norm(vec):
    """
    Евклидова норма вектора.
    """

    return math.sqrt(sum(v * v for v in vec.values()))


def cosine_similarity(v1, v2):
    """
    Косинусное сходство двух разреженных векторов.
    """

    if not v1 or not v2:
        return 0.0

    s = 0.0

    # итерируемся по меньшему вектору
    if len(v1) > len(v2):
        v1, v2 = v2, v1

    for term, w in v1.items():
        if term in v2:
            s += w * v2[term]

    n1 = vector_norm(v1)
    n2 = vector_norm(v2)

    if n1 == 0 or n2 == 0:
        return 0.0

    return s / (n1 * n2)


def search(query, document_vectors, idf_table, top_k=10):
    """
    Выполняет векторный поиск.
    """

    query_vec = build_query_vector(query, idf_table)

    scores = []

    for doc_id, doc_vec in document_vectors.items():
        score = cosine_similarity(query_vec, doc_vec)
        if score > 0:
            scores.append((doc_id, score))

    scores.sort(key=lambda x: x[1], reverse=True)

    return scores[:top_k]


if __name__ == "__main__":

    print("Загрузка векторов документов...")
    document_vectors = load_document_vectors()
    idf_table = load_idf_table()

    print("Документов:", len(document_vectors))

    while True:

        query = input("\nВведите поисковый запрос: ").strip()

        if not query:
            break

        results = search(query, document_vectors, idf_table)

        if not results:
            print("Ничего не найдено.")
            continue

        for doc, score in results:
            print(f"{doc} -> {score:.6f}")