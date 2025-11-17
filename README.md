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

- **Emotion Analysis**: Uses RoBERTa AI model (GoEmotions dataset) to detect 28 emotions including love, caring, admiration, excitement, and more
- **Sentiment Analysis**: Uses VADER to calculate positive/negative sentiment scores
- **End-to-End Encryption**: Optional X25519 + XChaCha20-Poly1305 encryption for secure chat analysis
- **Chat Statistics**:
  - Messages per day, per user, per weekday, per hour
  - Average message length
  - Longest conversation streak (consecutive days both users replied)
  - Top emojis used by each user
  - Top words used by each user (with smart filtering)
- **WhatsApp Export Parser**: Supports Italian and English WhatsApp export formats
- **REST API**: Easy to integrate with mobile apps or web frontends
- **Fast Processing**: ONNX-optimized model for 5x faster inference with lower memory usage
- **Cloud-Native**: Deployed on Google Cloud Run with automatic scaling

---

## 🛠 Technology Stack

- **FastAPI**: Modern Python web framework for building APIs
- **Pydantic**: Data validation using Python type hints
- **Transformers (HuggingFace)**: RoBERTa model fine-tuned on Google Research GoEmotions dataset
- **ONNX Runtime**: Optimized inference engine for 5x faster emotion detection
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

- **What it does**: Emotion detection using HuggingFace Transformers with ONNX optimization
- **Model**: `SamLowe/roberta-base-go_emotions-onnx` (Google Research GoEmotions dataset)
- **28 Emotions**: admiration, amusement, anger, annoyance, approval, caring, confusion, curiosity, desire, disappointment, disapproval, disgust, embarrassment, excitement, fear, gratitude, grief, joy, love, nervousness, optimism, pride, realization, relief, remorse, sadness, surprise, neutral
- **Key functions**:
  - `get_emotion_classifier()`: Loads the ONNX-optimized AI model (cached, lazy-loaded)
  - `analyze_emotion_batch()`: Analyzes multiple texts at once (batch_size=128)
  - `get_dominant_emotion()`: Finds the strongest emotion with optional neutral exclusion
- **Output**: For each message, returns 28 emotion scores (0.0 to 1.0)
- **Performance**: ONNX quantized INT8 model is 5x faster than PyTorch, uses 75% less memory
- **GPU support**: Runs on CPU (optimized for Render deployment)

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
- **28 Emotions tracked**: admiration, amusement, anger, annoyance, approval, caring, confusion, curiosity, desire, disappointment, disapproval, disgust, embarrassment, excitement, fear, gratitude, grief, joy, love, nervousness, optimism, pride, realization, relief, remorse, sadness, surprise, neutral
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

#### Option A: Plaintext Analysis

**Using curl:**

```bash
curl -X POST "https://moodsense-38104758698.europe-west1.run.app/api/v1/analyze-conversation" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@chat.txt"
```

**Using Python requests:**

```python
import requests

with open("chat.txt", "rb") as f:
    response = requests.post(
        "https://moodsense-38104758698.europe-west1.run.app/api/v1/analyze-conversation",
        files={"file": f}
    )

data = response.json()
print(data["metadata"])
print(data["overall_sentiment_avg"])
```

**Using Postman:**

1. Create POST request to `https://moodsense-38104758698.europe-west1.run.app/api/v1/analyze-conversation`
2. Go to Body → form-data
3. Key: `file` (type: File)
4. Value: Select your WhatsApp `.txt` file
5. Send

#### Option B: Encrypted Analysis (Recommended)

**Using Dart (Flutter/Mobile):**

See `dart_example/` folder for a complete client implementation with X25519 + XChaCha20-Poly1305 encryption.

**Using Python:**

```python
import requests
from nacl.public import PrivateKey, PublicKey, Box
from nacl.utils import random
from base64 import b64encode, b64decode

# 1. Get server public key
response = requests.get("https://moodsense-38104758698.europe-west1.run.app/api/v1/public-key")
server_public_key = PublicKey(b64decode(response.json()["public_key"]))

# 2. Generate client keypair
client_private_key = PrivateKey.generate()
client_public_key = client_private_key.public_key

# 3. Encrypt chat data
box = Box(client_private_key, server_public_key)
with open("chat.txt", "r", encoding="utf-8") as f:
    plaintext = f.read().encode("utf-8")

encrypted = box.encrypt(plaintext)
nonce = encrypted.nonce
ciphertext = encrypted.ciphertext

# 4. Send encrypted request
response = requests.post(
    "https://moodsense-38104758698.europe-west1.run.app/api/v1/analyze-conversation-encrypted",
    json={
        "encrypted_data": b64encode(ciphertext).decode(),
        "client_public_key": b64encode(bytes(client_public_key)).decode(),
        "nonce": b64encode(nonce).decode()
    }
)

data = response.json()
print(data["metadata"])
```

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

Analyzes a WhatsApp chat export file (plaintext).

**Request:**

- Method: POST
- Content-Type: multipart/form-data
- Body: file (WhatsApp .txt export)

