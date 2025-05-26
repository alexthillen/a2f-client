import json
import os
from A2FClient import A2FClient

# os.environ["A2F_HEADLESS_SCRIPT"] = os.path.join(
#     os.path.expanduser("~"), ".local/share/ov/pkg/audio2face-2023.2.0/audio2face_headless.sh")

# Initialize the client
client = A2FClient(port=8192)  # Use the same port as the server


# Path to your audio file
audio_file = "A2FClient/samples/sample-0.wav"  # "path/to/your/audio.wav"
# Set the audio for processing
client.set_audio(audio_file)
# Generate blendshapes
blendshapes = client.generate_blendshapes(start=0.0, end=0.1, fps=10)
print(json.dumps(blendshapes, indent=4))
