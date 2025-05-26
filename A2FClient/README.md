## A2FClient

A minimal Python client for NVIDIA Audio2Face’s headless HTTP API.  
Load a USD face model, stream a WAV file, export per-frame blendshape weights.

---

## Requirements

-  Linux  
-  Python 3.10+  
-  NVIDIA Audio2Face headless script  
- see `pyproject.toml` for python dependencies

---

## Install

```bash
git clone ...
poetry install
source .venv/bin/activate
cd A2FClient
```

Set (or export) your headless script in `A2F_HEADLESS_SCRIPT`. ("path/to/audio2face_headless.sh")

---

## Quickstart

```python
from A2FClient import A2FClient

# os.environ["A2F_HEADLESS_SCRIPT"]="path/to/audio2face_headless.sh"
client = A2FClient(port="8192")  

client.set_audio("samples/sample-0.wav")
resp = client.generate_blendshapes(start=0, end=0.1, fps=10) # one frame
print(resp["blendshapes"])
```

---

## API

-  `set_audio(path: str) → None`  
-  `set_emotions(emotions: dict) → None`  
     - Example: `{"joy": 0.5, "sadness": 0.2, "anger": 0.1}`
-  `generate_blendshapes(start: float, end: float, fps: int, use_a2e: bool=False) → dict`  
