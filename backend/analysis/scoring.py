from .velocity import analyze_review_velocity
from .credibility import analyze_reviewer_credibility
from .dark_patterns import analyze_dark_patterns
from .semantic import detect_semantic_duplicates
from .aspects import extract_aspect_sentiments


def compute_true_trust_score(
    reviews: list,
    price_history: list = None,
    current_price: float = None,
    original_price: float = None,
    category: str = 'ecommerce'
) -> dict:
    """
    Combines review velocity, credibility heuristics, dark patterns,
    semantic duplicate detection, and category-specific aspect sentiments
    into a consolidated True Trust Score (0-100).
    """
    # 0. Handle zero or empty reviews
    if not reviews or len(reviews) == 0:
        return {
            'trust_score': 0.0,
            'fake_review_percentage': 0.0,
            'velocity_spike_detected': False,
            'dark_patterns_detected': [],
            'aspects_sentiment': {},
            'summary_reasons': ['Insufficient review data to compute a reliable Trust Score.'],
            'components': {}
        }

    # 1. Run component analyses with category awareness
    velocity_res = analyze_review_velocity(reviews)
    credibility_res = analyze_reviewer_credibility(reviews)
    dark_patterns_res = analyze_dark_patterns(price_history or [], current_price, original_price)
    semantic_res = detect_semantic_duplicates(reviews)
    aspects_res = extract_aspect_sentiments(reviews, category=category)

    # 2. Base score starts at 100
    score = 100.0
    all_reasons = []

    # Penalty A: Review Velocity & Rating Distribution (Up to 25 points)
    if velocity_res.get('velocity_spike_detected'):
        score -= 15.0
    if velocity_res.get('bimodal_distribution'):
        score -= 10.0
    all_reasons.extend(velocity_res.get('flagged_reasons', []))

    # Penalty B: Reviewer Credibility & Single-Review Bot Rings (Up to 25 points)
    cred_score = credibility_res.get('credibility_score', 100.0)
    score -= (100.0 - cred_score) * 0.25
    all_reasons.extend(credibility_res.get('flagged_reasons', []))

    # Penalty C: Semantic Duplicates / Spun AI Reviews (Up to 25 points)
    spun_ratio = semantic_res.get('semantic_cluster_ratio', 0.0)
    score -= min(25.0, spun_ratio * 50.0)
    all_reasons.extend(semantic_res.get('flagged_reasons', []))

    # Penalty D: Dark Patterns (Artificial Pricing / Fake Urgency) (Up to 15 points)
    if dark_patterns_res.get('price_manipulation_detected'):
        score -= 10.0
    if dark_patterns_res.get('fake_scarcity_detected'):
        score -= 5.0
    all_reasons.extend(dark_patterns_res.get('flagged_reasons', []))

    # Penalty E: Aspect Deficits (Hidden Flaws) (Up to 10 points)
    if aspects_res.get('flagged_reasons'):
        score -= min(10.0, len(aspects_res['flagged_reasons']) * 5.0)
        all_reasons.extend(aspects_res['flagged_reasons'])

    # Final bounded score between 5.0 and 100.0
    final_score = max(5.0, min(100.0, round(score, 1)))

    # Calculate estimated percentage of suspicious/manipulated reviews
    total_revs = max(1, len(reviews))
    flagged_reviews_count = (
        credibility_res.get('exact_duplicates_count', 0) +
        semantic_res.get('semantic_duplicate_count', 0)
    )
    fake_review_pct = round(min(100.0, (flagged_reviews_count / total_revs) * 100.0), 1)

    return {
        'trust_score': final_score,
        'fake_review_percentage': fake_review_pct,
        'velocity_spike_detected': velocity_res.get('velocity_spike_detected', False),
        'dark_patterns_detected': dark_patterns_res.get('dark_patterns', []),
        'aspects_sentiment': aspects_res.get('aspects', {}),
        'summary_reasons': all_reasons,
        'components': {
            'velocity': velocity_res,
            'credibility': credibility_res,
            'semantic': semantic_res,
            'dark_patterns': dark_patterns_res,
            'aspects': aspects_res,
        }
    }