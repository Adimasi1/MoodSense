import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from functools import lru_cache


# Lazy-load spaCy model to reduce memory/startup peak on small instances.
@lru_cache(maxsize=1)
def get_nlp():
    import spacy
    return spacy.load('en_core_web_sm')

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
        "sentiment_neg": original_scores['neg'],
        "sentiment_neu": original_scores['neu'],
        "sentiment_pos": original_scores['pos'],
        "sentiment_compound": original_scores['compound']
    }
    return renamed_scores


