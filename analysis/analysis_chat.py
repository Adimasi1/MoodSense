from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from analysis import analysis_emotion
from analysis import analysis_core
from analysis import stats_calculator

def analyze_full_chat(messages: list[dict], metadata: dict) -> dict:
  # 1. Filtra messaggi di testo
  text_messages = [m for m in messages if not m['is_media']]
  texts = [m['message'] for m in text_messages]

  # 2. Parallelizza emotion e sentiment (risparmia 5-10 sec su chat lunghe)
  with ThreadPoolExecutor(max_workers=2) as executor:
    # Lancia emotion e sentiment in parallelo
    emotion_future = executor.submit(analysis_emotion.analyze_emotion_batch, texts)
    sentiment_future = executor.submit(lambda: [analysis_core.get_vader_scores(t) for t in texts])
    
    # Aspetta i risultati
    emotion_results = emotion_future.result()
    sentiment_results = sentiment_future.result()
  
  dominant_emotion_results = [analysis_emotion.get_dominant_emotion(emo_dict) 
                              for emo_dict in emotion_results]

  # 3. Merge results with original messages
  enriched = []
  text_idx = 0
  for msg in messages:
    if msg['is_media']:
      enriched.append({**msg, 'emotions': None, 'sentiment_pos': None, 'sentiment_neu': None, 'sentiment_neg': None, 'sentiment_compound': None})
    else:
      enriched.append({
        **msg, 
        'emotions': emotion_results[text_idx],
        'dominant_emotion': dominant_emotion_results[text_idx],
        'sentiment_pos': sentiment_results[text_idx]['sentiment_pos'],
        'sentiment_neu': sentiment_results[text_idx]['sentiment_neu'],
        'sentiment_neg': sentiment_results[text_idx]['sentiment_neg'],
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
  
  # 6. Calculate overall sentiment (pos, neu, neg, compound)
  overall_sentiment = analysis_emotion.calculate_overall_sentiment(enriched)

  # 7. Additional statistics
  messages_per_day = stats_calculator.calculate_avg_messages_per_day(metadata)
  hourly_distribution = stats_calculator.compute_messages_per_hours_category(enriched)
  weekday_distribution = stats_calculator.compute_avg_and_count_messages_by_day(enriched, metadata)
  longest_streak = stats_calculator.compute_longest_conversation_streak(enriched, metadata)
  messages_per_user = stats_calculator.messages_per_user(enriched, metadata)
  avg_msg_length = stats_calculator.avg_message_length_per_user(enriched, metadata)
  top_emojis_per_user = stats_calculator.top_emojis(enriched, metadata, N=10)
  top_words_per_user = stats_calculator.top_words_per_user(enriched, metadata, N=20)

  # 8. Prepare metadata for response (convert dates to strings)
  # Create user mapping: user_1, user_2, etc.
  sorted_users = sorted(metadata['users'])
  user_mapping = {f"user_{i+1}": name for i, name in enumerate(sorted_users)}
  reverse_mapping = {name: f"user_{i+1}" for i, name in enumerate(sorted_users)}
  
  metadata_output = {
      'total_messages': metadata['total_messages'],
      'users': metadata['users'],
      'user_mapping': user_mapping,  # {"user_1": "Andrea di Masi", "user_2": "Mario Rossi"}
      'start_date': metadata['start_date'].isoformat(),
      'end_date': metadata['end_date'].isoformat(),
      'media_count': metadata['total_media'],
      'media_by_type': metadata['media_by_type'],
      'media_by_user': metadata['media_by_user']
  }

  # Convert all user-specific dictionaries to use generic keys (user_1, user_2, etc.)
  user_emotion_stats_generic = {reverse_mapping[user]: stats for user, stats in user_emotion_stats.items()}
  messages_per_user_generic = {reverse_mapping[user]: count for user, count in messages_per_user.items()}
  avg_msg_length_generic = {reverse_mapping[user]: avg for user, avg in avg_msg_length.items()}
  top_emojis_generic = {reverse_mapping[user]: emojis for user, emojis in top_emojis_per_user.items()}
  top_words_generic = {reverse_mapping[user]: words for user, words in top_words_per_user.items()}

  return {
      'metadata': metadata_output,
      'user_emotion_stats': user_emotion_stats_generic,
      'overall_emotion_distribution': overall_emotion_dist,
      'overall_sentiment': overall_sentiment,
      # 'messages_analyzed': enriched, ---> we have to send back the statistics without the message bodies
      'messages_per_day': messages_per_day,
      'hourly_distribution': hourly_distribution,
      'weekday_distribution': weekday_distribution,
      'longest_streak': longest_streak,
      'messages_per_user': messages_per_user_generic,
      'avg_message_length_per_user': avg_msg_length_generic,
      'top_emojis_per_user': top_emojis_generic,
      'top_words_per_user': top_words_generic
  }