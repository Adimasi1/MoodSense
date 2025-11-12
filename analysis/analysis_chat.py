from typing import List, Dict
from analysis import analysis_emotion
from analysis import analysis_core
from analysis import stats_calculator

def analyze_full_chat(messages: list[dict], metadata: dict) -> dict:
  # 1. Analyze emotions (DistilRoBERTa)
  text_messages = [m for m in messages if not m['is_media']]
  texts = [m['message'] for m in text_messages]

  emotion_results = analysis_emotion.analyze_emotion_batch(texts)
  dominant_emotion_results = [analysis_emotion.get_dominant_emotion(emo_dict) 
                              for emo_dict in emotion_results]

  # 2. Analyze sentiment (VADER)
  sentiment_results = [analysis_core.get_vader_scores(t) for t in texts]

  # 3. Merge results with original messages
  enriched = []
  text_idx = 0
  for msg in messages:
    if msg['is_media']:
      enriched.append({**msg, 'emotions': None, 'sentiment': None})
    else:
      enriched.append({
        **msg, 
        'emotions': emotion_results[text_idx],
        'dominant_emotion': dominant_emotion_results[text_idx], 
        'sentiment_compound': sentiment_results[text_idx]['sentiment_compound']
      })
      text_idx += 1

  # 4. Calculate user emotion stats 
  users = metadata['users']
  user_emotion_stats = {}
  for user_name in users:
      emotion_stats = stats_calculator.calculate_user_emotion_stats(enriched, user_name)
      user_emotion_stats[user_name] = emotion_stats

  # 5. Overall emotion stats
  overall_emotion_dist = stats_calculator.calculate_overall_emotion_distribution(enriched)
  
  # Calculate average sentiment
  sentiment_scores = [m['sentiment_compound'] for m in enriched if m.get('sentiment_compound')]
  overall_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

  # 6. Additional statistics
  messages_per_day = stats_calculator.calculate_messages_per_day(metadata)
  hourly_distribution = stats_calculator.compute_messages_per_hours_category(enriched)
  weekday_distribution = stats_calculator.compute_avg_and_count_messages_grouped_by_day(enriched, metadata)
  longest_streak = stats_calculator.compute_longest_conversation_streak(enriched, metadata)
  messages_per_user = stats_calculator.messages_per_user(enriched, metadata)
  avg_msg_length = stats_calculator.avg_message_length_per_user(enriched, metadata)
  top_emojis_per_user = stats_calculator.top_emojis(enriched, metadata, N=10)
  top_words_per_user = stats_calculator.top_words_per_user(enriched, metadata, N=20)

  return {
      'user_emotion_stats': user_emotion_stats,
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
  }