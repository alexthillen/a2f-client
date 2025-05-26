import math
import os
import json
from typing import Optional, Union

from loguru import logger

import A2FClient.settings as settings
from A2FClient.utils import load_audio
from A2FClient.modules._a2f_endpoints_client import _A2FEndpointsClient
import tempfile


class A2FClient(_A2FEndpointsClient):
    """A minimalistic wrapper around the Audio2Face HTTP API endpoints allowing to stream blendshapes."""

    def __init__(
        self,
        output_dir: str = settings.DEFAULT_OUTPUT_DIR,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.player: Optional[str] = None
        self.solver: Optional[str] = None
        self.duration: Optional[float] = None
        self.output_dir: Optional[str] = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def set_audio(
        self,
        audio_source: str,
    ) -> None:
        audio_path, duration = load_audio(audio_source)
        self.duration = duration
        needs_init = (
            self.root_path != os.path.dirname(audio_path)
            or self.audio_filename != os.path.basename(audio_path)
            or not self.solver
            or not self.player
        )
        if needs_init:
            self.player = self._get_player()
            self._set_root_path(self.player, os.path.dirname(audio_path))
            self._set_track(self.player, os.path.basename(audio_path))
            self.solver = self._get_solvers()

    def set_emotions(self, emotions: dict = None) -> None:
        """
        Set the emotions for the solver.

        Args:
            emotions (dict): A dictionary mapping emotion names to intensities.
        """
        if not self.solver:
            raise RuntimeError("Solver is not initialized. Did you call set_audio?")
        self._set_emotions(self.player, emotions or {})

    def generate_blendshapes(
        self,
        start: float = 0.0,
        end: float = -1.0,
        fps: int = 30,
        use_a2e: bool = False,
    ) -> dict:
        """
        Export blendshapes data for a specified time window as a dictionary.

        This method restricts the playback window of the server to the interval [start, end] seconds.
        It can optionally apply automatic emotion keying (via use_a2e) or a manual emotion override if an
        emotion dictionary is provided. Afterwards, it exports the blendshapes for that time window.

        Args:
            start (float): The starting time in seconds for the export segment.
            end (float): The ending time in seconds for the export segment; use -1.0 for the full duration.
            fps (int): Frame rate for sampling blendshapes.
            emotion (dict, optional): Mapping of emotion names to intensities for manual override.
            use_a2e (bool): If True, run automatic emotion key generation.

        Returns:
            dict: A dictionary containing the server's export response along with an additional key "blendshapes"
              holding the blendshapes data loaded from JSON.

        Raises:
            RuntimeError: If required initializations (e.g., setting the audio) have not been performed.
        """
        if not self.player or not self.solver or self.duration is None:
            raise RuntimeError("Audio is not correctly initialized. Did you call set_audio?")
        # restrict playback range
        self._set_range(self.player, start, end)

        if use_a2e:
            self._run_a2e(self.player)

        # set fps such that at least one frame is generated in the specified range
        fps = max(fps, math.ceil(1.0 / (end - start) + 1e-3))

        # export blendshapes
        with tempfile.NamedTemporaryFile(suffix=".json", dir=self.output_dir) as tmpfile:
            filename = os.path.basename(tmpfile.name).rstrip(".json")
            resp = self._export_blendshapes(
                solver=self.solver,
                out_dir=self.output_dir,
                filename=filename,
                fps=fps,
            )
            blendshapes_path = os.path.join(self.output_dir, filename + "_bsweight.json")
            with open(blendshapes_path, "r") as f:
                resp["blendshapes"] = json.load(f)
            try:
                os.remove(blendshapes_path)
            except OSError:
                logger.warning(f"Warning: Could not remove temporary file {blendshapes_path}.")
        return resp
