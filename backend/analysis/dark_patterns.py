import pandas as pd
import numpy as np


def analyze_dark_patterns(price_history: list, current_price: float = None, original_price: float = None) -> dict:
    """
    Analyzes historical price data and stock availability alerts
    to detect deceptive pricing and artificial scarcity tricks.
    """
    dark_patterns = []
    flagged_reasons = []

    price_manipulation_detected = False
    fake_scarcity_detected = False

    # 1. Base Discount Sanity Check
    if current_price and original_price and original_price > current_price:
        claimed_discount = ((original_price - current_price) / original_price) * 100
        if claimed_discount >= 70.0:
            dark_patterns.append({
                'type': 'EXAGGERATED_DISCOUNT',
                'severity': 'MEDIUM',
                'description': f"Unusually high claimed discount of {round(claimed_discount)}% against inflated MSRP."
            })
            flagged_reasons.append(f"Exaggerated MRP discount claimed ({round(claimed_discount)}%).")

    # If insufficient historical data, return baseline inspection
    if not price_history or len(price_history) < 3:
        return {
            'price_manipulation_detected': price_manipulation_detected,
            'fake_scarcity_detected': fake_scarcity_detected,
            'dark_patterns': dark_patterns,
            'price_volatility': 0.0,
            'lowest_price': current_price or 0.0,
            'highest_price': original_price or current_price or 0.0,
            'average_price': current_price or 0.0,
            'flagged_reasons': flagged_reasons
        }

    df = pd.DataFrame(price_history)
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.dropna(subset=['price']).sort_values(by='recorded_at')

    if df.empty:
        return {
            'price_manipulation_detected': False,
            'fake_scarcity_detected': False,
            'dark_patterns': dark_patterns,
            'price_volatility': 0.0,
            'lowest_price': current_price or 0.0,
            'highest_price': original_price or current_price or 0.0,
            'average_price': current_price or 0.0,
            'flagged_reasons': flagged_reasons
        }

    lowest_price = float(df['price'].min())
    highest_price = float(df['price'].max())
    avg_price = float(df['price'].mean())
    price_volatility = float(df['price'].std() / avg_price) if avg_price > 0 else 0.0

    # 2. Artificial Pre-Sale Price Hike Detection
    # If the price was hiked by > 15% recently right before dropping back down
    if len(df) >= 3:
        recent_prices = df['price'].values
        max_recent = np.max(recent_prices[:-1])
        latest = recent_prices[-1]

        if max_recent > (avg_price * 1.20) and latest <= avg_price:
            price_manipulation_detected = True
            dark_patterns.append({
                'type': 'ARTIFICIAL_PRICE_HIKE',
                'severity': 'HIGH',
                'description': "Price was temporarily inflated prior to current discount to simulate a larger price drop."
            })
            flagged_reasons.append("Temporary price hike detected immediately preceding current sale price.")

    # 3. Persistent Fake Scarcity Detection
    if 'stock_status' in df.columns:
        scarcity_keywords = ['only 1 left', 'only 2 left', 'only 3 left', 'hurry', 'almost gone']
        scarcity_records = df['stock_status'].dropna().str.lower().apply(
            lambda s: any(k in s for k in scarcity_keywords)
        )

        # If scarcity warnings persist across multiple separate checks
        if scarcity_records.sum() >= 3:
            fake_scarcity_detected = True
            dark_patterns.append({
                'type': 'FAKE_SCARCITY_URGENCY',
                'severity': 'MEDIUM',
                'description': "Item has continuously displayed 'low stock' warnings over time without selling out."
            })
            flagged_reasons.append("Perpetual scarcity alert detected to pressure immediate purchase.")

    return {
        'price_manipulation_detected': price_manipulation_detected,
        'fake_scarcity_detected': fake_scarcity_detected,
        'dark_patterns': dark_patterns,
        'price_volatility': round(price_volatility, 3),
        'lowest_price': round(lowest_price, 2),
        'highest_price': round(highest_price, 2),
        'average_price': round(avg_price, 2),
        'flagged_reasons': flagged_reasons
    }