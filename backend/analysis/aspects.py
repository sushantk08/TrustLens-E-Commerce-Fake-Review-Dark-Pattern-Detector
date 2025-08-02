import spacy
from nltk.sentiment.vader import SentimentIntensityAnalyzer

_nlp = None
_vader = None


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def get_vader():
    global _vader
    if _vader is None:
        _vader = SentimentIntensityAnalyzer()
    return _vader


# Canonical product aspects and their keyword triggers
ASPECT_CATEGORIES = {
    'Battery': ['battery', 'charge', 'charging', 'backup', 'mah', 'power'],
    'Display': ['screen', 'display', 'panel', 'amoled', 'brightness', 'refresh rate'],
    'Camera': ['camera', 'photo', 'photos', 'picture', 'video', 'lens', 'sensor'],
    'Performance': ['speed', 'lag', 'processor', 'gaming', 'fast', 'slow', 'heating', 'heat'],
    'Build Quality': ['build', 'plastic', 'metal', 'durability', 'hinge', 'design', 'weight'],
    'Sound': ['sound', 'audio', 'speaker', 'bass', 'treble', 'mic', 'volume'],
    'Delivery': ['delivery', 'packaging', 'box', 'courier', 'shipping', 'package'],
}


def extract_aspect_sentiments(reviews: list) -> dict:
    """
    Extracts sentences matching key product aspects, analyzes their polarity,
    and computes a 1.0 to 5.0 rating for each aspect.
    """
    if not reviews:
        return {'aspects': {}, 'flagged_reasons': []}

    nlp = get_nlp()
    vader = get_vader()

    aspect_scores = {category: [] for category in ASPECT_CATEGORIES}

    for r in reviews:
        text = r.get('review_text', '')
        if not text or len(text.strip()) < 10:
            continue

        doc = nlp(text)

        # Evaluate each sentence individually to localize sentiment
        for sent in doc.sents:
            sent_text = sent.text.lower()
            sent_polarity = vader.polarity_scores(sent.text)['compound']

            # Match sentence against canonical aspects
            for category, keywords in ASPECT_CATEGORIES.items():
                if any(kw in sent_text for kw in keywords):
                    # Map VADER compound (-1.0 to +1.0) to a 1.0 to 5.0 star scale
                    star_equiv = 1.0 + ((sent_polarity + 1.0) / 2.0) * 4.0
                    aspect_scores[category].append(round(star_equiv, 2))

    summary = {}
    flagged_reasons = []

    for category, scores in aspect_scores.items():
        if len(scores) >= 2:  # Only report aspects with multiple mentions
            avg_rating = round(sum(scores) / len(scores), 1)
            positive_count = sum(1 for s in scores if s >= 3.5)
            negative_count = sum(1 for s in scores if s < 2.5)

            summary[category] = {
                'score': avg_rating,
                'mentions': len(scores),
                'positive_mentions': positive_count,
                'negative_mentions': negative_count
            }

            # Flag hidden defects where an aspect scores significantly low
            if avg_rating <= 2.2 and len(scores) >= 3:
                flagged_reasons.append(
                    f"Hidden flaw detected: '{category}' has poor customer sentiment ({avg_rating}/5.0 across {len(scores)} mentions)."
                )

    return {
        'aspects': summary,
        'flagged_reasons': flagged_reasons
    }