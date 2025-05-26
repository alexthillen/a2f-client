import os
import sys
import tempfile
from loguru import logger
from scipy.io import wavfile
import time
from functools import wraps

logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | " "<level>{level: <8}</level> | {message}",
)
logger.add(
    "a2f_client.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    backtrace=True,
    diagnose=True,
)


def delayed_return(delay_time):
    """
    Delays the execution of a function by a specified amount of time.

    Args:
        delay_time (float): The amount of time to delay in seconds.
    """

    def decorator_delay(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time.sleep(delay_time)
            return func(*args, **kwargs)

        return wrapper

    return decorator_delay


def load_audio(audio_path: str) -> str:
    """Load audio file and return its path."""
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if not audio_path.endswith(".wav"):
        raise ValueError(f"Audio file must be a .wav file: {audio_path}")
    sample_rate, data = wavfile.read(audio_path)
    duration = len(data) / sample_rate
    return audio_path, duration


def merge_blendshapes(blendshapes1: dict, blendshapes2: dict) -> dict:
    """
    Merge two facial-animation chunks by concatenating their frame data.

    Both chunks must have identical:
      - exportFps
      - numPoses
      - facsNames
      - joints

    Resulting chunk has:
      - numFrames = blendshapes1.numFrames + blendshapes2.numFrames
      - weightMat, rotations, translations concatenated in time
      - trackPath chosen from the first non-empty path
    """
    # Basic validations
    if blendshapes1["exportFps"] != blendshapes2["exportFps"]:
        raise ValueError(
            f"exportFps mismatch: {blendshapes1['exportFps']} vs {blendshapes2['exportFps']}"
        )
    if blendshapes1["numPoses"] != blendshapes2["numPoses"]:
        raise ValueError(
            f"numPoses mismatch: {blendshapes1['numPoses']} vs {blendshapes2['numPoses']}"
        )
    if blendshapes1["facsNames"] != blendshapes2["facsNames"]:
        raise ValueError("facsNames lists differ")
    if blendshapes1["joints"] != blendshapes2["joints"]:
        raise ValueError("joints lists differ")

    # Concatenate per-frame data
    merged_weightMat = blendshapes1["weightMat"] + blendshapes2["weightMat"]
    merged_rotations = blendshapes1["rotations"] + blendshapes2["rotations"]
    merged_translations = blendshapes1["translations"] + blendshapes2["translations"]

    merged = {
        "exportFps": blendshapes1["exportFps"],
        "trackPath": blendshapes1.get("trackPath") or blendshapes2.get("trackPath", ""),
        "numPoses": blendshapes1["numPoses"],
        "numFrames": len(merged_weightMat),
        "facsNames": blendshapes1["facsNames"],
        "weightMat": merged_weightMat,
        "joints": blendshapes1["joints"],
        "rotations": merged_rotations,
        "translations": merged_translations,
    }

    return merged


def merge_blendshape_list(list_of_blendshapes: list) -> dict:
    """
    Merge multiple facial-animation chunks by concatenating their frame data.
    """
    if not list_of_blendshapes:
        raise ValueError("No blendshapes to merge")
    merged = list_of_blendshapes[0]
    for i in range(1, len(list_of_blendshapes)):
        merged = merge_blendshapes(merged, list_of_blendshapes[i])
    return merged