**Response:** `ChatAnalysisOutput` (see `app/schemas/analysis.py`)

**Errors:**

- 400: Invalid file type (not .txt or application/octet-stream)
- 500: Processing error (invalid format, parsing failed, etc.)

### `POST /api/v1/analyze-conversation-encrypted`

Analyzes an encrypted WhatsApp chat export.

**Request:**

- Method: POST
- Content-Type: application/json
- Body: `{"encrypted_data": "base64", "client_public_key": "base64", "nonce": "base64"}`

**Response:** `ChatAnalysisOutput` (decrypted server-side)

**Encryption:**

- Uses X25519 key exchange + HKDF-SHA256 key derivation
- XChaCha20-Poly1305 AEAD for symmetric encryption
- Client must fetch server public key from `/api/v1/public-key` first

### `GET /api/v1/public-key`

Returns the server's X25519 public key for encryption.

**Response:** `{"public_key": "base64_encoded_key"}`

### `GET /`

Root endpoint, returns API information.

### `GET /health`

Health check endpoint, returns `{"status": "healthy"}`.

---

## 🔬 How It Works

### Emotion Detection

Uses the **RoBERTa** model fine-tuned on Google Research GoEmotions dataset (ONNX optimized):

- Model: `SamLowe/roberta-base-go_emotions-onnx`
- Dataset: GoEmotions (58k Reddit comments curated by Google Research, Amazon Alexa, Stanford - ACL 2020)
- **28 emotions**: admiration, amusement, anger, annoyance, approval, caring, confusion, curiosity, desire, disappointment, disapproval, disgust, embarrassment, excitement, fear, gratitude, grief, joy, **love**, nervousness, optimism, pride, realization, relief, remorse, sadness, surprise, neutral
- Each message gets 28 scores (0.0 to 1.0)
- Dominant emotion: highest score (with optional neutral exclusion)
- **Performance**: ONNX quantized INT8 model - 5x faster inference, 125 MB vs 499 MB (75% smaller)
- **Quality**: F1 score 0.81 for love detection (Precision: 0.74, Recall: 0.90)
- License: MIT (commercial use allowed)

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
- **Batch processing**: Analyzes emotions in batches of 128 messages for optimal speed with ONNX

---

## 🌐 Deployment

### Deploy to Google Cloud Run

This project is deployed on **Google Cloud Run** with automatic GitHub continuous deployment.

#### Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed (optional, for command-line deployment)
3. **GitHub repository** connected to Cloud Run

#### Deployment Steps

1. **Enable Required APIs**:

   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   ```

2. **Set up GitHub Continuous Deployment**:

   - Go to [Cloud Run Console](https://console.cloud.google.com/run)
   - Click **CREATE SERVICE**
   - Select **Continuously deploy from a repository**
   - Connect your GitHub account and select the `MoodSense` repository
   - Branch: `main`
   - Build type: **Dockerfile**
   - Region: `europe-west1` (or your preferred region)

3. **Configure Service**:

   - **Memory**: **2 GiB** (required for ONNX model + spaCy + processing)
   - **CPU**: 1 CPU
   - **Min instances**: 0 (pay only when used)
   - **Max instances**: 1 (or more for high traffic)
   - **Port**: 8080 (auto-detected from Dockerfile)
   - **Authentication**: Allow unauthenticated invocations (for public API)

4. **Set Environment Variables**:

   - `SERVER_PRIVATE_KEY`: Base64-encoded X25519 private key (generate with `python generate_keypair.py`)
   - `CLOUD_RUN_ENV`: `true` (enables local-only model loading)

5. **Deploy**:
   - Click **CREATE**
   - Cloud Run will build the Docker image and deploy
   - You'll get a URL like `https://moodsense-XXXXXXXXX.region.run.app`

#### Automatic Deployment

Every push to the `main` branch triggers an automatic rebuild and deployment.

#### Manual Deployment via CLI

```bash
gcloud run deploy moodsense \
  --source . \
  --region europe-west1 \
  --memory 2Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --port 8080 \
  --allow-unauthenticated \
  --set-env-vars CLOUD_RUN_ENV=true
```

### Performance Notes

- **CPU-only**: RoBERTa ONNX model runs efficiently on CPU (no GPU needed)
- **Processing time**: ~10-15 seconds for 1738 messages with ONNX optimization
- **Memory**: ~1.5-2 GB RAM total (FastAPI + transformers + ONNX model + spaCy + processing)
- **Required**: **2 GiB RAM minimum** on Cloud Run (512 MB causes out-of-memory errors)
- **Cold start**: First request after inactivity takes ~30-45 seconds (container startup + model loading)
- **Cost**: With 0 min instances, you only pay per request (~€0.00001 per request)

### Security Notes

- **Encryption**: The `SERVER_PRIVATE_KEY` environment variable must be set for encrypted endpoints to work
- **CORS**: Update `main.py` with your actual frontend domains
- **Secrets**: Never commit private keys to GitHub - use Cloud Run environment variables
- **.dockerignore**: Excludes test files, examples, and sensitive data from the Docker image

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
