from pydantic import BaseModel
from typing import Optional

# --- Output Schemas ---
class SingleTextInput(BaseModel):
    text: str

class AnalysisResult(BaseModel):
    original_text: str
    cleaned_text: str
    sentiment_neg: float
    sentiment_neu: float
    sentiment_pos: float
    sentiment_compound: float

class ErrorOutput(BaseModel):
    error: str


