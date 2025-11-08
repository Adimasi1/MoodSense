import re
import pandas as pd
from typing import Union
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.decomposition import LatentDirichletAllocation, NMF
from functools import lru_cache


# Lazy-load spaCy model to reduce memory/startup peak on small instances.
@lru_cache(maxsize=1)
def get_nlp():
    import spacy
    return spacy.load('en_core_web_sm')

# ------------ Text Processing ------------
def lower_replace(text: str) -> str:
    temp_text = text.lower()
    temp_text = re.sub(r'\[.*?\]', '', temp_text)
    temp_text = re.sub(r'[^\w\s]', '', temp_text)

    return temp_text

def process_text_spacy(text: str, pos_list: list) -> str:
    nlp = get_nlp()
    doc = nlp(text)
    output = [
        token.lemma_
        for token in doc
        if not token.is_stop and token.pos_ in pos_list
    ]
    return ' '.join(output)

def cleaning_set_pipeline(series: pd.Series, pos: list) -> pd.Series:
    return (
        lower_replace(series)
        .apply(lambda text: process_text_spacy(text, pos_list = pos))
    )

# ------------ Count Vectorizer ------------
# count_frame return the count vectorized table
def count_vectorize(text_clean: pd.Series, stop_words:str = 'english', ngram_range:tuple = (1, 1), 
                    min_df:Union[int, float] = 2, max_df: Union[int, float] = 1.0) -> pd.DataFrame:
    cv = CountVectorizer(stop_words=stop_words, ngram_range=ngram_range, min_df=min_df, max_df=max_df)
    dtm = cv.fit_transform(text_clean)
    return dtm, cv

# ------------ TF-IDF: Term Frequency-Inverse Document Frequency ------------
# return the TF-IDF index 
def tfidf_vectorize(text_clean: pd.Series, stop_words:str = 'english', ngram_range:tuple = (1, 1), 
                    min_df:Union[int, float] = 2, max_df: Union[int, float] = 1.0) -> pd.DataFrame:
    tv = TfidfVectorizer(stop_words=stop_words, ngram_range=ngram_range, min_df=min_df, max_df=max_df)
    tfidf = tv.fit_transform(text_clean)
    return tfidf, tv

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

def create_vader_frame(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    vader_df = df[col_name].apply(get_vader_scores)
    vader_df = pd.json_normalize(vader_df)
    return vader_df

def add_vader_col(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    return df.join(create_vader_frame(df, col_name))

# ------------ NMF_modeling dor max 10000 rows dataset ------------
# NMF works well with TF-IDF vectorization.
def NMF_modeling(dtm, n_components: int = 5, vectorizer=None, random_state=42, 
                 topic_displayed: int=10, max_iter: int = 200):
    model = NMF(n_components=n_components, random_state=random_state, max_iter=max_iter)
    model.fit(dtm)
    feature_names = vectorizer.get_feature_names_out()
    topics_dict = {}

    for topic_idx, topic in enumerate(model.components_):
        top_words_indices = topic.argsort()[:-topic_displayed - 1: -1]
        top_words = [feature_names[i] for i in top_words_indices]
        topics_dict[f"topic_{topic_idx+1}"] = top_words

    return topics_dict

# ------------ Latent Dirichlet Allocation (LDA) for medium dataset (10001 - 100000) ------------
# LDA works with raw word counts from CountVectorizer.
def LDA_modeling(dtm, n_components: int = 5, vectorizer=None, random_state=42, 
                 topic_displayed: int=10, max_iter: int = 200):
    model = LatentDirichletAllocation(n_components=n_components, random_state=random_state, max_iter=max_iter)
    model.fit(dtm)
    feature_names = vectorizer.get_feature_names_out()
    topics_dict = {}
    
    for topic_idx, topic in enumerate(model.components_):
        top_words_indices = topic.argsort()[:-topic_displayed - 1: -1]
        top_words = [feature_names[i] for i in top_words_indices]
        topics_dict[f"topic_{topic_idx+1}"] = top_words

    return topics_dict
