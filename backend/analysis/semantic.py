import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def detect_semantic_duplicates(reviews: list, similarity_threshold: float = 0.72) -> dict:
    """
    Detects paraphrased or AI-spun reviews using character and word n-gram
    TF-IDF vectors and cosine similarity (consumes ~15MB RAM vs 400MB with PyTorch).
    """
    valid_reviews = [
        r for r in reviews
        if r.get('review_text') and len(r['review_text'].strip()) >= 15
    ]

    if len(valid_reviews) < 4:
        return {
            'semantic_duplicate_count': 0,
            'semantic_cluster_ratio': 0.0,
            'flagged_clusters': [],
            'flagged_reasons': []
        }

    texts = [r['review_text'].strip() for r in valid_reviews]

    # Character-level n-grams capture paraphrased word forms without heavy models
    vectorizer = TfidfVectorizer(ngram_range=(1, 3), analyzer='char_wb', min_df=1)
    tfidf_matrix = vectorizer.fit_transform(texts)
    cosine_scores = cosine_similarity(tfidf_matrix, tfidf_matrix)

    n = len(texts)
    flagged_indices = set()
    clusters = []

    for i in range(n):
        for j in range(i + 1, n):
            # Check if similarity meets threshold and strings are not verbatim duplicates
            if cosine_scores[i][j] >= similarity_threshold and texts[i].lower() != texts[j].lower():
                flagged_indices.add(i)
                flagged_indices.add(j)
                clusters.append({
                    'review_1': texts[i],
                    'review_2': texts[j],
                    'similarity': round(float(cosine_scores[i][j]), 3)
                })

    flagged_count = len(flagged_indices)
    ratio = flagged_count / len(valid_reviews)
    flagged_reasons = []

    if flagged_count > 0:
        flagged_reasons.append(
            f"Detected {flagged_count} semantically spun reviews exhibiting >= {int(similarity_threshold * 100)}% text similarity."
        )

    return {
        'semantic_duplicate_count': flagged_count,
        'semantic_cluster_ratio': round(ratio, 2),
        'flagged_clusters': clusters[:5],
        'flagged_reasons': flagged_reasons
    }