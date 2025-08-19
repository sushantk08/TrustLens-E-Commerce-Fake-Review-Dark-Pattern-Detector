import re
from collections import Counter


def analyze_reviewer_credibility(reviews: list) -> dict:
    if not reviews or len(reviews) < 5:
        return {
            'credibility_score': 100.0,
            'exact_duplicates_count': 0,
            'generic_reviewer_ratio': 0.0,
            'unverified_ratio': 0.0,
            'short_review_ratio': 0.0,
            'single_review_account_ratio': 0.0,
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
            f"Found {len(duplicate_groups)} recurring verbatim review text groups ({total_duplicate_instances} instances)."
        )

    # 2. Google Maps: Single-Review Account Rings (Accounts that only ever posted 1 review)
    single_review_accounts = [r for r in reviews if r.get('reviewer_total_reviews', 1) <= 1 and r.get('rating', 5.0) >= 4.0]
    single_review_ratio = len(single_review_accounts) / total_reviews

    if single_review_ratio >= 0.40:
        penalties += 20.0
        flagged_reasons.append(
            f"High volume of single-review Google accounts ({round(single_review_ratio * 100)}% of positive reviews), typical of purchased rating campaigns."
        )

    # 3. Google Maps: Local Guide Presence Check
    has_local_guide_data = any('is_local_guide' in r for r in reviews)
    if has_local_guide_data and total_reviews >= 10:
        local_guides_count = sum(1 for r in reviews if r.get('is_local_guide', False))
        if local_guides_count == 0:
            penalties += 10.0
            flagged_reasons.append(
                "Suspiciously zero reviews from verified Google Local Guides despite high volume."
            )

    # 4. Unverified / Generic Reviewer Profiles
    generic_patterns = ['amazon customer', 'flipkart customer', 'anonymous', 'google user', 'user']
    names = [r.get('reviewer_name', '').strip().lower() for r in reviews]
    generic_count = sum(1 for name in names if any(p in name for p in generic_patterns) or len(name) < 2)
    generic_ratio = generic_count / total_reviews

    if generic_ratio >= 0.35:
        penalties += 15.0
        flagged_reasons.append(
            f"High ratio of generic or anonymous reviewer profiles ({round(generic_ratio * 100)}%)."
        )

    # 5. Generic Ultra-Short 5-Star Reviews
    short_positive_count = sum(
        1 for r in reviews
        if r.get('rating', 0) >= 4.0 and len(re.findall(r'\w+', r.get('review_text', ''))) <= 3
    )
    short_ratio = short_positive_count / total_reviews
    if short_ratio >= 0.30:
        penalties += 15.0
        flagged_reasons.append(
            f"Suspicious cluster of generic ultra-short reviews with no details ({round(short_ratio * 100)}%)."
        )

    credibility_score = max(0.0, 100.0 - penalties)

    return {
        'credibility_score': round(credibility_score, 1),
        'exact_duplicates_count': total_duplicate_instances,
        'generic_reviewer_ratio': round(generic_ratio, 2),
        'unverified_ratio': round(generic_ratio, 2),
        'short_review_ratio': round(short_ratio, 2),
        'single_review_account_ratio': round(single_review_ratio, 2),
        'flagged_reasons': flagged_reasons
    }