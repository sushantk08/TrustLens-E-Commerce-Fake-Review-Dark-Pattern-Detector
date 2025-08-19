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


# Domain-specific aspect keyword dictionaries
DOMAIN_ASPECTS = {
    'ecommerce': {
        'Battery': ['battery', 'charge', 'charging', 'backup', 'mah', 'power'],
        'Display': ['screen', 'display', 'panel', 'amoled', 'brightness', 'refresh rate'],
        'Camera': ['camera', 'photo', 'photos', 'picture', 'video', 'lens', 'sensor'],
        'Performance': ['speed', 'lag', 'processor', 'gaming', 'fast', 'slow', 'heating', 'heat'],
        'Build Quality': ['build', 'plastic', 'metal', 'durability', 'hinge', 'design', 'weight'],
        'Sound': ['sound', 'audio', 'speaker', 'bass', 'treble', 'mic', 'volume'],
        'Delivery': ['delivery', 'packaging', 'box', 'courier', 'shipping', 'package'],
    },
    'restaurant': {
        'Food Quality & Taste': ['taste', 'delicious', 'spicy', 'flavor', 'fresh', 'food', 'dish', 'portion', 'menu'],
        'Ambience & Vibe': ['ambience', 'atmosphere', 'vibe', 'seating', 'music', 'lighting', 'interior', 'decor'],
        'Service & Staff': ['service', 'staff', 'waiter', 'polite', 'delay', 'prompt', 'manager', 'hospitality'],
        'Hygiene & Cleanliness': ['clean', 'hygiene', 'hygienic', 'washroom', 'table', 'cleanliness'],
        'Value for Money': ['price', 'pricing', 'expensive', 'affordable', 'cheap', 'worth', 'cost', 'bill'],
    },
    'healthcare': {
        'Doctor Expertise': ['doctor', 'physician', 'diagnosis', 'treatment', 'consultation', 'surgeon', 'cure'],
        'Nursing & Staff Care': ['nurse', 'nursing', 'staff', 'receptionist', 'behavior', 'attendant', 'care'],
        'Cleanliness & Facilities': ['clean', 'hygiene', 'beds', 'room', 'icu', 'cleanliness', 'sanitized'],
        'Billing Transparency': ['bill', 'billing', 'charges', 'insurance', 'tpa', 'cost', 'expensive', 'hidden'],
        'Waiting Times': ['waiting', 'wait', 'queue', 'delay', 'emergency', 'appointment', 'rush'],
    },
    'automotive': {
        'Service Quality': ['service', 'servicing', 'repair', 'mechanic', 'parts', 'engine', 'oil', 'brakes', 'maintenance'],
        'Pricing Transparency': ['estimate', 'bill', 'charges', 'pricing', 'hidden', 'fair', 'quote', 'overpriced'],
        'Delivery & Timelines': ['delivery', 'delay', 'on time', 'handover', 'promised', 'prompt'],
        'Staff & Customer Handling': ['advisor', 'executive', 'staff', 'behavior', 'response', 'polite', 'manager'],
    },
    'general_business': {
        'Customer Service': ['service', 'staff', 'support', 'help', 'polite', 'response', 'behavior'],
        'Quality of Work': ['quality', 'work', 'job', 'professional', 'experience', 'standard'],
        'Pricing & Value': ['price', 'cost', 'expensive', 'reasonable', 'affordable', 'charges', 'bill'],
        'Timeliness': ['time', 'timely', 'punctual', 'delay', 'quick', 'schedule'],
    }
}


def extract_aspect_sentiments(reviews: list, category: str = 'ecommerce') -> dict:
    """
    Extracts sentences matching the target domain's aspects and computes 1.0 to 5.0 ratings.
    """
    if not reviews:
        return {'aspects': {}, 'flagged_reasons': []}

    nlp = get_nlp()
    vader = get_vader()

    aspect_dict = DOMAIN_ASPECTS.get(category, DOMAIN_ASPECTS['ecommerce'])
    aspect_scores = {aspect_name: [] for aspect_name in aspect_dict}

    for r in reviews:
        text = r.get('review_text', '')
        if not text or len(text.strip()) < 10:
            continue

        doc = nlp(text)

        for sent in doc.sents:
            sent_text = sent.text.lower()
            sent_polarity = vader.polarity_scores(sent.text)['compound']

            for aspect_name, keywords in aspect_dict.items():
                if any(kw in sent_text for kw in keywords):
                    star_equiv = 1.0 + ((sent_polarity + 1.0) / 2.0) * 4.0
                    aspect_scores[aspect_name].append(round(star_equiv, 2))

    summary = {}
    flagged_reasons = []

    for aspect_name, scores in aspect_scores.items():
        if len(scores) >= 2:
            avg_rating = round(sum(scores) / len(scores), 1)
            positive_count = sum(1 for s in scores if s >= 3.5)
            negative_count = sum(1 for s in scores if s < 2.5)

            summary[aspect_name] = {
                'score': avg_rating,
                'mentions': len(scores),
                'positive_mentions': positive_count,
                'negative_mentions': negative_count
            }

            if avg_rating <= 2.2 and len(scores) >= 3:
                flagged_reasons.append(
                    f"Frequent customer complaints on '{aspect_name}' (rated {avg_rating}/5.0 across {len(scores)} mentions)."
                )

    return {
        'aspects': summary,
        'flagged_reasons': flagged_reasons
    }