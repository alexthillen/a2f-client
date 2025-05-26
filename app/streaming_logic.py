import asyncio
import json
import math
import msvcrt
import platform
import random
import time
from typing import Optional, Union

from loguru import logger

from A2FClient.a2f_client import A2FClient
from A2FClient.utils import load_audio
import os

from app.config import Config, EmotionWeights

if platform.system() == "Windows":
    import msvcrt
else:
    import fcntl


class StreamingManager:
    def __init__(self, clients_per_worker: int = 2):
        self.available_ports = [
            i for i in range(8190, 8190 + Config.DEFAULT_WORKERS * clients_per_worker)
        ]
        self.locked_files = {}
        self.a2f_clients = [
            A2FClient(port=str(self._next_port())) for _ in range(clients_per_worker)
        ]
        self.client_locks = [asyncio.Lock() for _ in self.a2f_clients]
        self.chunk_size = 0.3
        self.current_fps = 30
        self.default_fps = 10
        self.max_fps = 30
        self.min_fps = 10

    def _acquire_lock(self, number):
        lock_file_path = f".lock_{number}"
        lock_file = None
        try:
            lock_file = open(lock_file_path, "w")
            if platform.system() == "Windows":
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            print(f"Process {os.getpid()} acquired lock on {lock_file_path}")
            self.locked_files[number] = lock_file
            return True
        except (BlockingIOError, OSError):
            if lock_file:
                lock_file.close()
            return False
        except FileNotFoundError:
            try:
                lock_file = open(lock_file_path, "w")
                if platform.system() == "Windows":
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                print(f"Process {os.getpid()} created and acquired lock on {lock_file_path}")
                self.locked_files[number] = lock_file
                return True
            except (BlockingIOError, OSError):
                if lock_file:
                    lock_file.close()
                return False
        return False

    def _release_lock(self, number):
        lock_file_path = f".lock_{number}"
        if number in self.locked_files:
            lock_file = self.locked_files[number]
            try:
                if platform.system() == "Windows":
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            except OSError as e:
                print(f"Error unlocking file {lock_file_path}: {e}")
            finally:
                lock_file.close()
                del self.locked_files[number]
                print(f"Process {os.getpid()} released lock on {lock_file_path}")
        else:
            print(f"No lock found for {lock_file_path}")

    def _next_port(self):
        for _ in range(10):
            for port in self.available_ports:
                time.sleep(random.uniform(0.1, 0.5))
                if self._acquire_lock(port):
                    return port
        raise RuntimeError(f"Process {os.getpid()} : No available ports found after 10 attempts.")

    def __del__(self):
        print(f"Releasing all locks for process {os.getpid()}")
        for port in list(self.locked_files.keys()):
            self._release_lock(port)
        for lock in self.client_locks:
            lock.release()
        print(f"All locks released for process {os.getpid()}")

    async def generate_blendshapes_coroutine(self, client_idx, start, end, use_a2e) -> dict:
        """Offload blocking `.generate_blendshapes` call to asyncio's default ThreadPoolExecutor."""
        async with self.client_locks[client_idx]:
            print(f"→ scheduling blocking export on client {client_idx}, {start:.1f}-{end:.1f}s")
            client: A2FClient = self.a2f_clients[client_idx]
            loop = asyncio.get_running_loop()
            start_time = time.time()
            result = await loop.run_in_executor(
                None,
                func=lambda: client.generate_blendshapes(start, end, self.current_fps, use_a2e)[
                    "blendshapes"
                ],
            )
            end_time = time.time()
            elapsed_time = end_time - start_time
            alpha = (end - start) / elapsed_time
            safe_fps = max(
                self.min_fps, math.floor(len(self.a2f_clients) * self.current_fps * alpha - 7)
            )
            self.current_fps = min(self.max_fps, (self.current_fps + safe_fps) // 2)
            logger.info(
                f"Adjusted FPS to {self.current_fps} as generation took {elapsed_time:.2f}s."
            )

            return result

    async def submit_job(
        self,
        audio_source: str,
        fps: Optional[int] = None,
        emotions: Optional[EmotionWeights] = None,
        use_a2e: bool = False,
    ):
        if fps is None:
            fps = self.default_fps
        self.current_fps = fps
        audio_path, duration = load_audio(audio_source)
        for client in self.a2f_clients:
            client.set_audio(audio_path)
            if emotions:
                client.set_emotions(dict(emotions))

        nr_splits = math.ceil(duration / self.chunk_size - 0.5)
        # Fire off ALL tasks immediately
        tasks = []

        chunks = [
            (i * self.chunk_size, min((i + 1) * self.chunk_size, duration))
            for i in range(nr_splits)
        ]
        for i, (start, end) in enumerate(chunks):
            client_idx = i % len(self.a2f_clients)
            task = asyncio.create_task(
                self.generate_blendshapes_coroutine(client_idx, start, end, use_a2e)
            )
            print(f"Created task #{i} on client {i % len(self.a2f_clients)}")
            tasks.append(task)

        # Await tasks one-by-one in order!
        for idx, task in enumerate(tasks):
            result = await task
            print(f"Process {os.getpid()} :Chunk #{idx} done")
            json_str = json.dumps({"chunk_id": idx, "result": result}).encode("utf-8") + b"\n"
            yield json_str
