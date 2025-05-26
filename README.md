# A2F Client

A Python client and server system for NVIDIA Audio2Face (A2F) that streamlines facial animation generation from audio files.

## What It Does

This project provides a complete solution for generating facial animations by combining:

1. **Python Client**: A simplistic interface (`A2FClient`) that abstracts the complexity of NVIDIA's Audio2Face application
2. **Flask Server**: A scalable backend that manages multiple A2F instances and handles concurrent animation requests

## Key Features

- **Simple API**: Three main operations through `A2FClient`:
  - `set_audio()` - Load audio files for processing
  - `set_emotions()` - Configure emotional expressions
  - `generate_blendshapes()` - Export facial animation data

- **Scalable Architecture**: 
  - Configurable worker pool for handling concurrent requests
  - Multiple A2F headless instances per worker for parallel processing
  - Chunks audio into manageable segments (e.g., 0.3-second intervals)

- **Efficient Processing**: Each worker can utilize all available A2F clients assigned to it, enabling parallel chunk processing for faster animation generation

## Quick Start

### Running the Server

```bash
export A2F_HEADLESS_SCRIPT="$HOME/.local/share/ov/pkg/audio2face-2023.2.0/audio2face_headless.sh"
cd a2fwrapper
poetry install
source .venv/bin/activate
python app/main.py
```

### Using the Client

```bash
pip install a2f-client # Install the client package
```

```python
import json
import os
from A2FClient import A2FClient
# os.environ["A2F_HEADLESS_SCRIPT"] = os.path.join(
#     os.path.expanduser("~"), ".local/share/ov/pkg/audio2face-2023.2.0/audio2face_headless.sh")
client = A2FClient(port=8192)  # Use the same port as the server
# Path to your audio file
audio_file = "A2FClient/samples/sample-0.wav" # "path/to/your/audio.wav"
# Set the audio for processing
client.set_audio(audio_file)
# Generate blendshapes
blendshapes = client.generate_blendshapes(start=0.0, end=0.1, fps=10)
print(json.dumps(blendshapes, indent=4))
```

## Architecture Overview

The system uses a distributed approach where workers manage pools of A2F clients, allowing for efficient parallel processing of audio chunks while maintaining scalability for multiple concurrent animation requests.


## Acknowledgements

The samples are generated with [Elevenlabs](https://elevenlabs.io/) online platform.

---

**Summary**: This A2F Client simplifies NVIDIA Audio2Face integration by providing a clean Python API backed by a scalable Flask server that can handle multiple concurrent facial animation generation tasks through parallel processing of audio chunks.