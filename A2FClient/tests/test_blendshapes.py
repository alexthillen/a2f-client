import pytest
import os
import sys
import math
from A2FClient.a2f_client import A2FClient
from A2FClient import settings
from A2FClient.utils import merge_blendshape_list, load_audio


TEST_AUDIO_FILE = os.path.join(settings.DIR_PATH, "samples", "sample-0.wav")


def assert_blendshapes_data_almost_equal(bs1, bs2, places=1):
    """
    Asserts that two blendshape data dictionaries (the inner "blendshapes" part)
    are almost equal using pytest.approx for numerical comparisons.
    Allows up to 1% of the entries to fail the approx check.
    """
    # Metadata keys
    assert bs1.get("exportFps") == bs2.get("exportFps"), "exportFps mismatch"
    assert bs1.get("numPoses") == bs2.get("numPoses"), "numPoses mismatch"
    assert bs1.get("facsNames") == bs2.get("facsNames"), "facsNames mismatch"
    assert bs1.get("joints") == bs2.get("joints"), "joints mismatch"
    assert bs1.get("numFrames") == bs2.get(
        "numFrames"
    ), f"numFrames mismatch. bs1: {bs1.get('numFrames')}, bs2: {bs2.get('numFrames')}"

    num_frames = bs1.get("numFrames", 0)
    if num_frames == 0:
        for key in ["weightMat", "rotations", "translations"]:
            assert bs1.get(key, []) == bs2.get(key, []), f"{key} mismatch for zero frames"
        return

    # Frame data checks - ensure keys exist and have correct length
    for key in ["weightMat", "rotations", "translations"]:
        assert key in bs1, f"bs1 missing '{key}'"
        assert key in bs2, f"bs2 missing '{key}'"
        assert (
            len(bs1[key]) == num_frames
        ), f"Length of bs1['{key}'] ({len(bs1[key])}) does not match numFrames ({num_frames})"
        assert (
            len(bs2[key]) == num_frames
        ), f"Length of bs2['{key}'] ({len(bs2[key])}) does not match numFrames ({num_frames})"

    # Detailed frame-by-frame comparison
    num_poses = bs1.get("numPoses", 0)
    num_joints = len(bs1.get("joints", []))

    total_entries = 0
    failed_entries = 0

    for i in range(num_frames):
        # weightMat: List[List[float]] (frames x poses)
        if num_poses > 0:
            assert len(bs1["weightMat"][i]) == num_poses
            assert len(bs2["weightMat"][i]) == num_poses
            for j in range(num_poses):
                total_entries += 1
                try:
                    assert bs1["weightMat"][i][j] == pytest.approx(
                        bs2["weightMat"][i][j], rel=1e-9, abs=10 ** (-places)
                    )
                except AssertionError:
                    failed_entries += 1
        else:
            assert (
                bs1.get("weightMat", [[]])[i] == []
            )  # Should be empty list for the frame if num_poses is 0
            assert bs2.get("weightMat", [[]])[i] == []

        # rotations & translations: List[List[List[float]]] (Frames[Joints[Values]])
        for key in ["rotations", "translations"]:
            if num_joints > 0:
                assert (
                    len(bs1[key][i]) == num_joints
                ), f"{key} joint count mismatch for bs1 at frame {i}"
                assert (
                    len(bs2[key][i]) == num_joints
                ), f"{key} joint count mismatch for bs2 at frame {i}"
                for j in range(num_joints):
                    total_entries += 1
                    try:
                        assert bs1[key][i][j] == pytest.approx(
                            bs2[key][i][j], rel=1e-9, abs=10 ** (-places)
                        )
                    except AssertionError:
                        failed_entries += 1
            else:  # No joints, so the list of joint data for this frame should be empty
                assert (
                    bs1.get(key, [[]])[i] == []
                ), f"bs1 {key} for frame {i} should be empty as no joints"
                assert (
                    bs2.get(key, [[]])[i] == []
                ), f"bs2 {key} for frame {i} should be empty as no joints"

    # Allow up to 1% of entries to fail
    allowed_failures = total_entries * 0.01
    assert (
        failed_entries <= allowed_failures
    ), f"Too many mismatches: {failed_entries} out of {total_entries} entries failed (allowed 1%)"


