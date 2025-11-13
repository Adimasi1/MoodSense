from fastapi import APIRouter, HTTPException, status, UploadFile, File
import schemas
from analysis import chat_parser, analysis_chat

router = APIRouter()

# --- SINGLE ANALYSIS ENDPOINT ---
@router.post("/analyze-conversation",
             response_model=schemas.ChatAnalysisOutput,
             status_code=status.HTTP_200_OK,
             summary="Chat parsing and analysing WhatsApp conversation",
             tags=["Analysis"])
async def analyzer_chat(file: UploadFile):
    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are accepted"
        )
    if file.content_type not in ['text/plain', 'application/octet-stream']:
        raise HTTPException(
            status_code=400,
            detail="Invalid content type"
        )
    
    content = await file.read()     # bytes
    text = content.decode('utf-8')  # to str    

    try:
        messages = chat_parser.parse_whatsapp_export(text)
        metadata = chat_parser.get_chat_metadata(messages)
        results = analysis_chat.analyze_full_chat(messages, metadata)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}"
        )
    
    return results 