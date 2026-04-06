"""
Voice API endpoints.
Handles the core voice interaction flow:
  1. Receive audio from user (speech)
  2. Transcribe audio to text (STT - Whisper)
  3. Generate AI response (LLM - GPT)
  4. Convert response to speech (TTS)
  5. Return audio response
"""

import io

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.services.ai_service import ai_service

router = APIRouter()


class TextRequest(BaseModel):
    """Request body for text-based chat."""

    message: str
    conversation_id: str | None = None


class TranscriptionResponse(BaseModel):
    """Response from speech-to-text."""

    text: str


class ChatResponse(BaseModel):
    """Response from text chat."""

    reply: str
    conversation_id: str | None = None


@router.post("/voice/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio to text using OpenAI Whisper.

    Accepts audio files (mp3, wav, webm, m4a, etc.)
    Returns the transcribed text.
    """
    # Validate file size
    contents = await audio.read()
    max_size = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
    if len(contents) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large. Max size: {settings.MAX_AUDIO_SIZE_MB}MB",
        )

    # Validate file type
    allowed_types = {
        "audio/mpeg",
        "audio/wav",
        "audio/webm",
        "audio/mp4",
        "audio/m4a",
        "audio/ogg",
        "audio/flac",
    }
    if audio.content_type and audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio format: {audio.content_type}",
        )

    try:
        text = await ai_service.transcribe(contents, audio.filename or "audio.webm")
        return TranscriptionResponse(text=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/voice/chat", response_model=ChatResponse)
async def chat(request: TextRequest):
    """
    Send a text message and get an AI response.

    This is the LLM step - takes text input and returns text output.
    """
    try:
        reply = await ai_service.chat(request.message, request.conversation_id)
        return ChatResponse(reply=reply, conversation_id=request.conversation_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/voice/speak")
async def text_to_speech(request: TextRequest):
    """
    Convert text to speech using OpenAI TTS.

    Returns an audio stream (mp3).
    """
    try:
        audio_bytes = await ai_service.text_to_speech(request.message)
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=response.mp3"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")


@router.post("/voice/converse")
async def full_voice_conversation(audio: UploadFile = File(...)):
    """
    Full voice conversation flow:
    1. Transcribe user's audio to text
    2. Get AI response
    3. Convert AI response to speech
    4. Return audio response

    This is the main endpoint for voice-to-voice interaction.
    """
    # Step 1: Transcribe
    contents = await audio.read()
    max_size = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
    if len(contents) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large. Max size: {settings.MAX_AUDIO_SIZE_MB}MB",
        )

    try:
        # Step 1: Speech to Text
        user_text = await ai_service.transcribe(contents, audio.filename or "audio.webm")

        # Handle empty transcription (silence / no speech detected)
        if not user_text or not user_text.strip():
            user_text = "(no speech detected)"

        # Step 2: Get AI response
        ai_reply = await ai_service.chat(user_text)

        # Step 3: Text to Speech
        audio_bytes = await ai_service.text_to_speech(ai_reply)

        # URL-encode header values (headers can't have newlines/special chars)
        from urllib.parse import quote
        safe_user_text = quote(user_text, safe="")
        safe_ai_reply = quote(ai_reply, safe="")

        # Return audio with transcription in headers
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=response.mp3",
                "X-User-Text": safe_user_text,
                "X-AI-Reply": safe_ai_reply,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice conversation failed: {str(e)}")
