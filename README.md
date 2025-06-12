# Audio2Face Client & Streaming Service

A comprehensive Python package that provides both a **client library** and a **FastAPI streaming server** for NVIDIA Omniverse Audio2Face (A2F). Generate facial blendshapes from audio with support for emotions, real-time streaming, and robust production-ready features.

---

## 🚀 Overview

This repository contains two main components:

1. **`a2f_client`** - A Python client library for programmatic control of Audio2Face via HTTP API
2. **`app`** - A FastAPI streaming server that processes audio files and streams blendshape data in real-time chunks

**Key Use Cases:**
- Real-time facial animation for avatars and VR/AR applications
- Batch processing of audio files for animation pipelines
- ML research and experimentation with facial expressions
- Integration into larger media production workflows

---

## ⚙️ Visualization 

<img src=".github/assets/A2FServerClient.png" width="700px" alt="Visualization">

---

## ✨ Key Features

### Client Library (`a2f_client`)
- **Simple Python API** for Audio2Face automation
- **Emotion Control** with customizable intensity weights
- **Chunked Processing** for large audio files
- **Automatic USD Model Loading** with ARKit blendshapes
- **Robust Error Handling** and logging
- **Comprehensive Testing** with pytest suite

### Streaming Server (`app`)
- **Real-time Streaming** via FastAPI with JSON-line responses
- **Dynamic FPS Optimization** based on processing performance  
- **Parallel Processing** using multiple A2F client instances
- **Emotion Support** for expressive facial animation
- **Production Ready** with logging, health checks, and error handling
- **Multi-worker Support** with file lock management

---

## 📁 Repository Structure

```
.
├── a2f_client/                 # Python client library
│   ├── modules/                # Internal HTTP API wrappers
│   ├── assets/                 # Default USD facial models
│   ├── samples/                # Example audio files
│   ├── tests/                  # Client unit tests
│   └── ...
├── app/                        # FastAPI streaming server
│   ├── config.py               # Server configuration
│   ├── main.py                 # FastAPI application
│   ├── streaming_logic.py      # Core streaming logic
│   └── tests/                  # Server integration tests
├── pyproject.toml              # Poetry configuration
└── README.md
```

---

## 🛠 Installation

### Prerequisites

- **Python 3.10+**
- **NVIDIA Omniverse Audio2Face** (locally installed)
- **Poetry** (recommended) or pip

### Setup

```bash
# Clone the repository
git clone git@github.com:alexthillen/a2f-client.git
cd a2f-client

# Install with Poetry
poetry install
poetry shell

# Or with pip
pip install -e .
```

### Environment Configuration

Set your Audio2Face headless script path:

**Definitions:**
- *Headless Script*: Executable that launches Audio2Face in server mode without UI, required for API automation.

**Linux:**
```bash
export A2F_HEADLESS_SCRIPT="$HOME/.local/share/ov/pkg/audio2face-2023.2.0/audio2face_headless.sh"
```

**Windows:**
```cmd
set A2F_HEADLESS_SCRIPT=%USERPROFILE%\AppData\Local\ov\pkg\audio2face-2023.2.0\audio2face_headless.bat
```

---

## 🎯 Quick Start

### Python Client Usage

```python
from a2f_client import A2FClient

# Initialize client
client = A2FClient(port=8192)

# Process audio with emotions
client.set_audio("path/to/audio.wav")
client.set_emotions({"joy": 0.8, "sadness": 0.2})

# Generate blendshapes for specific time window
blendshapes = client.generate_blendshapes(
    start=0.5, 
    end=1.0, 
    fps=30
)

print(f"Generated {blendshapes['blendshapes']['numFrames']} frames")
```

### Streaming Server

**Start the server:**
```bash
python app/main.py
# Server starts at http://localhost:8000
```

**Process audio via HTTP:**
```python
import requests
import json

# Simple audio processing
with open("audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/process-audio/?fps=20",
        files={"audio_file": f},
        stream=True
    )
    
    for line in response.iter_lines():
        chunk_data = json.loads(line)
        print(f"Chunk {chunk_data['chunk_id']}: {chunk_data['result']['numFrames']} frames")
```

**With emotion control:**
```python
emotions = {"joy": 0.8, "amazement": 0.3, "anger": 0.1}

with open("audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/process-audio/",
        files={"audio_file": f},
        data={"emotions": json.dumps(emotions)},
        stream=True
    )
```

---

## ⚙️ Configuration

### Client Settings (`a2f_client/settings.py`)

| Variable                 | Default                                | Description                   |
| ------------------------ | -------------------------------------- | ----------------------------- |
| `A2F_HEADLESS_SCRIPT`    | Platform-specific path                 | Path to A2F headless launcher |
| `A2F_PORT`               | `8190`                                 | Port for A2F headless server  |
| `A2F_BASE_URL`           | `http://localhost`                     | Base URL for A2F API          |
| `A2F_DEFAULT_USD_MODEL`  | `assets/mark_arkit_solved_default.usd` | Default facial model          |
| `A2F_DEFAULT_OUTPUT_DIR` | `tmp/blendshapes`                      | Output directory for exports  |

### Server Settings (`app/config.py`)

| Variable                         | Default   | Description                |
| -------------------------------- | --------- | -------------------------- |
| `A2F_FASTAPI_HOST`               | `0.0.0.0` | Server host address        |
| `A2F_FASTAPI_PORT`               | `8000`    | Server port                |
| `A2F_FASTAPI_DEFAULT_WORKERS`    | `2`       | Number of worker processes |
| `A2F_FASTAPI_CLIENTS_PER_WORKER` | `2`       | A2F clients per worker     |
| `A2F_FASTAPI_TMP_DIR`            | `tmp`     | Temporary file directory   |

