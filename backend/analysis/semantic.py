import numpy as np
from sentence_transformers import SentenceTransformer, util

# Lightweight, fast 80MB embedding model suitable for real-time inference
_model = None


def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def detect_semantic_duplicates(reviews: list, similarity_threshold: float = 0.60) -> dict:    
    """
    Detects paraphrased or AI-spun review pairs using dense vector embeddings.
    Flags groups of non-identical reviews that convey nearly identical semantic meaning.
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
    model = get_embedding_model()

    # Generate vector embeddings
    embeddings = model.encode(texts, convert_to_tensor=True, show_progress_bar=False)

    # Compute pairwise cosine similarity matrix
    cosine_scores = util.cos_sim(embeddings, embeddings).cpu().numpy()

    n = len(texts)
    flagged_indices = set()
    clusters = []

    for i in range(n):
        for j in range(i + 1, n):
            # Check if similarity meets threshold and the strings are not verbatim duplicates
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
            f"Detected {flagged_count} paraphrased or AI-spun reviews exhibiting >= {int(similarity_threshold * 100)}% semantic similarity."
        )

    return {
        'semantic_duplicate_count': flagged_count,
        'semantic_cluster_ratio': round(ratio, 2),
        'flagged_clusters': clusters[:5],  # Keep top 5 samples for inspection
        'flagged_reasons': flagged_reasons
    }