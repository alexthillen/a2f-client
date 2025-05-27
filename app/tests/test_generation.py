import json
import os
from pathlib import Path

import pytest
import requests


def handle_stream_sync(response):
    """
    Synchronously handles a streaming response where each line is a JSON object.
    Parses the outer dictionary.

    Args:
        response: A requests.Response object with streaming enabled.
    """
    for line in response.iter_lines(decode_unicode=True):
        if line:  # Ensure the line is not empty
            try:
                outer_dict = json.loads(line)
                yield outer_dict
            except json.JSONDecodeError as e:
                print(f"Error decoding outer JSON: {e}, raw line: {line}")
                continue


def test_streaming_endpoint():
    url = "http://127.0.0.1:8000/process-audio/?fps=20"
    # Assuming 'samples' directory is at the same level as the test file
    file_path = os.path.join(os.path.dirname(__file__), "sample-0.wav")

    assert os.path.isfile(file_path), f"Sample audio file not found at: {file_path}"

    try:
        with open(file_path, "rb") as f:
            response = requests.post(url, files={"audio_file": f}, stream=True, timeout=90.0)
            response.raise_for_status()  # Raise an exception for bad status codes

            first_response_received = False
            for parsed_data in handle_stream_sync(response):
                assert isinstance(
                    parsed_data, dict
                ), "Expected each streamed item to be a dictionary"
                # You can add more specific assertions about the content of the dictionaries if needed
                if not first_response_received:
                    first_response_received = True
                    first_parsed_data = parsed_data  # Optionally store the first response
                print("Parsed Data:", parsed_data)  # Keep the print for visibility during testing

            assert first_response_received, "No data was received from the streaming endpoint"

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request error: {e}")
    finally:
        if "response" in locals() and response:
            response.close()


def test_streaming_endpoint_dynamic_fps():
    url = "http://127.0.0.1:8000/process-audio/"
    # Assuming 'samples' directory is at the same level as the test file
    file_path = os.path.join(os.path.dirname(__file__), "sample-0.wav")

    assert os.path.isfile(file_path), f"Sample audio file not found at: {file_path}"

    try:
        with open(file_path, "rb") as f:
            response = requests.post(url, files={"audio_file": f}, stream=True, timeout=90.0)
            response.raise_for_status()  # Raise an exception for bad status codes

            first_response_received = False
            for parsed_data in handle_stream_sync(response):
                assert isinstance(
                    parsed_data, dict
                ), "Expected each streamed item to be a dictionary"
                # You can add more specific assertions about the content of the dictionaries if needed
                if not first_response_received:
                    first_response_received = True
                    first_parsed_data = parsed_data  # Optionally store the first response
                print("Parsed Data:", parsed_data)  # Keep the print for visibility during testing

            assert first_response_received, "No data was received from the streaming endpoint"

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request error: {e}")
    finally:
        if "response" in locals() and response:
            response.close()


def test_streaming_endpoint_with_emotions():
    url = "http://127.0.0.1:8000/process-audio/"
    # Assuming 'samples' directory is at the same level as the test file
    file_path = os.path.join(os.path.dirname(__file__), "sample-0.wav")

    assert os.path.isfile(file_path), f"Sample audio file not found at: {file_path}"

    # Define emotion weights to test
    emotions_data = {"joy": 0.8, "amazement": 0.3, "anger": 0.1, "sadness": 0.2, "fear": 0.0}
    emotions_json = json.dumps(emotions_data)

    try:
        with open(file_path, "rb") as f:
            # Prepare form data with emotions
            data = {"emotions": emotions_json}
            files = {"audio_file": f}

            response = requests.post(url, files=files, data=data, stream=True, timeout=90.0)
            response.raise_for_status()  # Raise an exception for bad status codes

            first_response_received = False
            for parsed_data in handle_stream_sync(response):
                assert isinstance(
                    parsed_data, dict
                ), "Expected each streamed item to be a dictionary"

                # Additional assertion to verify emotions are being processed
                # (This depends on your streaming response format)
                if not first_response_received:
                    first_response_received = True
                    first_parsed_data = parsed_data  # Optionally store the first response

                print("Parsed Data:", parsed_data)  # Keep the print for visibility during testing

            assert first_response_received, "No data was received from the streaming endpoint"

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request error: {e}")
    finally:
        if "response" in locals() and response:
            response.close()


# To run this test, save it as a Python file (e.g., test_audio_stream.py)
# and run pytest from your terminal in the same directory or a parent directory.