---

## 🧪 Testing

### Client Tests
```bash
# Run client unit tests
pytest a2f_client/tests/

# Test specific functionality
pytest a2f_client/tests/test_blendshapes.py::test_chunking_vs_full_export_equivalence
```

### Server Tests
```bash
# Start server first
python app/main.py &

# Run integration tests
pytest app/tests/

# Test streaming with emotions
pytest app/tests/test_generation.py::test_streaming_endpoint_with_emotions
```

### Test Coverage
- **Client**: Chunked vs full export probabilistic equivalence, emotion setting, audio loading
- **Server**: Streaming endpoints, dynamic FPS, emotion processing, error handling

---

## 🔧 Advanced Features

### Dynamic FPS Optimization

The streaming server automatically adjusts frame rate based on processing performance:

```python
# Algorithm used internally:
alpha = chunk_duration / processing_time
safe_fps = max(min_fps, floor(num_clients * current_fps * alpha - 7))
current_fps = min(max_fps, (current_fps + safe_fps) / 2)
```

This ensures optimal throughput while maintaining quality.

### Emotion System

**Supported Emotions:**
- `amazement`, `anger`, `cheekiness`, `disgust`
- `fear`, `grief`, `joy`, `outofbreath` 
- `pain`, `sadness`

**Usage:**
```python
# Client
client.set_emotions({"joy": 1.0, "sadness": 0.3})

# Server API
emotions = {"joy": 0.8, "anger": 0.2}
requests.post(url, data={"emotions": json.dumps(emotions)}, ...)
```

### Parallel Processing

The server uses multiple A2F client instances with file locking to prevent port conflicts:

```python
# Automatic port allocation with locking
streaming_manager = StreamingManager(clients_per_worker=2)
# Handles 8190, 8191, 8192, etc. automatically
```

---

## 📊 API Reference

### Client Methods

**Definitions:**
- **Blendshape**: Numerical weights representing facial muscle deformations for 3D animation
- **USD Model**: Universal Scene Description file containing 3D facial geometry and blendshape targets

| Method                   | Parameters                   | Returns | Description                          |
| ------------------------ | ---------------------------- | ------- | ------------------------------------ |
| `set_audio(path)`        | `path: str`                  | `None`  | Load audio file and initialize model |
| `set_emotions(emotions)` | `emotions: Dict[str, float]` | `None`  | Set emotion weights (0.0-1.0)        |
| `generate_blendshapes()` | `start, end, fps, use_a2e`   | `Dict`  | Export blendshapes for time range    |

### Server Endpoints

| Endpoint          | Method | Parameters                  | Description              |
| ----------------- | ------ | --------------------------- | ------------------------ |
| `/process-audio/` | `POST` | `audio_file, fps, emotions` | Stream blendshape chunks |
| `/`               | `GET`  | -                           | Health check             |
| `/health`         | `GET`  | -                           | Detailed system status   |

---

## 🐛 Troubleshooting

### Common Issues

1. **"Headless script not found"**
   - Set `A2F_HEADLESS_SCRIPT` environment variable to correct path
   - Verify Audio2Face installation

2. **Port conflicts**
   - Server uses ports 8190+ for A2F clients
   - Check for running A2F instances: `netstat -tlnp | grep 819`

3. **File lock errors**
   - Remove stale lock files: `rm .lock_*`
   - Ensure proper server shutdown

4. **Audio format issues**
   - Use WAV format for best compatibility
   - Check sample rate (44.1kHz recommended)

### Performance Optimization

**For High Throughput:**
```bash
export A2F_FASTAPI_DEFAULT_WORKERS=3
export A2F_FASTAPI_CLIENTS_PER_WORKER=3
# Uses 9 A2F client instances total
```

**For Low Latency:**
```python
streaming_manager.chunk_size = 0.1  # Smaller chunks
```

---

## 🔬 Important Terms & Theorems

**Definitions:**

- **Blendshape**: A vector of weights $∈ [1]^n$ representing facial expressions, where n is the number of facial control points
- **Chunking**: Temporal decomposition of audio into overlapping or non-overlapping segments for parallel processing
- **A2F Instance**: Individual Audio2Face headless server process bound to a specific port
- **Emotion Weight**: Continuous scalar $∈ [1]$ controlling the intensity of named emotional expressions

**Chunk Equivalence Definition:** Chunked blendshape generation is $(1\%, 0.1)$-chunk-equivalent to full export generation if less than $1\%$ of all blendshape weights disagree by more than an absolute value of $0.1$ or by more than $0.1 \times 10^{-6}$ relative error.

*Implementation verified in `test_chunking_vs_full_export_equivalence`*

---

## 📈 Summary Table

| Component         | Purpose           | Key Features                                   | Test Coverage                           |
| ----------------- | ----------------- | ---------------------------------------------- | --------------------------------------- |
| **a2f_client**    | Python API client | Audio loading, emotion control, chunked export | Unit tests, equivalence validation      |
| **app/streaming** | Real-time server  | FastAPI, parallel processing, dynamic FPS      | Integration tests, streaming validation |
| **assets/**       | 3D models         | USD facial models with ARKit blendshapes       | Used in all tests                       |
| **samples/**      | Test data         | Reference audio files                          | 100% test coverage                      |

---

**Fun Fact:** The dynamic FPS optimization can automatically adjust from 10 FPS to 30 FPS based on your hardware's processing capability! 🚀


