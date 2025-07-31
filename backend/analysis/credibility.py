import re
from collections import Counter


def analyze_reviewer_credibility(reviews: list) -> dict:
    """
    Analyzes reviewer name patterns, verified purchase status, exact text duplicates,
    and review length anomalies.
    """
    if not reviews or len(reviews) < 5:
        return {
            'credibility_score': 100.0,
            'exact_duplicates_count': 0,
            'generic_reviewer_ratio': 0.0,
            'unverified_ratio': 0.0,
            'short_review_ratio': 0.0,
            'flagged_reasons': []
        }

    total_reviews = len(reviews)
    flagged_reasons = []
    penalties = 0.0

    # 1. Exact Duplicate Text Detection
    texts = [r.get('review_text', '').strip().lower() for r in reviews if r.get('review_text')]
    text_counts = Counter(texts)
    duplicate_groups = {text: count for text, count in text_counts.items() if count > 1 and len(text) > 10}
    total_duplicate_instances = sum(duplicate_groups.values())

    if total_duplicate_instances > 0:
        penalty = min(35.0, total_duplicate_instances * 7.0)
        penalties += penalty
        flagged_reasons.append(
            f"Found {len(duplicate_groups)} recurring exact-duplicate review text groups ({total_duplicate_instances} instances)."
        )

    # 2. Generic Reviewer Names
    generic_patterns = ['amazon customer', 'flipkart customer', 'anonymous', 'user', 'customer']
    names = [r.get('reviewer_name', '').strip().lower() for r in reviews]
    generic_count = sum(1 for name in names if any(p in name for p in generic_patterns) or len(name) < 2)
    generic_ratio = generic_count / total_reviews

    if generic_ratio >= 0.35:
        penalties += 15.0
        flagged_reasons.append(
            f"High volume of generic/anonymous reviewer profiles ({round(generic_ratio * 100)}%)."
        )

    # 3. Unverified Purchase Ratio
    unverified_count = sum(1 for r in reviews if not r.get('is_verified_purchase', False))
    unverified_ratio = unverified_count / total_reviews

    if unverified_ratio >= 0.40:
        penalties += 20.0
        flagged_reasons.append(
            f"High ratio of unverified purchase reviews ({round(unverified_ratio * 100)}%)."
        )

    # 4. Abnormally Brief Reviews (< 4 words) on 5-Star Ratings
    short_positive_count = 0
    for r in reviews:
        words = re.findall(r'\w+', r.get('review_text', ''))
        if r.get('rating', 0) >= 4.0 and len(words) <= 3:
            short_positive_count += 1

    short_ratio = short_positive_count / total_reviews
    if short_ratio >= 0.30:
        penalties += 15.0
        flagged_reasons.append(
            f"Suspicious cluster of generic ultra-short 5-star reviews ({round(short_ratio * 100)}%)."
        )

    credibility_score = max(0.0, 100.0 - penalties)

    return {
        'credibility_score': round(credibility_score, 1),
        'exact_duplicates_count': total_duplicate_instances,
        'generic_reviewer_ratio': round(generic_ratio, 2),
        'unverified_ratio': round(unverified_ratio, 2),
        'short_review_ratio': round(short_ratio, 2),
        'flagged_reasons': flagged_reasons
    }