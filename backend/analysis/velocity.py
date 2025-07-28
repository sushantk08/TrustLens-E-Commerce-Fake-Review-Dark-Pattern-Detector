import pandas as pd
import numpy as np


def analyze_review_velocity(reviews: list) -> dict:
    """
    Analyzes review time-series patterns and rating distributions
    to flag inorganic surges and bimodal ratings.
    """
    if not reviews or len(reviews) < 5:
        return {
            'velocity_spike_detected': False,
            'bimodal_distribution': False,
            'max_reviews_single_day': len(reviews) if reviews else 0,
            'spike_dates': [],
            'rating_distribution': {},
            'unverified_ratio': 0.0,
            'flagged_reasons': []
        }

    df = pd.DataFrame(reviews)

    flagged_reasons = []

    # 1. Rating Distribution & Bimodal Detection
    rating_counts = df['rating'].value_counts().to_dict()
    total_reviews = len(df)
    five_star_ratio = rating_counts.get(5.0, 0) / total_reviews
    one_star_ratio = rating_counts.get(1.0, 0) / total_reviews

    # Flag bimodal (polarized 5-star and 1-star reviews common in fake review campaigns)
    bimodal = (five_star_ratio >= 0.40) and (one_star_ratio >= 0.25)
    if bimodal:
        flagged_reasons.append(
            f"Polarized rating distribution: {round(five_star_ratio * 100)}% 5-star vs {round(one_star_ratio * 100)}% 1-star reviews."
        )

    # 2. Unverified Purchase Ratio
    unverified_ratio = 0.0
    if 'is_verified_purchase' in df.columns:
        unverified_count = (~df['is_verified_purchase']).sum()
        unverified_ratio = float(unverified_count / total_reviews)
        if unverified_ratio > 0.40:
            flagged_reasons.append(
                f"High proportion of unverified reviews ({round(unverified_ratio * 100)}%)."
            )

    # 3. Velocity Spike Detection across Dates
    velocity_spike_detected = False
    spike_dates = []
    max_single_day = 0

    if 'review_date' in df.columns and df['review_date'].notna().any():
        valid_dates = df[df['review_date'].notna()].copy()
        valid_dates['review_date'] = pd.to_datetime(valid_dates['review_date'])

        # Group review counts by date
        daily_counts = valid_dates.groupby('review_date').size()

        if not daily_counts.empty:
            max_single_day = int(daily_counts.max())
            mean_daily = daily_counts.mean()
            std_daily = daily_counts.std() if len(daily_counts) > 1 else 0.0

            # Threshold: single day count exceeds mean + 2.5 standard deviations (and at least 5 reviews)
            threshold = max(5, mean_daily + (2.5 * std_daily))
            spikes = daily_counts[daily_counts >= threshold]

            if not spikes.empty:
                velocity_spike_detected = True
                spike_dates = [d.strftime('%Y-%m-%d') for d in spikes.index]
                flagged_reasons.append(
                    f"Suspicious review velocity: surge of {max_single_day} reviews detected on {', '.join(spike_dates[:3])}."
                )

    return {
        'velocity_spike_detected': velocity_spike_detected,
        'bimodal_distribution': bimodal,
        'max_reviews_single_day': max_single_day,
        'spike_dates': spike_dates,
        'rating_distribution': rating_counts,
        'unverified_ratio': round(unverified_ratio, 2),
        'flagged_reasons': flagged_reasons
    }