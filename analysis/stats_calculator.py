import emoji
import re
from collections import defaultdict
from analysis.analysis_core import process_text_spacy

# HELPERS
def __emotion_avg(scores: list[int]) -> float:
     if not scores:
          return 0.0
     return sum(scores) / len(scores)

def __emotion_frequency(user_messages: list[dict], emotion: str) -> int:
     return sum(1 for msg in user_messages 
                if msg.get('dominant_emotion') and
                msg.get('dominant_emotion')[0] == emotion)

def __emotion_percentage(frequency: int, user_messages: list[dict]) -> float:
     if not user_messages:
          return 0.0
     return frequency/len(user_messages) * 100

def __count_weekdays_in_period(start_date, end_date) -> dict:
     """
     Conta quanti lunedì, martedì, ecc. ci sono in un periodo.
     
     Args:
         start_date: data inizio (datetime o date)
         end_date: data fine (datetime o date)
     
     Returns:
         Dict con conteggio per ogni giorno: {"Monday": 73, "Tuesday": 73, ...}
     """
     from datetime import timedelta
     
     WEEKDAYS_NAME = ["Monday", "Tuesday", "Wednesday", "Thursday",
                      "Friday", "Saturday", "Sunday"]
     
     # Converti in date se necessario
     start = start_date.date() if hasattr(start_date, 'date') else start_date
     end = end_date.date() if hasattr(end_date, 'date') else end_date
     
     weekday_counts = {w: 0 for w in WEEKDAYS_NAME}
     current_date = start
     
     while current_date <= end:
          day_name = WEEKDAYS_NAME[current_date.weekday()]
          weekday_counts[day_name] += 1
          current_date += timedelta(days=1)
     
     return weekday_counts
     
def __calculate_emotion_stats(enriched_messages: list[dict], user_name: str = None) -> dict:
    """
    Calcola statistiche emozioni per un singolo utente.
    
    Args:
        enriched_messages: lista messaggi con campo 'emotions' (da analyze_full_chat)
        user_name: nome dell'utente da analizzare
    
    Returns:
        Dict con statistiche per ogni emozione (6 emozioni totali)
    """
    # GoEmotions 28 emotions
    EMOTIONS = ['admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring', 
                'confusion', 'curiosity', 'desire', 'disappointment', 'disapproval', 
                'disgust', 'embarrassment', 'excitement', 'fear', 'gratitude', 'grief', 
                'joy', 'love', 'nervousness', 'optimism', 'pride', 'realization', 
                'relief', 'remorse', 'sadness', 'surprise', 'neutral']
    if user_name:
         messages = [msg for msg in enriched_messages if msg['user'] == user_name]
    else:
         messages = enriched_messages

    scores = {emotion: [] for emotion in EMOTIONS}
    for emotion in EMOTIONS:
        scores[emotion] = [msg['emotions'][emotion] 
                          for msg in messages 
                          if msg['emotions'] is not None]

    stats = {}

    for emotion in EMOTIONS:
        emotion_scores = scores[emotion]
        avg = __emotion_avg(emotion_scores)
        max_score = max(emotion_scores) if emotion_scores else 0.0
        frequency = __emotion_frequency(messages, emotion)
        percentage = __emotion_percentage(frequency, messages)
        strong_count = sum(1 for msg in messages 
                          if msg['emotions'] and msg['emotions'][emotion] > 0.30)
        stats[emotion] = {
            'avg': round(avg, 2),
            'max': round(max_score, 2),
            'frequency': frequency,
            'percentage': round(percentage, 2),
            'strong_count': strong_count 
        }

    return stats

# compute emotions stats by users
def calculate_user_emotion_stats(enriched_messages: list[dict], user_name: str) -> dict:
     return __calculate_emotion_stats(enriched_messages, user_name)
# compute overall emotions stats 
def calculate_overall_emotion_distribution(enriched_messages: list[dict]) -> dict:
     return __calculate_emotion_stats(enriched_messages)

def calculate_avg_messages_per_day(metadata: dict) -> float:
     """
     Compute messages per day
     
     Args:
         metadata: Dict with start_date, end_date, total_messages
     
     Returns:
         Float with messages per day
     """
     if not metadata:
          return 0.0
     
     # Dates are already datetime objects from get_chat_metadata()
     start = metadata['start_date']
     end = metadata['end_date']
     
     # Calculate total days
     total_days = (end - start).days + 1
     
     if total_days == 0:
          return float(metadata['total_messages'])
     
     return round(metadata['total_messages'] / total_days, 2)

def compute_messages_per_hours_category(enriched_message: list[dict]) -> dict:
     HOURS = ["00-02", "02-04", "04-06", "06-08", "08-10", "10-12",
              "12-14", "14-16", "16-18", "18-20", "20-22", "22-24"]
     hours_dict = {k: 0 for k in HOURS}
     for msg in enriched_message:
         hour_category = msg['hour_category']
         if hour_category:
              hours_dict[hour_category] += 1
    
     return hours_dict

