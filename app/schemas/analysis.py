from pydantic import BaseModel
from typing import Dict, List, Optional

# --- Chat Analysis Schemas ---

class PublicKey(BaseModel):
    public_key: str

class EncryptedChatPayload(BaseModel):
    client_public_key: str
    nonce: str
    ciphertext: str

class EmotionStats(BaseModel):
    """Statistics for a single emotion"""
    avg: float
    max: float
    frequency: int
    percentage: float
    strong_count: int

class WeekdayStats(BaseModel):
    """Statistics for a single weekday"""
    total_messages: int
    average: float
    days_in_period: int

class StreakInfo(BaseModel):
    """Information about conversation streak"""
    days: int
    start_date: Optional[str]
    end_date: Optional[str]

class EmojiCount(BaseModel):
    """Single emoji with count"""
    emoji: str
    count: int

class WordCount(BaseModel):
    """Single word with count"""
    word: str
    count: int

class SentimentScore(BaseModel):
    """VADER sentiment scores"""
    pos: float
    neu: float
    neg: float
    compound: float

class ChatMetadata(BaseModel):
    """Metadata about the chat"""
    total_messages: int
    users: List[str]
    user_mapping: Dict[str, str]  # {"user_1": "Andrea di Masi", "user_2": "Mario Rossi"}
    start_date: str
    end_date: str
    media_count: int
    media_by_type: Dict[str, int]
    media_by_user: Dict[str, int]

class ChatAnalysisOutput(BaseModel):
    """Complete output for chat analysis"""
    metadata: ChatMetadata
    user_emotion_stats: Dict[str, Dict[str, EmotionStats]]  # "user_1" -> emotion -> stats
    overall_emotion_distribution: Dict[str, EmotionStats]  # emotion -> stats
    overall_sentiment: SentimentScore
    messages_per_day: float
    hourly_distribution: Dict[str, int]  # "00-02" -> count
    weekday_distribution: Dict[str, WeekdayStats]  # "Monday" -> WeekdayStats
    longest_streak: StreakInfo
    messages_per_user: Dict[str, int]  # "user_1" -> count
    avg_message_length_per_user: Dict[str, float]  # "user_1" -> avg_length
    top_emojis_per_user: Dict[str, List[EmojiCount]]  # "user_1" -> list of emojis
    top_words_per_user: Dict[str, List[WordCount]]  # "user_1" -> list of words
