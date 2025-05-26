# A2F/modules/_A2FEndpointsClient.py

import os
import platform
import subprocess
import time

import requests
from A2FClient import settings
from A2FClient.utils import logger
from A2FClient.modules._a2f_http_client import _A2FHttpClient


class _A2FEndpointsClient(_A2FHttpClient):
    def __init__(
        self,
        usd_model: str = settings.DEFAULT_USD_MODEL,
        headless_script: str = settings.A2F_HEADLESS_SCRIPT,
        *args,
        **kwargs,
    ):
        self.root_path = None
        self.audio_filename = None
        self.usd_loaded = False
        self.usd_model = os.path.abspath(usd_model)
        self.headless_script = headless_script
        super().__init__(*args, **kwargs)
        self._start_headless()
        self._load_usd()

    def _start_headless(self, wait_secs: float = 15.0) -> None:
        """
        Ensure an Audio2Face headless server is running on the configured port.

        Attempts to reach the `/status` endpoint. If unreachable, launches the
        headless script in a new session and sleeps for `wait_secs` to allow
        initialization.

        Args:
            wait_secs (float): Seconds to wait after launching the headless script. Defaults to 15.0.

        Raises:
            FileNotFoundError: If the configured headless script cannot be found on disk.
        """
        try:
            self._get("/status")
            logger.info(f"Audio2Face headless server is already running at {self.base_url}")
        except requests.RequestException:
            if not os.path.exists(self.headless_script):
                raise FileNotFoundError(f"Headless script not found: {self.headless_script}")
            # Cross-platform subprocess execution
            cmd = [
                self.headless_script,
                f"--/exts/omni.services.transport.server.http/port={self.port}",
            ]
            is_windows = platform.system() == "Windows"
            if not is_windows:
                cmd = ["bash"] + cmd

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if is_windows else 0,
                start_new_session=not is_windows,
            )
            logger.info("Started Audio2Face headless (pid={})", proc.pid)
            time.sleep(wait_secs)

    def _load_usd(self) -> dict:
        """Loads a USD model into the Audio2Face application.

        Returns:
            dict: A dictionary containing the response from the server.
        """
        res = self._post("/A2F/USD/Load", {"file_name": self.usd_model})
        self.usd_loaded = True
        return res

    def _get_player(self) -> str:
        """Retrieves the name of the A2F player instance.

        Returns:
            str: The name of the A2F player instance.

        Raises:
            RuntimeError: If no regular A2F player is found.
        """
        res = self._get("/A2F/Player/GetInstances")
        players = res.get("result", {}).get("regular", [])
        if not players:
            raise RuntimeError("No regular A2F player found.", f"{res}")
        return players[0]

    def _set_track(self, player: str, audio_filename: str) -> dict:
        """Sets the audio track for the given A2F player.

        Args:
            player (str): The name of the A2F player instance.
            audio_filename (str): The filename of the audio file (located in track root path).

        Returns:
            dict: A dictionary containing the response from the server.
        """
        self.audio_filename = audio_filename
        res = self._post(
            "/A2F/Player/SetTrack",
            {"a2f_player": player, "file_name": audio_filename, "time_range": [0, -1]},
        )
        tracks = self._get_tracks()
        if audio_filename not in tracks["result"]:
            raise RuntimeError("Audio track not found in player.", f"{tracks}")
        return res

    def _get_tracks(self) -> dict:
        """Retrieves the list of available audio tracks.

        Returns:
            dict: A dictionary containing the response from the server.
        """
        return self._post("/A2F/Player/GetTracks", {"a2f_player": self._get_player()})

    def _set_root_path(self, player: str, root_path: str) -> dict:
        """Sets the root folder for the player's audio files.

        Args:
            player (str): The name of the A2F player instance.
            root_path (str): The path to the root directory containing audio files.

        Returns:
            dict: A dictionary containing the response from the server.
        """
        self.root_path = os.path.abspath(root_path)
        payload = {"a2f_player": player, "dir_path": self.root_path}
        return self._post("/A2F/Player/SetRootPath", payload)

    def _play(self, player: str) -> dict:
        """Starts playing the audio track for the given A2F player.

        Args:
            player (str): The name of the A2F player instance.

        Returns:
            dict: A dictionary containing the response from the server.
        """
        return self._post("/A2F/Player/Play", {"a2f_player": player})

    def _get_solvers(self) -> str:
        """Retrieves the name of the blendshape solver node. The blendshape solver is the component
        that calculates the weights for each blendshape based on the audio input.

        Returns:
            str: The name of the blendshape solver node.

        Raises:
            RuntimeError: If no blendshape solver is found.
        """
        res = self._get("/A2F/Exporter/GetBlendShapeSolvers")
        sol = res.get("result", [])
        if not sol:
            raise RuntimeError("No blendshape solver found")
        return sol[0]

    def _export_blendshapes(
        self, solver: str, out_dir: str, filename: str = "blendshapes.json", fps: int = 30
    ) -> dict:
        """Exports blendshapes from the given solver node to a JSON file.

        Args:
            solver (str): The name of the blendshape solver node.
            out_dir (str): The directory to export the blendshapes to.
            filename (str, optional): The name of the output file. Defaults to "blendshapes.json".
            fps (int, optional): The frames per second for the exported blendshapes. Defaults to 30.

        Returns:
            dict: A dictionary containing the response from the server.
        """
        payload = {
            "solver_node": solver,
            "export_directory": os.path.abspath(out_dir),
            "file_name": filename,
            "fps": fps,
            "format": "json",
        }
        res = self._post("/A2F/Exporter/ExportBlendshapes", payload)
        # res["blendshapes"] = json.load(open(os.path.join(out_dir, filename + "_bsweight.json"), "r"))
        return res

    def _run_a2e(self, a2f_instance: str):
        """Trigger automatic emotion-key generation on current frame range.

        Args:
            a2f_instance (str): The name of the A2F instance.

        Returns:
            dict: A dictionary containing the response from the server.
        """
        return self._post("/A2F/A2E/GenerateKeys", {"a2f_instance": a2f_instance})

    def _set_emotions(self, a2f_instance: str, emotions: dict):
        """Override emotions by name on current frame range.

        Args:
            a2f_instance (str): The name of the A2F instance.
            emotions (dict): A dictionary of emotions to override, where keys are emotion names and values are the intensity.
                emotions:["amazement","anger","disgust","fear","grief","joy","pain","sadness",...]

        Returns:
            dict: A dictionary containing the response from the server.
        """
        emotions = {
            "amazement": 0.0,
            "anger": 0.0,
            "cheekiness": 0.0,
            "disgust": 0.0,
            "fear": 0.0,
            "grief": 0.0,
            "joy": 0.0,
            "outofbreath": 0.0,
            "pain": 0.0,
            "sadness": 0.0,
            **emotions,
        }

        return self._post(
            "/A2F/A2E/SetEmotionByName", {"a2f_instance": a2f_instance, "emotions": emotions}
        )

    def _set_range(self, player: str, start: float = 0.0, end: float = -1.0):
        """Limit playback to a sub-range [start,end] in seconds.

        Args:
            player (str): The name of the A2F player instance.
            start (float, optional): The start time of the playback range in seconds. Defaults to 0.0.
            end (float, optional): The end time of the playback range in seconds. Defaults to -1.0 (full track).

        Returns:
            dict: A dictionary containing the response from the server.
        """
        return self._post(
            "/A2F/Player/SetRange", {"a2f_player": player, "start": start, "end": end}
        )
