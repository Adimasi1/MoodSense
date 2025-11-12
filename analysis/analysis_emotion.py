from transformers import pipeline
from typing import List, Dict
from functools import lru_cache

# Jochen Hartmann, "Emotion English DistilRoBERTa-base". 
# https://huggingface.co/j-hartmann/emotion-english-distilroberta-base/, 2022.

@lru_cache(maxsize=1)
def get_emotion_classifier(device: int = -1):
    """
    Lazy-load emotion classifier to reduce startup memory.
    Returns classifier with return_all_scores=True for complete emotion breakdown.
    Truncation enabled to handle long messages (max 512 tokens).
    
    Args:
        device: GPU device ID (0, 1, etc.) or -1 for CPU (default: -1)
    """
    return pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        return_all_scores=True,
        truncation=True,
        max_length=512,
        device=device  # 0 for GPU, -1 for CPU
    )


def analyze_emotion_batch(texts: List[str], batch_size: int = 32, use_gpu: bool = False) -> List[Dict[str, float]]:
    """
    Analyzes emotions for a batch of texts using DistilRoBERTa.
    
    Args:
        texts: List of text strings
        batch_size: Number of texts to process at once (default: 32)
        use_gpu: Whether to use GPU (default: False)
    
    Returns:
        List of dicts, each containing all 7 emotion scores:
        [
            {'anger': 0.103, 'disgust': 0.022, 'fear': 0.002, 'joy': 0.714, ...},
            {'anger': 0.015, 'sadness': 0.600, ...},
            ...
        ]
    
    Example:
        >>> texts = ["I love you!", "I'm so angry"]
        >>> results = analyze_emotion_batch(texts)
        >>> results[0]['joy']
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
            emotion_dict = {item['label']: item['score'] for item in result_list}
            results.append(emotion_dict)
    
    return results


def analyze_emotion_single(text: str) -> Dict[str, float]:
    """
    Analyzes emotions for a single text.
    
    Args:
        text: Text string
    
    Returns:
        Dict with all 7 emotion scores
    
    Example:
        >>> result = analyze_emotion_single("Hey, you know you are a good person!")
        >>> result
        {'anger': 0.103, 'disgust': 0.022, 'fear': 0.002, 'joy': 0.714, ...}
    """
    return analyze_emotion_batch([text])[0]


def get_dominant_emotion(emotion_dict: Dict[str, float], exclude_neutral: bool = True, neutral_threshold: float = 0.70) -> tuple[str, float]:
    """
    Finds the dominant emotion from emotion scores.
    
    Args:
        emotion_dict: Dict with emotion scores (e.g., {'joy': 0.7, 'anger': 0.1, ...})
        exclude_neutral: If True, only use neutral if it's very dominant (>neutral_threshold)
        neutral_threshold: Minimum score for neutral to be considered dominant (default: 0.70)
    
    Returns:
        Tuple of (emotion_label, score)
    
    Example:
        >>> emotions = {'joy': 0.714, 'anger': 0.103, 'neutral': 0.111, ...}
        >>> get_dominant_emotion(emotions)
        ('joy', 0.714)
        
        >>> emotions = {'joy': 0.05, 'anger': 0.02, 'neutral': 0.85, ...}
        >>> get_dominant_emotion(emotions)
        ('neutral', 0.85)
    """
    # If not excluding neutral at all, return max directly
    if not exclude_neutral:
        return max(emotion_dict.items(), key=lambda x: x[1])
    
    # If neutral is very dominant (>threshold), use it
    if emotion_dict.get('neutral', 0) > neutral_threshold:
        return ('neutral', emotion_dict['neutral'])
    
    # Otherwise, exclude neutral and find max among other emotions
    emotions_to_consider = [(k, v) for k, v in emotion_dict.items() if k != 'neutral']
    if not emotions_to_consider:
        return ('neutral', emotion_dict['neutral'])
    return max(emotions_to_consider, key=lambda x: x[1])


def filter_strong_emotions(emotion_dict: Dict[str, float], threshold: float = 0.30) -> Dict[str, float]:
    """
    Filters emotions above a certain threshold (useful for UI display).
    
    Args:
        emotion_dict: Dict with emotion scores
        threshold: Minimum score to include (default: 0.30)
    
    Returns:
        Dict with only strong emotions
    
    Example:
        >>> emotions = {'joy': 0.714, 'anger': 0.103, 'disgust': 0.022, 'neutral': 0.111}
        >>> filter_strong_emotions(emotions, threshold=0.10)
        {'joy': 0.714, 'anger': 0.103, 'neutral': 0.111}
    """
    return {emotion: score for emotion, score in emotion_dict.items() if score >= threshold}
