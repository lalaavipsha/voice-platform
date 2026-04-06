"""
Application configuration.
Loads settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "Voice Platform API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # AWS
    AWS_REGION: str = "eu-west-2"
    AWS_S3_BUCKET: str = ""
    DYNAMODB_TABLE: str = "voice-platform-conversations"

    # Amazon Bedrock (LLM)
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-haiku-20240307-v1:0"
    BEDROCK_MAX_TOKENS: int = 500
    BEDROCK_TEMPERATURE: float = 0.7

    # Amazon Polly (TTS)
    POLLY_VOICE_ID: str = "Matthew"
    POLLY_ENGINE: str = "neural"
    POLLY_OUTPUT_FORMAT: str = "mp3"

    # Amazon Transcribe (STT)
    TRANSCRIBE_LANGUAGE_CODE: str = "en-US"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:8000",  # Backend docs
        "https://d2xy0r5ne2t43p.cloudfront.net",  # Production frontend
        "http://d2xy0r5ne2t43p.cloudfront.net",  # Production frontend (http)
    ]

    # Rate limiting
    MAX_AUDIO_SIZE_MB: int = 25
    MAX_REQUESTS_PER_MINUTE: int = 20

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
