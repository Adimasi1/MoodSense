import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from functools import lru_cache


# Lazy-load spaCy model to reduce memory/startup peak on small instances.
@lru_cache(maxsize=1)
def get_nlp():
    import spacy
    # Disabilita parser/ner per velocizzare (servono solo POS tagging e lemmatization)
    return spacy.load('en_core_web_sm', disable=['parser', 'ner'])

# ------------ Text Processing ------------
def process_text_spacy(text: str, pos_list: list) -> str:
    nlp = get_nlp()
    doc = nlp(text)
    output = [
        token.lemma_
        for token in doc
        if not token.is_stop and token.pos_ in pos_list
    ]
    return ' '.join(output)

# ------------ Sentiment Analysis with VADER ------------
analyzer = SentimentIntensityAnalyzer()

def get_vader_scores(text: str) -> dict:
    original_scores = analyzer.polarity_scores(text)
    renamed_scores = {
        "sentiment_neg": round(original_scores['neg'], 2),
        "sentiment_neu": round(original_scores['neu'], 2),
        "sentiment_pos": round(original_scores['pos'], 2),
        "sentiment_compound": round(original_scores['compound'], 2)
    }
    return renamed_scores


