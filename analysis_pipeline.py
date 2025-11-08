import analysis_core 
import pandas as pd
import json

pos = ['NOUN', 'VERB', 'ADJ', 'ADV']

def clean_and_sentiment(data, language: str):
    """
    Cleans text and performs VADER sentiment analysis.
    Handles single dict input or list of dicts input.
    """

    # --- Single Dictionary Input ---
    if isinstance(data, dict):
        text = data.get('text', '')
        
        # Clean text
        temp_text = analysis_core.lower_replace(text)
        cleaned_text = analysis_core.process_text_spacy(temp_text, pos_list=pos)
        
        # Get VADER scores on ORIGINAL text
        sentiment_scores = analysis_core.get_vader_scores(text) 

        # Prepare output (request_id removed - not required)
        output = {
            "original_text": text,
            "cleaned_text": cleaned_text,
            "sentiment_neg": sentiment_scores['sentiment_neg'],
            "sentiment_neu": sentiment_scores['sentiment_neu'],
            "sentiment_pos": sentiment_scores['sentiment_pos'],
            "sentiment_compound": sentiment_scores['sentiment_compound']
        }
        return output
    
    # --- List of Dictionaries Input ---
    elif isinstance(data, list):
        if not data: # Handle empty list
             return [] 
                
        df = pd.DataFrame(data) 
        text_col = 'text' # Make sure your input JSON uses 'text'

        # Apply cleaning steps
        cleaned_series = df[text_col].apply(analysis_core.lower_replace)
        df['cleaned_text'] = cleaned_series.apply(lambda t: analysis_core.process_text_spacy(t, pos_list=pos))
        
        # Add VADER scores (using original text)
        df = analysis_core.add_vader_col(df, text_col) 
        df.rename(columns={'text': 'original_text'}, inplace=True)
        # Ensure we don't include request_id in the output records
        if 'request_id' in df.columns:
            df = df.drop(columns=['request_id'])
        # Return results as a list of dictionaries
        output_list = df.to_dict(orient='records')
        return output_list

    # --- Invalid Input ---
    else:
        return {"error": "Not valid input. Please provide a single object (dict) or a list of objects"}