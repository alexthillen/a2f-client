import asyncio
import base64
import json
import logging
import os
import secrets
from typing import Any, AsyncGenerator, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl

from app.config import Config, EmotionWeights
from app.streaming_logic import StreamingManager


def setup_logging() -> logging.Logger:
    """Configure logging for the application and related services."""
    log_file_path = os.path.join(os.getcwd(), Config.LOG_FILE)

    # Base logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, mode="a", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # Configure uvicorn logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = []
    uvicorn_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    uvicorn_handler.setFormatter(
        logging.Formatter("[uvicorn] %(asctime)s %(levelname)s %(message)s")
    )
    uvicorn_logger.addHandler(uvicorn_handler)
    uvicorn_logger.addHandler(logging.StreamHandler())
    uvicorn_logger.setLevel(logging.INFO)

    # Configure FastAPI logger
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.handlers = []
    fastapi_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    fastapi_handler.setFormatter(
        logging.Formatter("[fastapi] %(asctime)s %(levelname)s %(message)s")
    )
    fastapi_logger.addHandler(fastapi_handler)
    fastapi_logger.addHandler(logging.StreamHandler())
    fastapi_logger.setLevel(logging.INFO)

    return logging.getLogger(__name__)


def initialize_streaming_manager() -> StreamingManager:
    """Initialize the StreamingManager with appropriate configuration."""
    streaming_manager = StreamingManager(clients_per_worker=Config.CLIENTS_PER_WORKER)
    logger.info("StreamingManager initialized.")
    return streaming_manager


async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global streaming_manager
    streaming_manager = initialize_streaming_manager()
    yield
    for port in list(streaming_manager.locked_files.keys()):
        streaming_manager._release_lock(port)
    logger.info("Released locks for all ports.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return FastAPI(
        title=Config.TITLE,
        description=Config.DESCRIPTION,
        version=Config.VERSION,
        lifespan=lifespan,
    )


def decode_audio_content(content: bytes) -> bytes:
    """Decode audio content, handling both direct WAV and base64 encoded data."""
    if not content.startswith(b"RIFF"):
        try:
            return base64.b64decode(content)
        except Exception as e:
            logger.error(f"Failed to decode base64 audio content: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audio content format"
            )
    return content


async def save_audio_file(audio_file: UploadFile) -> str:
    """Save uploaded audio file to temporary location."""
    audio_filename = f"{Config.TMP_DIR}/{secrets.token_hex(8)}.wav"

    try:
        content = await audio_file.read()
        decoded_content = decode_audio_content(content)

        with open(audio_filename, "wb") as f:
            f.write(decoded_content)

        return audio_filename
    except Exception as e:
        logger.error(f"Failed to save audio file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process audio file"
        )


def cleanup_temp_file(filename: str) -> None:
    """Remove temporary file safely."""
    try:
        if os.path.exists(filename):
            os.remove(filename)
            logger.info(f"Cleaned up temporary file: {filename}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temporary file {filename}: {e}")


# Initialize logging and create app
logger = setup_logging()
streaming_manager: Optional[StreamingManager] = None
app = create_app()

# Ensure temporary directory exists
os.makedirs(Config.TMP_DIR, exist_ok=True)


@app.post("/process-audio/")
async def process_audio_endpoint(
    fps: Optional[int] = None,
    emotions: Optional[str] = Form(None),
    audio_file: UploadFile = File(...),
) -> StreamingResponse:
    """
    Process an audio file and stream back the processing status of each chunk.

    Args:
        fps: Frames per second for processing (optional)
        emotions: JSON string of emotion weights (optional)
        audio_file: The audio file to process

    Returns:
        StreamingResponse with processing results
    """
    if streaming_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Streaming manager not initialized",
        )

    # Parse emotions if provided
    emotion_weights = None
    if emotions:
        try:
            emotion_data = json.loads(emotions)
            emotion_weights = EmotionWeights(**emotion_data)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid emotions format: {e}"
            )

    audio_filename = None
    try:
        # Save and process audio file
        audio_filename = await save_audio_file(audio_file)
        generator = streaming_manager.submit_job(
            audio_source=audio_filename, fps=fps, emotions=emotion_weights
        )

        # Create response that will cleanup file after streaming
        async def cleanup_generator():
            try:
                async for chunk in generator:
                    yield chunk
            finally:
                if audio_filename:
                    cleanup_temp_file(audio_filename)

        return StreamingResponse(cleanup_generator())

    except Exception as e:
        # Cleanup on error
        if audio_filename:
            cleanup_temp_file(audio_filename)
        raise


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint to check if the server is running."""
    return {"message": f"{Config.TITLE} is running."}


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "streaming_manager": "initialized" if streaming_manager else "not initialized",
    }


if __name__ == "__main__":
    # Set up worker count in environment if not present
    logger.info(f"Starting server with {Config.DEFAULT_WORKERS} workers.")
    uvicorn.run(
        "app.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False,
        log_config=None,
        workers=Config.DEFAULT_WORKERS,
    )
