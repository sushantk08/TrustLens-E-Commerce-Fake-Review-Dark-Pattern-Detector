from .velocity import analyze_review_velocity
from .credibility import analyze_reviewer_credibility
from .dark_patterns import analyze_dark_patterns
from .semantic import detect_semantic_duplicates
from .aspects import extract_aspect_sentiments


def compute_true_trust_score(reviews: list, price_history: list = None, current_price: float = None, original_price: float = None) -> dict:
    """
    Combines velocity analysis, semantic duplicate clustering, reviewer heuristics,
    dark patterns, and aspect sentiments into a consolidated True Trust Score (0-100).
    """
    # 1. Run component analyses
    velocity_res = analyze_review_velocity(reviews)
    credibility_res = analyze_reviewer_credibility(reviews)
    dark_patterns_res = analyze_dark_patterns(price_history or [], current_price, original_price)
    semantic_res = detect_semantic_duplicates(reviews)
    aspects_res = extract_aspect_sentiments(reviews)

    # 2. Base score starts at 100
    score = 100.0
    all_reasons = []

    # Penalty A: Review Velocity & Rating Distribution (Up to 25 points)
    if velocity_res['velocity_spike_detected']:
        score -= 15.0
    if velocity_res['bimodal_distribution']:
        score -= 10.0
    all_reasons.extend(velocity_res['flagged_reasons'])

    # Penalty B: Reviewer Credibility & Exact Duplicates (Up to 25 points)
    cred_score = credibility_res['credibility_score']
    cred_penalty = (100.0 - cred_score) * 0.25
    score -= cred_penalty
    all_reasons.extend(credibility_res['flagged_reasons'])

    # Penalty C: Semantic Duplicates / Spun Bot Reviews (Up to 25 points)
    spun_ratio = semantic_res['semantic_cluster_ratio']
    score -= min(25.0, spun_ratio * 50.0)
    all_reasons.extend(semantic_res['flagged_reasons'])

    # Penalty D: Dark Patterns & Artificial Pricing (Up to 15 points)
    if dark_patterns_res['price_manipulation_detected']:
        score -= 10.0
    if dark_patterns_res['fake_scarcity_detected']:
        score -= 5.0
    all_reasons.extend(dark_patterns_res['flagged_reasons'])

    # Penalty E: Hidden Product Flaw (Up to 10 points)
    if aspects_res['flagged_reasons']:
        score -= min(10.0, len(aspects_res['flagged_reasons']) * 5.0)
        all_reasons.extend(aspects_res['flagged_reasons'])

    # Final bounded score
    final_score = max(5.0, min(100.0, round(score, 1)))

    # Calculate estimated percentage of suspicious/manipulated reviews
    total_revs = max(1, len(reviews))
    flagged_reviews_count = (
        credibility_res['exact_duplicates_count'] +
        semantic_res['semantic_duplicate_count']
    )
    fake_review_pct = round(min(100.0, (flagged_reviews_count / total_revs) * 100.0), 1)

    return {
        'trust_score': final_score,
        'fake_review_percentage': fake_review_pct,
        'velocity_spike_detected': velocity_res['velocity_spike_detected'],
        'dark_patterns_detected': dark_patterns_res['dark_patterns'],
        'aspects_sentiment': aspects_res['aspects'],
        'summary_reasons': all_reasons,
        'components': {
            'velocity': velocity_res,
            'credibility': credibility_res,
            'semantic': semantic_res,
            'dark_patterns': dark_patterns_res,
            'aspects': aspects_res,
        }
    }