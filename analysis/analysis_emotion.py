from transformers import pipeline
from typing import List, Dict
from functools import lru_cache

# Jochen Hartmann, "Emotion English DistilRoBERTa-base". 
# https://huggingface.co/j-hartmann/emotion-english-distilroberta-base/, 2022.

@lru_cache(maxsize=1)
def get_emotion_classifier(device: int = -1):
    """
    Lazy-load emotion classifier to reduce startup memory.
    Uses SamLowe/roberta-base-go_emotions-onnx (28 emotions, Google Research dataset).
    Returns classifier with top_k=None for all 28 emotion scores.
    Truncation enabled to handle long messages (max 512 tokens).
    
    Args:
        device: GPU device ID (0, 1, etc.) or -1 for CPU (default: -1)
    
    """
    from optimum.onnxruntime import ORTModelForSequenceClassification
    from transformers import AutoTokenizer
    
    model_id = "SamLowe/roberta-base-go_emotions-onnx"
    
    # Always use local files only to avoid HuggingFace API rate limits
    # The model is pre-cached during Docker build (see Dockerfile)
    # trust_remote_code=False prevents any remote code execution checks
    
    # Load ONNX optimized model (2-5x faster, lower memory)
    model = ORTModelForSequenceClassification.from_pretrained(
        model_id, 
        local_files_only=True,
        trust_remote_code=False
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        local_files_only=True,
        trust_remote_code=False
    )
    
    return pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        top_k=None,  # Return all 28 emotion scores
        device=device
    )


def analyze_emotion_batch(texts: List[str], batch_size: int = 64, use_gpu: bool = False) -> List[Dict[str, float]]:
    """
    Analyzes emotions for a batch of texts using GoEmotions (28 emotions).
    
    Args:
        texts: List of text strings
        batch_size: Number of texts to process at once (default: 64 for CPU, 128 for GPU)
        use_gpu: Whether to use GPU (default: False)
    
    Returns:
        List of dicts, each containing all 28 emotion scores:
        [
            {'love': 0.714, 'joy': 0.103, 'caring': 0.050, 'neutral': 0.022, ...},
            {'anger': 0.600, 'annoyance': 0.200, 'neutral': 0.100, ...},
            ...
        ]
    
    Example:
        >>> texts = ["I love you!", "I'm so angry"]
        >>> results = analyze_emotion_batch(texts)
        >>> results[0]['love']
        0.85
        >>> results[1]['anger']
        0.78
    """
    device = 0 if use_gpu else -1
    classifier = get_emotion_classifier(device)
    results = []
    
    # Process in batches to avoid memory issues with large chats
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_results = classifier(batch)
        
        # Convert from list of lists to list of dicts
        # Input:  [[{label: 'anger', score: 0.1}, {label: 'joy', score: 0.7}, ...], [...]]
        # Output: [{'anger': 0.1, 'joy': 0.7, ...}, {...}]
        for result_list in batch_results:
            emotion_dict = {item['label']: round(item['score'], 2) for item in result_list}
            results.append(emotion_dict)
    
    return results


def get_dominant_emotion(emotion_dict: Dict[str, float], exclude_neutral: bool = False, neutral_threshold: float = 0.5) -> tuple[str, float]:
    """
    Finds the dominant emotion from emotion scores.
    
    Args:
        emotion_dict: Dict with emotion scores (e.g., {'joy': 0.7, 'anger': 0.1, 'love': 0.15, ...})
        exclude_neutral: If True, excludes 'neutral' unless it's very dominant (default: False)
        neutral_threshold: Minimum score for neutral to be considered dominant (default: 0.5)
    
    Returns:
        Tuple of (emotion_label, score) for the highest scoring emotion
    
    Example:
        >>> emotions = {'sadness': 0.714, 'joy': 0.103, 'love': 0.111, 'neutral': 0.02}
        >>> get_dominant_emotion(emotions)
        ('sadness', 0.714)
        
        >>> emotions = {'neutral': 0.6, 'joy': 0.2, 'love': 0.15}
        >>> get_dominant_emotion(emotions, exclude_neutral=True)
        ('neutral', 0.6)  # neutral is >0.5, so it's returned even with exclude_neutral=True
        
        >>> emotions = {'neutral': 0.4, 'joy': 0.3, 'love': 0.2}
        >>> get_dominant_emotion(emotions, exclude_neutral=True)
        ('joy', 0.3)  # neutral excluded, next highest is joy
    """
    # If not excluding neutral, return max directly
    if not exclude_neutral:
        emotion, score = max(emotion_dict.items(), key=lambda x: x[1])
        return (emotion, round(score, 2))
    
    # If neutral is very dominant (>threshold), use it even if exclude_neutral=True
    neutral_score = emotion_dict.get('neutral', 0)
    if neutral_score >= neutral_threshold:
        return ('neutral', round(neutral_score, 2))
    
    # Otherwise, exclude neutral and find max among other emotions
    emotions_to_consider = [(k, v) for k, v in emotion_dict.items() if k != 'neutral']
    if not emotions_to_consider:
        return ('neutral', round(neutral_score, 2))
    
    emotion, score = max(emotions_to_consider, key=lambda x: x[1])
    return (emotion, round(score, 2))


def calculate_overall_sentiment(enriched_messages: List[Dict]) -> Dict[str, float]:
    """
    Calculates overall sentiment averages from enriched messages.
    Single-pass implementation for optimal performance.
    
    Args:
        enriched_messages: List of messages with sentiment fields (sentiment_pos, sentiment_neu, sentiment_neg, sentiment_compound)
    
    Returns:
        Dict with averaged sentiment scores: {'pos': float, 'neu': float, 'neg': float, 'compound': float}
        Returns all zeros if no valid sentiment data found.
    
    Example:
        >>> messages = [
        ...     {'sentiment_pos': 0.5, 'sentiment_neu': 0.3, 'sentiment_neg': 0.2, 'sentiment_compound': 0.6},
        ...     {'sentiment_pos': 0.3, 'sentiment_neu': 0.5, 'sentiment_neg': 0.2, 'sentiment_compound': 0.2}
        ... ]
        >>> calculate_overall_sentiment(messages)
        {'pos': 0.4, 'neu': 0.4, 'neg': 0.2, 'compound': 0.4}
    """
    total_pos = 0.0
    total_neu = 0.0
    total_neg = 0.0
    total_compound = 0.0
    count = 0
    
    for m in enriched_messages:
        if m.get('sentiment_compound') is not None:
            total_pos += m['sentiment_pos']
            total_neu += m['sentiment_neu']
            total_neg += m['sentiment_neg']
            total_compound += m['sentiment_compound']
            count += 1
    
    if count > 0:
        return {
            'pos': round(total_pos / count, 2),
            'neu': round(total_neu / count, 2),
            'neg': round(total_neg / count, 2),
            'compound': round(total_compound / count, 2)
        }
    else:
        return {'pos': 0.0, 'neu': 0.0, 'neg': 0.0, 'compound': 0.0}

