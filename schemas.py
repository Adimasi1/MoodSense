from pydantic import BaseModel
from typing import Dict, List

# --- Chat Analysis Schemas ---
class EmotionStats(BaseModel):
    """Statistics for a single emotion"""
    avg: float
    max: float
    frequency: int
    percentage: float
    strong_count: int

class UserEmotionStats(BaseModel):
    """Emotion statistics for a single user"""
    user_emotion_stats: Dict[str, Dict[str, EmotionStats]]

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
    user_stats: List[UserEmotionStats]
    overall_emotion_distribution: Dict[str, EmotionStats]
    overall_sentiment_avg: float
    messages_count: int

"""
      v 'user_emotion_stats': user_emotion_stats,
      'overall_emotion_distribution': overall_emotion_dist,
      'overall_sentiment_avg': overall_sentiment,
      'messages_analyzed': enriched,
      'messages_per_day': messages_per_day,
      'hourly_distribution': hourly_distribution,
      'weekday_distribution': weekday_distribution,
      'longest_streak': longest_streak,
      'messages_per_user': messages_per_user,
      'avg_message_length_per_user': avg_msg_length,
      'top_emojis_per_user': top_emojis_per_user,
      'top_words_per_user': top_words_per_user

"""

