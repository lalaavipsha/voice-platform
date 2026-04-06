"""
AI Service - handles all AWS AI/ML interactions.

Uses AWS-native services only (no third-party APIs):
  - Speech-to-Text: Amazon Transcribe
  - Chat/LLM: Amazon Bedrock (Claude)
  - Text-to-Speech: Amazon Polly
"""

import json
import tempfile
import uuid
from pathlib import Path

import boto3

from app.config import settings

SYSTEM_PROMPT = """You are Avi, a friendly AI voice assistant built on AWS.
Your name is Avi. Always introduce yourself as Avi when greeted.
Keep your responses concise and conversational since they will be spoken aloud.
Aim for 1-3 sentences unless the user asks for detailed information.
Be friendly, clear, and helpful. Never use placeholder text like [Assistant Name]."""


class AIService:
    """Manages all AI/ML operations using AWS services."""

    def __init__(self):
        self._transcribe_client = None
        self._bedrock_client = None
        self._polly_client = None
        self._s3_client = None

    @property
    def transcribe_client(self):
        """Lazy-initialize the Transcribe client."""
        if self._transcribe_client is None:
            self._transcribe_client = boto3.client(
                "transcribe", region_name=settings.AWS_REGION
            )
        return self._transcribe_client

    @property
    def bedrock_client(self):
        """Lazy-initialize the Bedrock Runtime client."""
        if self._bedrock_client is None:
            self._bedrock_client = boto3.client(
                "bedrock-runtime", region_name=settings.AWS_REGION
            )
        return self._bedrock_client

    @property
    def polly_client(self):
        """Lazy-initialize the Polly client."""
        if self._polly_client is None:
            self._polly_client = boto3.client(
                "polly", region_name=settings.AWS_REGION
            )
        return self._polly_client

    @property
    def s3_client(self):
        """Lazy-initialize the S3 client (used for Transcribe input)."""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                "s3", region_name=settings.AWS_REGION
            )
        return self._s3_client

    async def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        """
        Transcribe audio to text using Amazon Transcribe.

        Uses the streaming API for real-time transcription when possible,
        falls back to batch transcription via S3 for larger files.

        Args:
            audio_bytes: Raw audio file bytes
            filename: Original filename (used for format detection)

        Returns:
            Transcribed text string
        """
        # Determine media format from filename
        suffix = Path(filename).suffix.lower().lstrip(".")
        media_format_map = {
            "webm": "webm",
            "mp3": "mp3",
            "mp4": "mp4",
            "m4a": "mp4",
            "wav": "wav",
            "flac": "flac",
            "ogg": "ogg",
        }
        media_format = media_format_map.get(suffix, "webm")

        # Use S3 for batch transcription
        job_name = f"voice-platform-{uuid.uuid4().hex[:12]}"
        s3_key = f"transcribe-input/{job_name}.{suffix}"
        bucket = settings.AWS_S3_BUCKET

        if not bucket:
            # If no S3 bucket configured, use a temp file approach with
            # Transcribe's start_transcription_job pointing to S3
            raise ValueError(
                "AWS_S3_BUCKET is required for transcription. "
                "Set it in your .env file."
            )

        # Upload audio to S3
        self.s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=audio_bytes,
        )

        try:
            # Start transcription job
            self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={"MediaFileUri": f"s3://{bucket}/{s3_key}"},
                MediaFormat=media_format,
                LanguageCode=settings.TRANSCRIBE_LANGUAGE_CODE,
            )

            # Wait for completion (poll every 2 seconds)
            import asyncio

            while True:
                status = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                job_status = status["TranscriptionJob"]["TranscriptionJobStatus"]

                if job_status == "COMPLETED":
                    break
                elif job_status == "FAILED":
                    reason = status["TranscriptionJob"].get("FailureReason", "Unknown")
                    raise RuntimeError(f"Transcription failed: {reason}")

                await asyncio.sleep(2)

            # Get the transcript
            transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]

            # Download and parse the transcript JSON
            import urllib.request

            with urllib.request.urlopen(transcript_uri) as response:
                transcript_json = json.loads(response.read().decode())

            text = transcript_json["results"]["transcripts"][0]["transcript"]
            return text

        finally:
            # Clean up S3 object
            try:
                self.s3_client.delete_object(Bucket=bucket, Key=s3_key)
            except Exception:
                pass  # Best effort cleanup

            # Clean up transcription job
            try:
                self.transcribe_client.delete_transcription_job(
                    TranscriptionJobName=job_name
                )
            except Exception:
                pass  # Best effort cleanup

    async def chat(self, message: str, conversation_id: str | None = None) -> str:
        """
        Generate an AI response using Amazon Bedrock (Claude).

        Args:
            message: User's text message
            conversation_id: Optional conversation ID for context (future use)

        Returns:
            AI response text
        """
        # TODO: Add conversation history from DynamoDB when database is set up

        # Bedrock Claude Messages API format
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": settings.BEDROCK_MAX_TOKENS,
            "temperature": settings.BEDROCK_TEMPERATURE,
            "system": SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": message},
            ],
        })

        response = self.bedrock_client.invoke_model(
            modelId=settings.BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]

    async def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech using Amazon Polly.

        Args:
            text: Text to convert to speech

        Returns:
            Audio bytes (MP3 format)
        """
        # Polly has a 3000 character limit per request
        # For longer text, we'd need to split and concatenate
        if len(text) > 3000:
            text = text[:3000]

        response = self.polly_client.synthesize_speech(
            Text=text,
            OutputFormat=settings.POLLY_OUTPUT_FORMAT,
            VoiceId=settings.POLLY_VOICE_ID,
            Engine=settings.POLLY_ENGINE,
        )

        # Read the audio stream
        audio_stream = response["AudioStream"]
        return audio_stream.read()


# Singleton instance
ai_service = AIService()
