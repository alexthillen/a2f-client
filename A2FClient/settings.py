import os
import platform

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
if platform.system() == "Linux":
    A2F_HEADLESS_SCRIPT = os.getenv(
        "A2F_HEADLESS_SCRIPT",
        os.path.join(
            os.path.expanduser("~"),
            ".local/share/ov/pkg/audio2face-2023.2.0/audio2face_headless.sh",
        ),
    )
else:
    A2F_HEADLESS_SCRIPT = os.getenv(
        "A2F_HEADLESS_SCRIPT",
        os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Local",
            "ov",
            "pkg",
            "audio2face-2023.2.0",
            "audio2face_headless.bat",
        ),
    )
if not os.path.exists(A2F_HEADLESS_SCRIPT):
    raise FileNotFoundError(
        f"A2F headless script not found at {A2F_HEADLESS_SCRIPT}. "
        f"Please set the `A2F_HEADLESS_SCRIPT` environment variable to a valid path."
    )

A2F_PORT = os.getenv("A2F_PORT", "8011")
BASE_URL = os.getenv("A2F_BASE_URL", f"http://localhost")
DEFAULT_USD_MODEL = os.getenv(
    "A2F_DEFAULT_USD_MODEL",
    os.path.join(DIR_PATH, "assets", "mark_arkit_solved_default.usd"),
)
DEFAULT_OUTPUT_DIR = os.getenv(
    "A2F_DEFAULT_OUTPUT_DIR",
    os.path.join(DIR_PATH, "tmp", "blendshapes"),
)
