import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


MIN_WORDS = 30
SIMILARITY_THRESHOLD = 0.88
MIN_SHARED_WORDS = 5


def _normalize_words(text: str) -> set:
    """
    Convert review text into a set of meaningful words.
    """
    words = re.findall(
        r"\b[a-zA-Z][a-zA-Z']{2,}\b",
        text.lower()
    )

    return set(words)


def detect_semantic_duplicates(
    reviews: list,
    similarity_threshold: float = SIMILARITY_THRESHOLD
) -> dict:
    """
    Detect highly similar review text using word-level TF-IDF.

    Short reviews are ignored because very short text can produce
    misleading similarity scores from common product-related words.
    """

    # Only analyze sufficiently long reviews.
    valid_reviews = [
        r
        for r in reviews
        if r.get("review_text")
        and len(
            r.get("review_text", "").split()
        ) >= MIN_WORDS
    ]

    if len(valid_reviews) < 2:
        return {
            "semantic_duplicate_count": 0,
            "semantic_cluster_ratio": 0.0,
            "flagged_clusters": [],
            "flagged_reasons": []
        }

    texts = [
        r["review_text"].strip()
        for r in valid_reviews
    ]

    # Word-based TF-IDF is more suitable than character-level
    # similarity for detecting genuinely similar review wording.
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        analyzer="word",
        stop_words="english",
        min_df=1,
        sublinear_tf=True
    )

    tfidf_matrix = vectorizer.fit_transform(texts)

    cosine_scores = cosine_similarity(
        tfidf_matrix,
        tfidf_matrix
    )

    flagged_indices = set()
    clusters = []

    normalized_word_sets = [
        _normalize_words(text)
        for text in texts
    ]

    n = len(texts)

    for i in range(n):
        for j in range(i + 1, n):

            similarity = float(
                cosine_scores[i][j]
            )

            # Only continue when the overall word-level
            # similarity is high.
            if similarity < similarity_threshold:
                continue

            shared_words = (
                normalized_word_sets[i]
                & normalized_word_sets[j]
            )

            # A high similarity score alone can still happen
            # because of common product words. Require a
            # reasonable number of shared meaningful words.
            if len(shared_words) < MIN_SHARED_WORDS:
                continue

            # Do not treat exact copies as semantic paraphrases.
            if (
                texts[i].lower().strip()
                == texts[j].lower().strip()
            ):
                continue

            flagged_indices.add(i)
            flagged_indices.add(j)

            clusters.append({
                "review_1": texts[i],
                "review_2": texts[j],
                "similarity": round(
                    similarity,
                    3
                ),
                "shared_words": sorted(
                    list(shared_words)
                )[:20]
            })

    flagged_count = len(flagged_indices)

    ratio = (
        flagged_count / len(valid_reviews)
        if valid_reviews
        else 0.0
    )

    flagged_reasons = []

    if flagged_count > 0:
        flagged_reasons.append(
            f"Detected {flagged_count} highly similar "
            f"reviews with >= "
            f"{int(similarity_threshold * 100)}% "
            f"word-level similarity."
        )

    return {
        "semantic_duplicate_count": flagged_count,
        "semantic_cluster_ratio": round(
            ratio,
            2
        ),
        "flagged_clusters": clusters[:5],
        "flagged_reasons": flagged_reasons
    }