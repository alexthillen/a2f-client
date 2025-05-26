# A2FClient/modules/_A2FHttpClient.py
import os
import subprocess
import time
from A2FClient.utils import logger
import requests

from A2FClient import settings


class _A2FHttpClient:
    """
    Wrapper around Audio2Face HTTP API endpoints.
    """

    def __init__(
        self,
        base_url: str = settings.BASE_URL,
        port: int = settings.A2F_PORT,
    ):
        self.base_url = f"{base_url.rstrip('/')}:{port}"
        self.port = port

    def _handle(self, resp: requests.Response) -> dict:
        """
        Raise HTTP errors or return parsed JSON.
        """
        try:
            resp.raise_for_status()
            if resp.content:
                data = resp.json()
            else:
                data = {}
            logger.debug("→ {} {}", resp.url, data)
            return data
        except requests.ConnectionError as ce:
            text = resp.text.strip() if resp.text else "No response"
            logger.error("Connection error on {}: {}", resp.url, text)
            raise requests.ConnectionError(f"A2F API connection error: {text}") from ce
        except requests.HTTPError as e:
            text = resp.text.strip()
            logger.error("HTTP {} on {}: {}", resp.status_code, resp.url, text)
            try:
                err = resp.json()
            except ValueError:
                err = {"error": text}
                err["statusCode"] = resp.status_code
                raise RuntimeError(f"A2F API error: {err}") from e

    def _get(self, path: str) -> dict:
        return self._handle(requests.get(f"{self.base_url}{path}"))

    def _post(self, path: str, payload: dict) -> dict:
        return self._handle(requests.post(f"{self.base_url}{path}", json=payload))
