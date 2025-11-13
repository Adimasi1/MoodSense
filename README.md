# MoodSense - WhatsApp Chat Emotion & Sentiment Analyzer

A powerful FastAPI application that analyzes WhatsApp chat exports to extract emotions, sentiment, and conversation statistics using AI models.

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [How It Works](#how-it-works)
- [Deployment](#deployment)

---

## ✨ Features

- **Emotion Analysis**: Uses DistilRoBERTa AI model to detect 7 emotions (joy, sadness, anger, fear, disgust, surprise, neutral)
- **Sentiment Analysis**: Uses VADER to calculate positive/negative sentiment scores
- **Chat Statistics**:
  - Messages per day, per user, per weekday, per hour
  - Average message length
  - Longest conversation streak (consecutive days both users replied)
  - Top emojis used by each user
  - Top words used by each user (with smart filtering)
- **WhatsApp Export Parser**: Supports Italian and English WhatsApp export formats
- **REST API**: Easy to integrate with mobile apps or web frontends
- **Fast Processing**: Batch processing for efficient analysis of large chats

---

## 🛠 Technology Stack

- **FastAPI**: Modern Python web framework for building APIs
- **Pydantic**: Data validation using Python type hints
- **Transformers (HuggingFace)**: DistilRoBERTa model for emotion detection
- **VADER Sentiment**: Lexicon-based sentiment analysis
- **spaCy**: Natural language processing for text cleaning and lemmatization
- **Python 3.11+**: Modern Python with type hints

---

## 📁 Project Structure

```
sentiment-analyzer/
│
├── app/                          # FastAPI application package
│   ├── __init__.py              # Makes 'app' a Python package
│   ├── routers/                 # API endpoint definitions
│   │   ├── __init__.py
│   │   └── analysis_router.py   # Chat analysis endpoint (/analyze-conversation)
│   └── schemas/                 # Pydantic models for request/response validation
│       ├── __init__.py
│       └── analysis.py          # All schemas for chat analysis API
│
├── analysis/                     # Core business logic (AI models, parsers, calculators)
│   ├── __init__.py
│   ├── analysis_chat.py         # Main orchestrator: calls emotion, sentiment, stats
│   ├── analysis_core.py         # VADER sentiment + spaCy text processing
│   ├── analysis_emotion.py      # DistilRoBERTa emotion detection (batch processing)
│   ├── chat_parser.py           # WhatsApp .txt file parser (Italian/English formats)
│   └── stats_calculator.py      # All statistics calculations (messages, streaks, emojis, etc.)
│
├── test/                         # Test files
│   ├── test_stats_calculator.py # Unit tests for statistics functions
│   ├── test_analysis_chat.py    # Integration tests for full analysis
│   └── WA/                      # Sample WhatsApp export files for testing
│
├── main.py                       # FastAPI app entry point (uvicorn main:app)
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── LICENSE                       # MIT License
└── .gitignore                   # Files to exclude from Git
```

---

## 📂 Detailed File Descriptions

### **Root Directory**

#### `main.py`

- **What it does**: Creates the FastAPI application and registers API routes
- **Key code**:
  - Creates `FastAPI()` instance with title, description, version
  - Adds CORS middleware (allows requests from any origin)
  - Includes the analysis router with prefix `/api/v1`
  - Defines `/` (root) and `/health` endpoints

---

### **`app/` folder** - FastAPI Application Layer

This folder contains everything related to the web API (endpoints, request/response validation).

#### `app/routers/analysis_router.py`

- **What it does**: Defines the `/analyze-conversation` endpoint
- **How it works**:
  1. Receives uploaded `.txt` file via HTTP POST
  2. Validates file type (must be `.txt`)
  3. Reads file content and decodes to UTF-8 text
  4. Calls parser → analysis → returns JSON response
  5. Handles errors and returns proper HTTP status codes
- **Import structure**:
  - `from app.schemas import analysis as schemas` - validation models
  - `from analysis import chat_parser, analysis_chat` - core logic

#### `app/schemas/analysis.py`

- **What it does**: Defines all Pydantic models for data validation
- **Key models**:
  - `ChatAnalysisOutput`: Main response structure with all statistics
  - `ChatMetadata`: Info about chat (users, dates, message count)
  - `EmotionStats`: Statistics for one emotion (avg, max, frequency, percentage)
  - `WeekdayStats`: Messages per weekday with realistic averages
  - `StreakInfo`: Longest conversation streak data
  - `EmojiCount`, `WordCount`: Top emojis/words with counts
- **Why it's important**: Ensures API always returns valid, consistent data

---

### **`analysis/` folder** - Core Business Logic

This folder contains the "brain" of the application: AI models, parsers, calculators.

#### `analysis/analysis_chat.py`

- **What it does**: Main orchestrator that coordinates all analysis steps
- **Process** (8 steps):
  1. Filters text messages (excludes media-only messages)
  2. Analyzes emotions using DistilRoBERTa (batch processing)
  3. Analyzes sentiment using VADER
  4. Merges AI results with original messages (creates "enriched messages")
  5. Calculates emotion statistics per user
  6. Calculates overall emotion distribution
  7. Calculates average sentiment score
  8. Calls all statistics functions (messages/day, streaks, emojis, etc.)
  9. Prepares metadata for API response (converts dates to ISO strings)
- **Returns**: Dictionary with 12 keys (metadata + 11 statistics)

#### `analysis/analysis_emotion.py`

- **What it does**: Emotion detection using HuggingFace Transformers
- **Model**: `j-hartmann/emotion-english-distilroberta-base`
- **Key functions**:
  - `get_emotion_classifier()`: Loads the AI model (cached, lazy-loaded)
  - `analyze_emotion_batch()`: Analyzes multiple texts at once (batch_size=32)
  - `get_dominant_emotion()`: Finds the strongest emotion (excludes neutral if <70%)
- **Output**: For each message, returns 7 emotion scores (0.0 to 1.0)
- **GPU support**: Can use GPU if available (device=0), defaults to CPU

#### `analysis/analysis_core.py`

- **What it does**: Sentiment analysis (VADER) and text cleaning (spaCy)
- **Key functions**:
  - `get_nlp()`: Loads spaCy model (`en_core_web_sm`) - cached
  - `process_text_spacy()`: Cleans text, removes stopwords, lemmatizes words
  - `get_vader_scores()`: Returns sentiment scores (neg, neu, pos, compound)
- **When used**:
  - VADER: called for every message in `analysis_chat.py`
  - spaCy: called by `top_words_per_user()` in stats calculator

#### `analysis/chat_parser.py`

- **What it does**: Parses WhatsApp `.txt` export files into structured data
- **Supports**:
  - Italian format: `11/10/2024, 14:23 - Mario Rossi: Ciao`
  - English format: `10/11/2024, 2:23 PM - John Doe: Hello`
  - Multi-line messages (continuations without timestamp)
  - Media messages (`<Media omitted>`, photos, videos, GIFs, etc.)
  - System messages (filtered out by default)
- **Key functions**:
  - `parse_whatsapp_export()`: Main parser, returns list of message dictionaries
  - `get_chat_metadata()`: Extracts total messages, users, date range, media counts
  - `parse_timestamp()`: Converts date/time strings to Python datetime
  - `detect_media_type()`: Identifies media type (photo, video, GIF, etc.)
  - `get_hour_category()`: Converts hour to time slot (e.g., "08-10")
  - `weekday_from_int_to_string()`: Converts 0-6 to Monday-Sunday
- **Output structure**: Each message is a dict with:
  - `timestamp`, `weekday`, `hour_category`
  - `user`, `message`, `message_length`
  - `is_media`, `media_type`, `is_system`

#### `analysis/stats_calculator.py`

- **What it does**: Calculates all conversation statistics
- **Public functions** (called by `analysis_chat.py`):
  - `calculate_user_emotion_stats()`: Emotion stats for one user
  - `calculate_overall_emotion_distribution()`: Combined emotion stats
  - `calculate_avg_messages_per_day()`: Total messages / total days
  - `compute_messages_per_hours_category()`: Messages in 12 time slots (00-02, 02-04, etc.)
  - `compute_avg_and_count_messages_by_day()`: Messages per weekday with realistic averages
  - `compute_longest_conversation_streak()`: Finds longest consecutive days both users replied
  - `messages_per_user()`: Count per user
  - `avg_message_length_per_user()`: Average characters per user
  - `top_emojis()`: Top N emojis per user (returns list of dicts: `{emoji, count}`)
  - `top_words_per_user()`: Top N words per user with smart filtering
- **Helper functions** (private, start with `__`):
  - `__emotion_avg()`, `__emotion_frequency()`, `__emotion_percentage()`
  - `__count_weekdays_in_period()`: Counts how many Mondays/Tuesdays/etc. in date range
  - `__calculate_emotion_stats()`: Core emotion calculation logic
- **Smart filtering in `top_words_per_user()`**:
  - Removes user names (extracts from metadata)
  - Removes media artifacts ("medium", "omit", "omitted")
  - Uses spaCy POS tagging (keeps NOUN, VERB, ADJ, ADV)
  - Lemmatizes words (e.g., "running" → "run")
  - Filters short words (<3 characters)

---

### **`test/` folder** - Test Files

Contains test scripts to validate the code works correctly.

#### `test/test_stats_calculator.py`

- **What it does**: Unit tests for all statistics functions
- **Coverage**: 11 tests covering all public functions in `stats_calculator.py`
- **Uses mock data**: Small MOCK_MESSAGES and MOCK_METADATA for fast testing

#### `test/test_analysis_chat.py`

- **What it does**: Integration test for full chat analysis pipeline
- **Tests**: End-to-end analysis with real WhatsApp export file
- **Output**: Saves complete analysis to `full_chat_analysis_output.txt`

#### `test/WA/` folder

- **Contains**: Sample WhatsApp export files for testing
- **Examples**:
  - Small chats (125 messages) for quick tests
  - Large chats (2000+ messages) for performance tests
  - Different formats (Italian, English, 12h/24h time)

---

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/Adimasi1/MoodSense.git
   cd MoodSense
   ```

2. **Create virtual environment** (recommended)

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model**

   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Run the server**

   ```bash
   uvicorn main:app --reload
   ```

6. **Open browser**
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

---

## 💻 Usage

### 1. Export WhatsApp Chat

- Open WhatsApp on your phone
- Go to a chat → Menu → More → Export chat
- Choose "Without media"
- Send the `.txt` file to your computer

### 2. Call the API

**Using curl:**

```bash
curl -X POST "http://localhost:8000/api/v1/analyze-conversation" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@chat.txt"
```

**Using Python requests:**

```python
import requests

with open("chat.txt", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/analyze-conversation",
        files={"file": f}
    )

data = response.json()
print(data["metadata"])
print(data["overall_sentiment_avg"])
```

**Using Postman:**

1. Create POST request to `http://localhost:8000/api/v1/analyze-conversation`
2. Go to Body → form-data
3. Key: `file` (type: File)
4. Value: Select your WhatsApp `.txt` file
5. Send

### 3. Response Example

```json
{
  "metadata": {
    "total_messages": 1962,
    "users": ["Andrea", "Rodante"],
    "start_date": "2023-10-14T18:10:00",
    "end_date": "2025-02-27T02:52:00",
    "media_count": 224
  },
  "overall_sentiment_avg": 0.454,
  "messages_per_day": 3.91,
  "longest_streak": {
    "days": 30,
    "start_date": "2024-04-16",
    "end_date": "2024-05-15"
  },
  "top_emojis_per_user": {
    "Andrea": [
      {"emoji": "♥️", "count": 88},
      {"emoji": "🥹", "count": 80}
    ]
  },
  ...
}
```

---

## 📡 API Endpoints

### `POST /api/v1/analyze-conversation`

Analyzes a WhatsApp chat export file.

**Request:**

- Method: POST
- Content-Type: multipart/form-data
- Body: file (WhatsApp .txt export)

**Response:** `ChatAnalysisOutput` (see `app/schemas/analysis.py`)

**Errors:**

- 400: Invalid file type (not .txt)
- 500: Processing error (invalid format, parsing failed, etc.)

### `GET /`

Root endpoint, returns API information.

### `GET /health`

Health check endpoint, returns `{"status": "healthy"}`.

---

## 🔬 How It Works

### Emotion Detection

Uses the **DistilRoBERTa** model fine-tuned on emotion classification:

- Model: `j-hartmann/emotion-english-distilroberta-base`
- 7 emotions: anger, disgust, fear, joy, neutral, sadness, surprise
- Each message gets 7 scores (0.0 to 1.0)
- Dominant emotion: highest score (excludes neutral if <70%)

### Sentiment Analysis

Uses **VADER** (Valence Aware Dictionary and sEntiment Reasoner):

- Lexicon-based (no training needed)
- Returns: negative, neutral, positive, compound scores
- Compound: overall sentiment (-1.0 to +1.0)
- Good for social media/chat text

### Statistics Calculation

- **Realistic averages**: Divides by ALL days in period, not just active days
  - Example: 15 messages on Monday over 501 days with 73 Mondays total = 0.21 avg/Monday
- **Smart word filtering**: Removes user names, media artifacts, stopwords
- **Streak detection**: Finds longest consecutive days where BOTH users sent messages
- **Batch processing**: Analyzes emotions in batches of 32 messages for speed

---

## 🌐 Deployment

### Deploy to Render (Free Tier)

1. **Create `render.yaml`** (optional, for auto-deploy):

   ```yaml
   services:
     - type: web
       name: moodsense
       env: python
       buildCommand: 'pip install -r requirements.txt && python -m spacy download en_core_web_sm'
       startCommand: 'uvicorn main:app --host 0.0.0.0 --port $PORT'
   ```

2. **Push to GitHub**:

   ```bash
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

3. **Connect Render to GitHub**:

   - Go to https://render.com
   - New → Web Service
   - Connect repository
   - Render auto-detects Python and builds

4. **Environment**:

   - Python version: 3.11
   - Build command: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

5. **Access your API**:
   - URL: `https://your-app-name.onrender.com`
   - Docs: `https://your-app-name.onrender.com/docs`

### Performance Notes

- **CPU-only**: DistilRoBERTa runs on CPU (no GPU on free tier)
- **Processing time**: ~10 seconds for 125 messages, ~2-3 minutes for 2000 messages
- **Memory**: ~1GB RAM needed for models
- **Cold start**: First request after inactivity takes ~30 seconds (model loading)

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Andrea Di Masi** - [GitHub](https://github.com/Adimasi1)

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

## 📧 Support

For questions or issues, please open a GitHub issue.
