from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Union # Ensure List is imported

import analysis_pipeline
from database import get_db
import schemas
import models

router = APIRouter()
MIN_LENGTH = 5 
LANGUAGE = "English"

# --- HELPER FUNCTION  ---
def prepare_record(d: dict, db: Session, language: str) -> models.single_text:
    """Creates, saves, and refreshes a single_text record in the database.
    note: request_id is no longer required and is not stored by default.
    """
    db_record = models.single_text(
        text=d.get("original_text"),
        cleaned_text=d.get("cleaned_text"),
        language=language,
        neg=d.get("sentiment_neg"),
        neu=d.get("sentiment_neu"),
        pos=d.get("sentiment_pos"),
        compound=d.get("sentiment_compound")
    )
    db.add(db_record)
    return db_record

# --- SINGLE ANALYSIS ENDPOINT ---
@router.post("/analyze-single",
             response_model=Union[schemas.AnalysisResult, schemas.ErrorOutput],
             status_code=status.HTTP_200_OK,
             summary="Analyze sentiment and clean a single text",
             tags=["Analysis"])
async def analyze_single_data(text_input: schemas.SingleTextInput, db: Session = Depends(get_db)):
    """
    Analyzes a single text review:
    - Performs cleaning.
    - Calculates VADER sentiment scores on the original text.
    - Saves results to the database.
    - Returns the analysis results (without database ID).
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
        print(f"Error during analysis: {e}") # Basic logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during text analysis."
        )

    # 3. Save to Database
    try:
        db_record = prepare_record(result_dict, db, language=LANGUAGE)
        db.commit()
        db.refresh(db_record)

    except Exception as e:
        db.rollback()
        print(f"Error saving to database: {e}") # Basic logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while saving the analysis results."
        )

    # 4. Return analysis result
    return result_dict

# --- BATCH ANALYSIS ENDPOINT (Completed) ---
@router.post("/analyze-batch",
             response_model=Union[List[schemas.AnalysisResult], schemas.ErrorOutput], 
             status_code=status.HTTP_200_OK,
             summary="Analyze sentiment and clean a batch of texts",
             tags=["Analysis"])
async def analyze_multiple_data(text_inputs: List[schemas.SingleTextInput], db: Session = Depends(get_db)): 
    """
    Analyzes a batch of text reviews:
    - Validates each text entry.
    - Performs cleaning.
    - Calculates VADER sentiment scores on the original texts.
    - Saves all results to the database in a single transaction.
    - Returns the list of analysis results.
    """
    # 1. Input Validation
    if not text_inputs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input list cannot be empty."
        )

    valid_inputs = []
    errors = []
    for i, item in enumerate(text_inputs):
        if not item.text or len(item.text.strip()) == 0:
            errors.append(f"Item {i}: Text field cannot be empty.")
            continue
        if len(item.text.strip()) < MIN_LENGTH:
            errors.append(f"Item {i}: Text must be at least {MIN_LENGTH} characters long.")
            continue
        valid_inputs.append(item.model_dump()) 

    if not valid_inputs:
        error_detail = "No valid text inputs provided. " + " ".join(errors)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )
    
    # Optional: inform the user about skipped items: add logic here.

    # 2. Perform Analysis on Valid Inputs
    try:
        # Pass the list of valid dictionaries
        result_list_of_dicts = analysis_pipeline.clean_and_sentiment(valid_inputs, language=LANGUAGE)

        # Check if the analysis function itself returned an error (less likely for batch)
        if isinstance(result_list_of_dicts, dict) and "error" in result_list_of_dicts:
             raise HTTPException (
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail=result_list_of_dicts["error"]
             )
        # Ensure it returned a list as expected
        if not isinstance(result_list_of_dicts, list):
             print(f"Unexpected analysis result type: {type(result_list_of_dicts)}")
             raise HTTPException (
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail="Analysis function returned an unexpected result format."
             )

    except Exception as e:
        print(f"Error during batch analysis: {e}") # Basic logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during batch text analysis."
        )

    # 3. Save all results to Database in one transaction
    db_records = []
    try:
        for result_item in result_list_of_dicts:
            # Prepare each record but don't commit yet
            db_record = prepare_record(result_item, db, language=LANGUAGE)
            db_records.append(db_record) # Keep track if you need IDs later

        db.commit() # Commit all added records at once to reduce complexity

        # Refresh records AFTER commit to get IDs
        # for i, record in enumerate(db_records):
        #    db.refresh(record)
        #    result_list_of_dicts[i]["db_id"] = record.id # Add db_id if needed

    except Exception as e:
        db.rollback() # Rollback the entire transaction if any save fails
        print(f"Error saving batch to database: {e}") # Basic logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while saving the batch analysis results."
        )

    # 4. Return the list of successful results
    return result_list_of_dicts