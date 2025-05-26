import os
from typing import Optional

from pydantic import BaseModel


class Config:
    """Application configuration settings."""

    TITLE = os.getenv("A2F_FLASK_TITLE", "A2F Streaming Service API")
    DESCRIPTION = os.getenv("A2F_FLASK_DESCRIPTION", "An API for streaming blendshapes.")
    VERSION = os.getenv("A2F_FLASK_VERSION", "0.1.0")
    HOST = os.getenv("A2F_FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("A2F_FLASK_PORT", "8000"))
    DEFAULT_WORKERS = int(os.getenv("A2F_FLASK_DEFAULT_WORKERS", "2"))
    CLIENTS_PER_WORKER = int(os.getenv("A2F_FLASK_CLIENTS_PER_WORKER", "2"))
    TMP_DIR = os.getenv("A2F_FLASK_TMP_DIR", "tmp")
    LOG_FILE = os.getenv("A2F_FLASK_LOG_FILE", "a2fserver.log")


class EmotionWeights(BaseModel):
    amazement: float = 0.0
    anger: float = 0.0
    cheekiness: float = 0.0
    disgust: float = 0.0
    fear: float = 0.0
    grief: float = 0.0
    joy: float = 0.0
    outofbreath: float = 0.0
    pain: float = 0.0
    sadness: float = 0.0

    def __dict__(self) -> dict:
        """Convert the EmotionWeights model to a dictionary."""
        return {
            "amazement": self.amazement,
            "anger": self.anger,
            "cheekiness": self.cheekiness,
            "disgust": self.disgust,
            "fear": self.fear,
            "grief": self.grief,
            "joy": self.joy,
            "outofbreath": self.outofbreath,
            "pain": self.pain,
            "sadness": self.sadness,
        }