# --- Pytest Fixtures ---
@pytest.fixture(scope="session", autouse=True)
def check_test_files_exist():
    """
    Session-scoped fixture to check for essential files once.
    Autouse ensures it runs before any test session.
    """
    if not os.path.exists(TEST_AUDIO_FILE):
        pytest.exit(f"Test audio file not found: {TEST_AUDIO_FILE}. Please ensure it exists.")

    expected_usd_path = settings.DEFAULT_USD_MODEL
    if not os.path.isabs(settings.DEFAULT_USD_MODEL):
        expected_usd_path = os.path.join(
            settings.DIR_PATH, "assets", os.path.basename(settings.DEFAULT_USD_MODEL)
        )
    if not os.path.exists(settings.DEFAULT_USD_MODEL):
        pytest.exit(
            f"Default USD model not found. Checked: {settings.DEFAULT_USD_MODEL}. Expected at (based on settings): {expected_usd_path}. Check A2F/settings.py."
        )


@pytest.fixture
def a2f_client():
    """
    Provides an A2FClient instance for tests, managing settings.CLEANUP.
    """
    try:
        port = int(settings.A2F_PORT)
    except ValueError:
        pytest.fail(f"A2F_PORT ('{settings.A2F_PORT}') is not a valid integer or not set.")
    client = A2FClient(port=port)
    yield client


# --- Test Function ---
def test_chunking_vs_full_export_equivalence(a2f_client: A2FClient):
    """
    Tests that exporting blendshapes in chunks and merging them is equivalent
    to exporting the entire audio's blendshapes at once.
    """
    audio_path = TEST_AUDIO_FILE
    fps = 15

    audio_path, audio_duration = load_audio(audio_path)
    print(f"Audio duration for {os.path.basename(audio_path)}: {audio_duration:.2f}s")

    if audio_duration == 0:
        pytest.skip("Audio duration is zero, skipping equivalence test.")

    # Full Export
    print("Starting full export scenario...")
    a2f_client.set_audio(audio_path)
    full_export = a2f_client.generate_blendshapes(fps=fps)
    assert isinstance(full_export, dict), "Full export should return a dictionary."
    assert "blendshapes" in full_export, "Full export envelope JSON is missing 'blendshapes' key."
    full_blendshapes = full_export["blendshapes"]
    print(f"Full export completed. Number of frames: {full_blendshapes.get('numFrames')}")

    # Chunked Export
    print("Starting chunked export scenario...")
    a2f_client = A2FClient(port=int(settings.A2F_PORT))
    a2f_client.set_audio(audio_path)
    chunk_size = 3.0
    chunks = []
    for i in range(math.ceil(audio_duration / chunk_size)):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, audio_duration)
        print(f"Exporting chunk {i}: {start:.2f}s to {end:.2f}s")
        chunk = a2f_client.generate_blendshapes(start, end, fps=fps)
        assert "blendshapes" in chunk, f"Chunk {i} export is missing 'blendshapes' key."
        chunks.append(chunk["blendshapes"])
    merged_blendshapes = merge_blendshape_list(chunks)

    # Check probabilistic equivalence
    assert_blendshapes_data_almost_equal(full_blendshapes, merged_blendshapes, 1)
    print("Equivalence test passed.")


def test_emotion_setting(a2f_client: A2FClient):
    """
    Tests the emotion setting functionality of the A2FClient.
    """
    audio_path = TEST_AUDIO_FILE
    fps = 5

    audio_path, audio_duration = load_audio(audio_path)
    print(f"Audio duration for {os.path.basename(audio_path)}: {audio_duration:.2f}s")

    if audio_duration == 0:
        pytest.skip("Audio duration is zero, skipping emotion setting test.")

    # Set audio and emotion
    a2f_client.set_audio(audio_path)
    emotions = {"sadness": 1.0}
    a2f_client.set_emotions(emotions)
    blendshapes = a2f_client.generate_blendshapes(fps=fps)

    assert isinstance(blendshapes, dict), "Emotion export should return a dictionary."
    assert (
        "blendshapes" in blendshapes
    ), "Emotion export envelope JSON is missing 'blendshapes' key."
    print("Emotion setting test passed.")


if __name__ == "__main__":
    pytest.main([__file__])
