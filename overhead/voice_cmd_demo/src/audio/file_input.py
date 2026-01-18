import numpy as np
import wave
from pathlib import Path
from typing import Iterator, Optional
from scipy.io import wavfile
from ..utils.logging import get_logger

logger = get_logger("file_input")

class AudioFileInput:
    """Reads audio from WAV/MP3 files and provides chunks like real-time capture."""

    def __init__(self,
                 file_path: str,
                 chunk_size: int = 1024,
                 target_sample_rate: int = 16000):
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self.target_sample_rate = target_sample_rate

        if not self.file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        self._audio_data: Optional[np.ndarray] = None
        self._sample_rate: int = 0
        self._current_pos: int = 0

        self._load_file()
        logger.info(f"AudioFileInput initialized: {file_path}, {self._sample_rate}Hz, {len(self._audio_data)} samples")

    def _load_file(self) -> None:
        """Load audio file and resample if needed."""
        file_ext = self.file_path.suffix.lower()

        if file_ext == '.wav':
            self._load_wav()
        else:
            raise ValueError(f"Unsupported file format: {file_ext}. Only WAV supported.")

        # Resample if needed
        if self._sample_rate != self.target_sample_rate:
            self._resample_audio()

    def _load_wav(self) -> None:
        """Load WAV file using scipy."""
        try:
            self._sample_rate, audio_data = wavfile.read(str(self.file_path))

            # Convert to float32 for processing
            if audio_data.dtype != np.float32:
                if audio_data.dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                elif audio_data.dtype == np.int32:
                    audio_data = audio_data.astype(np.float32) / 2147483648.0
                else:
                    audio_data = audio_data.astype(np.float32)

            # Ensure mono
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)

            self._audio_data = audio_data

        except Exception as e:
            logger.error(f"Failed to load WAV file: {e}")
            raise

    def _resample_audio(self) -> None:
        """Resample audio to target sample rate."""
        if self._audio_data is None:
            return

        try:
            from scipy import signal

            # Calculate resampling ratio
            ratio = self.target_sample_rate / self._sample_rate

            # Resample
            new_length = int(len(self._audio_data) * ratio)
            self._audio_data = signal.resample(self._audio_data, new_length)
            self._sample_rate = self.target_sample_rate

            logger.info(f"Resampled audio to {self.target_sample_rate}Hz")

        except ImportError:
            logger.warning("scipy not available for resampling, using original sample rate")
        except Exception as e:
            logger.error(f"Failed to resample audio: {e}")

    def get_chunks(self) -> Iterator[np.ndarray]:
        """Generator that yields audio chunks.

        Yields:
            Audio chunks as numpy arrays (float32)
        """
        if self._audio_data is None:
            return

        self._current_pos = 0

        while self._current_pos < len(self._audio_data):
            end_pos = min(self._current_pos + self.chunk_size, len(self._audio_data))
            chunk = self._audio_data[self._current_pos:end_pos]

            # Convert back to int16 for compatibility with VAD
            chunk_int16 = (chunk * 32767).astype(np.int16)

            yield chunk_int16
            self._current_pos = end_pos

    def get_duration_seconds(self) -> float:
        """Get total duration of audio in seconds."""
        if self._audio_data is None or self._sample_rate == 0:
            return 0.0
        return len(self._audio_data) / self._sample_rate

    def seek_to_start(self) -> None:
        """Reset position to start of file."""
        self._current_pos = 0

    @property
    def sample_rate(self) -> int:
        """Get sample rate."""
        return self._sample_rate

    @property
    def total_samples(self) -> int:
        """Get total number of samples."""
        return len(self._audio_data) if self._audio_data is not None else 0