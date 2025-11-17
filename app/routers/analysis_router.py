import os
from nacl.exceptions import CryptoError
from app.security.encryption import NaClEnvelopeEncryption
from fastapi import APIRouter, HTTPException, status, UploadFile
from app.schemas import analysis as schemas
from analysis import chat_parser, analysis_chat

router = APIRouter()

def _get_encryption_helper() -> NaClEnvelopeEncryption:
    """Lazy-load encryption helper; raises HTTPException if SERVER_PRIVATE_KEY missing."""
    private_key = os.getenv("SERVER_PRIVATE_KEY")
    if not private_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Encryption not configured: SERVER_PRIVATE_KEY environment variable missing"
        )
    helper = getattr(_get_encryption_helper, "_helper", None)
    if helper is None:
        helper = NaClEnvelopeEncryption(private_key)
        setattr(_get_encryption_helper, "_helper", helper)
    return helper

def _analyze_chat_text(text: str):
    messages = chat_parser.parse_whatsapp_export(text)
    metadata = chat_parser.get_chat_metadata(messages)
    return analysis_chat.analyze_full_chat(messages, metadata)

# --- SINGLE ANALYSIS ENDPOINT ---
@router.get("/public-key",
            response_model=schemas.PublicKey,
            status_code=status.HTTP_200_OK,
            summary="Public Key for encryption",
            tags=["Public-Key"])
async def get_public_key():
    helper = _get_encryption_helper()
    return schemas.PublicKey(public_key=helper.public_key_b64)


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
        results = _analyze_chat_text(text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}"
        )
    
    return results 

@router.post("/analyze-conversation-encrypted",
             response_model=schemas.ChatAnalysisOutput,
             status_code=status.HTTP_200_OK,
             summary="Chat parsing and analysing Encrypted WhatsApp conversation",
             tags=["Analysis"])
async def analyze_encrypted(payload: schemas.EncryptedChatPayload):
    helper = _get_encryption_helper()
    try:
        decrypted_bytes = helper.decrypt(
            payload.client_public_key,
            payload.nonce,
            payload.ciphertext,
        )
    except CryptoError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid encrypted payload"
        )

    try:
        text = decrypted_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decrypted payload is not valid UTF-8"
        )

    try:
        return _analyze_chat_text(text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {e}",
        )