from pydantic import BaseModel
from typing import Dict, List, Optional

# --- Chat Analysis Schemas ---

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

class ChatMetadata(BaseModel):
    """Metadata about the chat"""
    total_messages: int
    users: List[str]
    start_date: str
    end_date: str
    media_count: int
    media_by_type: Dict[str, int]
    media_by_user: Dict[str, int]

class ChatAnalysisOutput(BaseModel):
    """Complete output for chat analysis"""
    metadata: ChatMetadata
    user_emotion_stats: Dict[str, Dict[str, EmotionStats]]  # user_name -> emotion -> stats
    overall_emotion_distribution: Dict[str, EmotionStats]  # emotion -> stats
    overall_sentiment_avg: float
    messages_per_day: float
    hourly_distribution: Dict[str, int]  # "00-02" -> count
    weekday_distribution: Dict[str, WeekdayStats]  # "Monday" -> WeekdayStats
    longest_streak: StreakInfo
    messages_per_user: Dict[str, int]  # user_name -> count
    avg_message_length_per_user: Dict[str, float]  # user_name -> avg_length
    top_emojis_per_user: Dict[str, List[EmojiCount]]  # user_name -> list of emojis
    top_words_per_user: Dict[str, List[WordCount]]  # user_name -> list of words
