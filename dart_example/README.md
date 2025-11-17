# MoodSense Dart/Flutter Client

Client Dart/Flutter per MoodSense API - analisi emozioni e sentiment di chat WhatsApp esportate.

## 📦 File da condividere

**Pacchetto completo per Flutter/Dart:**

1. `lib/moodsense_client.dart` - Client principale ✅
2. `pubspec.yaml` - Dipendenze necessarie ✅
3. `README.md` - Documentazione ✅

## 🚀 Setup Rapido

### 1. Aggiungi dipendenze in `pubspec.yaml`

```yaml
dependencies:
  http: ^1.1.0
  http_parser: ^4.0.0
  cryptography: ^2.5.0 # Solo se usi encryption (opzionale)
```

### 2. Installa

```bash
flutter pub get
# oppure
dart pub get
```

### 3. Copia `moodsense_client.dart` in `lib/`

## 💻 Uso Base (Plaintext - CONSIGLIATO)

```dart
import 'dart:io';
import 'package:your_app/moodsense_client.dart';

void main() async {
  final client = MoodSenseClient();

  // Leggi file esportato da WhatsApp
  final chatText = await File('chat.txt').readAsString();

  // Analizza (timeout 2 minuti consigliato)
  final result = await client
      .analyzePlaintext(chatText)
      .timeout(Duration(minutes: 2));

  // Usa i risultati
  print('Messaggi totali: ${result["metadata"]["total_messages"]}');
  print('Utenti: ${result["metadata"]["users"]}');
  print('Love score: ${result["overall_emotion_distribution"]["love"]["avg"]}');
  print('Caring score: ${result["overall_emotion_distribution"]["caring"]["avg"]}');
  print('Sentiment: ${result["overall_sentiment"]["compound"]}');

  client.dispose();
}
```

## 📊 Struttura Risposta API

```dart
{
  "metadata": {
    "total_messages": 1962,
    "users": ["Andrea Di Masi", "..."],
    "user_mapping": {"user_1": "Andrea Di Masi", "user_2": "..."},
    "start_date": "2023-10-14T18:10:00",
    "end_date": "2025-02-27T02:52:00",
    "media_count": 158
  },
  "overall_emotion_distribution": {
    "love": {"avg": 0.17, "frequency": 288},
    "caring": {"avg": 0.2, "frequency": 360},
    "joy": {"avg": 0.15, "frequency": 245},
    // ... altre 25 emozioni
  },
  "overall_sentiment": {
    "pos": 0.25, "neu": 0.65, "neg": 0.10, "compound": 0.34
  },
  "messages_per_day": 3.91,
  "user_emotion_stats": {
    "user_1": {"dominant_emotion": "love", "top_3": [...]},
    "user_2": {...}
  },
  "top_emojis_per_user": {...},
  "top_words_per_user": {...}
}
```

## 🌐 API Endpoint

**Production:** `https://moodsense-38104758698.europe-west1.run.app`

## ⚡ Performance

- **2000 messaggi**: ~77 secondi
- **Cold start**: +30-45 secondi (prima richiesta)
- **Consiglio**: timeout di 2-3 minuti

## 🎭 28 Emozioni Rilevate (GoEmotions)

**Positive:** admiration, amusement, approval, caring, desire, excitement, gratitude, joy, love, optimism, pride, relief

**Negative:** anger, annoyance, disappointment, disapproval, disgust, embarrassment, fear, grief, nervousness, remorse, sadness

**Neutral/Ambiguous:** confusion, curiosity, realization, surprise, neutral

## 🔐 Encryption (Opzionale - WIP)

L'endpoint encrypted è disponibile ma ha problemi di compatibilità HKDF Dart↔Python.
**Consigliato:** usa solo `analyzePlaintext()` per ora.

## 📝 Note Importanti

1. File WhatsApp esportati devono essere in formato testo UTF-8
2. Supporta export italiani e inglesi
3. Prima richiesta ha cold start (~30s aggiuntivi)
4. API hosted su Google Cloud Run (europe-west1)
5. Free tier: ~50 analisi/giorno gratis

## 🐛 Troubleshooting

**Timeout errors:** Aumenta timeout a 3 minuti

```dart
.timeout(Duration(minutes: 3))
```

**File encoding:** Assicurati UTF-8

```dart
final text = await file.readAsString(encoding: utf8);
```

**Cold start lento:** Normale per prima richiesta, poi veloce