def compute_avg_and_count_messages_by_day(enriched_messages: list[dict], metadata: dict) -> dict:
     """
     Calcola statistiche messaggi per giorno della settimana.
     
     Args:
         enriched_messages: lista messaggi con timestamp e weekday
         metadata: dict con start_date e end_date per calcolare il numero totale di giorni
     
     Returns:
         Dict con total_messages e average per ogni giorno della settimana
     """
     WEEKDAYS_NAME = ["Monday", "Tuesday", "Wednesday", "Thursday",
                         "Friday", "Saturday", "Sunday"]
     weekdays = {w: dict() for w in WEEKDAYS_NAME}

     for msg in enriched_messages:
          if msg:
               weekday = msg['weekday']
               date = msg['timestamp'].date()

               if date not in weekdays[weekday]:
                    weekdays[weekday][date] = 0
               weekdays[weekday][date] += 1

     # Conta quanti giorni di ogni tipo ci sono nel periodo
     weekday_counts = __count_weekdays_in_period(metadata['start_date'], metadata['end_date'])
     
     # Calcola statistiche
     results = {}
     for weekday in WEEKDAYS_NAME:
          total_messages = sum(weekdays[weekday].values()) if weekdays[weekday] else 0
          total_weekdays_in_period = weekday_counts[weekday]
          
          if total_weekdays_in_period > 0:
               average = total_messages / total_weekdays_in_period
               results[weekday] = {
                    "total_messages": total_messages, 
                    "average": round(average, 2),
                    "days_in_period": total_weekdays_in_period
               }
          else:
               results[weekday] = {"total_messages": 0, "average": 0.0, "days_in_period": 0}

     return results

def compute_longest_conversation_streak(enriched_messages: list[dict], metadata: dict) -> dict:
     """
     Calcola lo streak più lungo di giorni consecutivi dove entrambi gli utenti hanno risposto.
     
     Args:
         enriched_messages: lista messaggi arricchiti con timestamp
         metadata: dict con 'users' (lista utenti della chat)
     
     Returns:
         Dict con: days (int), start_date (str), end_date (str)
     """
     if not enriched_messages or len(metadata.get('users', [])) < 2:
          return {"days": 0, "start_date": None, "end_date": None}
          
     # Raggruppa messaggi per data: {date: {user1, user2}}
     daily_users = defaultdict(set)
     for msg in enriched_messages:
          daily_users[msg['timestamp'].date()].add(msg['user'])
     
     # Trova giorni dove entrambi hanno scritto
     both_days = sorted([date for date, users in daily_users.items() if len(users) >= 2])
     
     if not both_days:
          return {"days": 0, "start_date": None, "end_date": None}
     
     # Trova lo streak più lungo
     max_streak = 1
     current_streak = 1
     best_start = both_days[0]
     best_end = both_days[0]
     streak_start = both_days[0]
     
     for i in range(1, len(both_days)):
          if (both_days[i] - both_days[i-1]).days == 1:  # Consecutivi
               current_streak += 1
               if current_streak > max_streak:
                    max_streak = current_streak
                    best_start = streak_start
                    best_end = both_days[i]
          else:  # Streak interrotto
               current_streak = 1
               streak_start = both_days[i]
     
     return {
          "days": max_streak,
          "start_date": best_start.isoformat(),
          "end_date": best_end.isoformat()
     }

def messages_per_user(enriched_messages: list[dict], metadata: dict) -> dict:
     users_rate = {user: 0 for user in metadata['users']}
     for msg in enriched_messages:
          if msg:
               users_rate[msg['user']] += 1

     return users_rate

def avg_message_length_per_user(enriched_messages: list[dict], metadata: dict) -> dict:
     users_data = {user: [0, 0] for user in metadata['users']}  # [count, total_length]
     
     for msg in enriched_messages:
          if msg:
               user = msg['user']
               length = len(msg['message'])
               users_data[user][0] += 1
               users_data[user][1] += length
     
     return {user: round(data[1] / data[0], 2) if data[0] > 0 else 0.0 
             for user, data in users_data.items()}

def top_emojis(enriched_messages: list[dict], metadata: dict, N: int = 10) -> dict:
     users_data = {user: defaultdict(int) for user in metadata['users']} 

     for msg in enriched_messages:
          if msg:
               emoji_list = emoji.emoji_list(msg['message'])
               for em_dict in emoji_list:
                    em = em_dict['emoji']
                    users_data[msg['user']][em] += 1
     
     # Ordina per count (decrescente) e prendi top N
     result = {}
     for user in users_data.keys():
          sorted_emojis = sorted(users_data[user].items(), key=lambda x: x[1], reverse=True)
          # Converti tuple in dizionari
          result[user] = [{"emoji": em, "count": cnt} for em, cnt in sorted_emojis[:N]]
     
     return result

def top_words_per_user(enriched_messages: list[dict], metadata: dict, N: int = 10) -> dict:
    
    users_words = {user: defaultdict(int) for user in metadata['users']}
    
    # Stopwords personalizzate: nomi utenti + parole comuni da media messages
    custom_stopwords = set()
    for user in metadata['users']:
        # Aggiungi ogni parola del nome utente (es. "Andrea Di Masi" → andrea, di, masi)
        custom_stopwords.update(word.lower() for word in user.split())
    
    # Aggiungi parole da "<Media omitted>" e simili
    custom_stopwords.update(['medium', 'omit', 'omitted', 'media', 'message', 'deleted'])
    
    for msg in enriched_messages:
        # Salta messaggi media e messaggi troppo corti
        if msg and msg['message'] and not msg.get('is_media', False):
            # Usa spaCy per pulire e lemmatizzare
            # Rimuovi PROPN (nomi propri) dalla lista per evitare nomi di persone/luoghi
            cleaned = process_text_spacy(msg['message'], pos_list=['NOUN', 'VERB', 'ADJ', 'ADV'])
            words = cleaned.split()
            
            for word in words:
                # Filtra: lunghezza > 2 E non in stopwords personalizzate
                if len(word) > 2 and word.lower() not in custom_stopwords:
                    users_words[msg['user']][word] += 1
    
    # Ordina e prendi top N
    result = {}
    for user, word_counts in users_words.items():
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        # Converti tuple in dizionari
        result[user] = [{"word": w, "count": cnt} for w, cnt in sorted_words[:N]]
    
    return result



