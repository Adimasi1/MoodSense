from fastapi import APIRouter, HTTPException, status, UploadFile, File
from typing import List, Union
import schemas
from analysis import chat_parser, analysis_chat

router = APIRouter()
MIN_LENGTH = 5 
LANGUAGE = "English"

# --- SINGLE ANALYSIS ENDPOINT ---
@router.post("/analyze-single",
             response_model=Union[schemas.AnalysisResult, schemas.ErrorOutput],
             status_code=status.HTTP_200_OK,
             summary="Analyze sentiment and clean a single text",
             tags=["Analysis"])
async def analyze_single_data(text_input: schemas.SingleTextInput):
    """
    Analyzes a single text review (stateless):
    - Performs cleaning.
    - Calculates VADER sentiment scores on the original text.
    - Returns the analysis results (no database save).
    """
    # 1. Input Validation
    if not text_input.text or len(text_input.text.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text field cannot be empty."
        )
    # Corrected typo: status_code
    if len(text_input.text.strip()) < MIN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text must be at least {MIN_LENGTH} characters long."
        )

    # 2. Perform Analysis
    try:
        result_dict = analysis_pipeline.clean_and_sentiment(text_input.model_dump(), language=LANGUAGE)

    except Exception as e:
        print(f"Error during analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during text analysis."
        )

    # 3. Return analysis result (no database save)
    return result_dict
