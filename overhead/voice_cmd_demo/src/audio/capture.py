import queue
import threading
import numpy as np
import sounddevice as sd
from typing import Optional, Callable
from ..utils.logging import get_logger
from ..utils.time import get_unix_timestamp

logger = get_logger("audio_capture")

class AudioCapture:
    """Captures audio from microphone in real-time."""

    def __init__(self,
                 sample_rate: int = 16000,
                 channels: int = 1,
                 block_size: int = 1024,
                 dtype: str = 'int16'):
        self.sample_rate = sample_rate
        self.channels = channels
        self.block_size = block_size
        self.dtype = dtype

        self._stream: Optional[sd.InputStream] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._audio_queue = queue.Queue()

        # Check if we need to resample
        self._needs_resample = sample_rate != 16000

        logger.info(f"AudioCapture initialized: {sample_rate}Hz, {channels}ch, {dtype}")

    def start(self, callback: Optional[Callable[[np.ndarray], None]] = None) -> None:
        """Start audio capture.

        Args:
            callback: Optional callback function for audio chunks
        """
        if self._running:
            logger.warning("Audio capture already running")
            return

        self._running = True

        def audio_callback(indata, frames, time_info, status):
            """Callback for audio stream."""
            if status:
                logger.warning(f"Audio stream status: {status}")

            # Convert to the expected format
            audio_data = indata.copy()

            # Put in queue for processing
            try:
                self._audio_queue.put(audio_data, timeout=0.1)
            except queue.Full:
                logger.warning("Audio queue full, dropping frame")

            # Call user callback if provided
            if callback:
                try:
                    callback(audio_data)
                except Exception as e:
                    logger.error(f"Audio callback failed: {e}")

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                blocksize=self.block_size,
                callback=audio_callback
            )
            self._stream.start()
            logger.info("Audio capture started")

        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            self._running = False
            raise

    def stop(self) -> None:
        """Stop audio capture."""
        if not self._running:
            return

        self._running = False

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
                logger.info("Audio capture stopped")
            except Exception as e:
                logger.error(f"Error stopping audio capture: {e}")

        # Clear queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break

    def get_audio_chunk(self, timeout: float = 0.1) -> Optional[np.ndarray]:
        """Get next audio chunk from queue.

        Args:
            timeout: Timeout in seconds

        Returns:
            Audio chunk as numpy array, or None if timeout
        """
        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def is_running(self) -> bool:
        """Check if audio capture is running."""
        return self._running

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._audio_queue.qsize()

    @staticmethod
    def list_devices() -> None:
        """List available audio devices."""
        print("Available audio devices:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            print(f"{i}: {device['name']} (in: {device['max_input_channels']}, out: {device['max_output_channels']})")

    @staticmethod
    def get_default_input_device() -> Optional[int]:
        """Get default input device index."""
        try:
            return sd.default.device[0]
        except Exception:
            return None