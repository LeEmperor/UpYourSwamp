import webrtcvad
import numpy as np
import threading
import queue
from typing import Optional, List, Tuple
from ..utils.logging import get_logger
from ..utils.time import get_unix_timestamp, format_duration_ms

logger = get_logger("vad_segmenter")

class VADSegmenter:
    """Voice Activity Detection segmenter using WebRTC VAD."""

    def __init__(self,
                 sample_rate: int = 16000,
                 vad_mode: int = 3,  # 0-3, higher = more aggressive
                 silence_threshold_ms: int = 900,
                 min_segment_ms: int = 300,
                 max_utterance_s: int = 10):
        """
        Initialize VAD segmenter.

        Args:
            sample_rate: Audio sample rate (must be 8000, 16000, 32000, or 48000)
            vad_mode: VAD aggressiveness (0=least, 3=most aggressive)
            silence_threshold_ms: Silence duration to end utterance
            min_segment_ms: Minimum segment length to keep
            max_utterance_s: Maximum utterance length before forcing end
        """
        if sample_rate not in [8000, 16000, 32000, 48000]:
            raise ValueError(f"Sample rate {sample_rate} not supported by WebRTC VAD")

        self.sample_rate = sample_rate
        self.vad_mode = vad_mode
        self.silence_threshold_ms = silence_threshold_ms
        self.min_segment_ms = min_segment_ms
        self.max_utterance_s = max_utterance_s

        # VAD expects 10, 20, or 30ms frames
        self.frame_duration_ms = 30  # 30ms frames
        self.frame_samples = int(sample_rate * self.frame_duration_ms / 1000)

        self.vad = webrtcvad.Vad(vad_mode)

        # State
        self._current_segment: List[np.ndarray] = []
        self._silence_frames = 0
        self._segment_start_time: Optional[float] = None
        self._last_speech_time: Optional[float] = None

        # Calculate thresholds in frames
        self.silence_threshold_frames = int(silence_threshold_ms / self.frame_duration_ms)
        self.max_utterance_frames = int(max_utterance_s * 1000 / self.frame_duration_ms)

        logger.info(f"VAD initialized: {sample_rate}Hz, mode={vad_mode}, silence={silence_threshold_ms}ms")

    def process_audio_chunk(self, audio_chunk: np.ndarray) -> Optional[Tuple[np.ndarray, float, float]]:
        """
        Process an audio chunk and return completed speech segments.

        Args:
            audio_chunk: Audio chunk as numpy array (int16)

        Returns:
            Tuple of (segment_audio, start_time, duration_ms) if segment complete, None otherwise
        """
        # Convert to bytes for VAD (expects 16-bit PCM)
        if audio_chunk.dtype != np.int16:
            audio_chunk = (audio_chunk * 32767).astype(np.int16)

        # Process in frames
        chunk_frames = self._chunk_to_frames(audio_chunk)

        current_time = get_unix_timestamp()

        for frame in chunk_frames:
            is_speech = self.vad.is_speech(frame.tobytes(), self.sample_rate)

            if is_speech:
                self._handle_speech_frame(frame, current_time)
            else:
                segment = self._handle_silence_frame()
                if segment:
                    return segment

        # Check for max utterance timeout
        if (self._segment_start_time and
            len(self._current_segment) >= self.max_utterance_frames):
            logger.info("Max utterance length reached, forcing segment end")
            return self._end_segment()

        return None

    def _chunk_to_frames(self, audio_chunk: np.ndarray) -> List[np.ndarray]:
        """Split audio chunk into VAD frames."""
        frames = []
        pos = 0

        while pos + self.frame_samples <= len(audio_chunk):
            frame = audio_chunk[pos:pos + self.frame_samples]
            frames.append(frame)
            pos += self.frame_samples

        return frames

    def _handle_speech_frame(self, frame: np.ndarray, current_time: float) -> None:
        """Handle a speech frame."""
        if not self._current_segment:
            # Start new segment
            self._segment_start_time = current_time
            logger.debug("Speech detected, starting new segment")

        self._current_segment.append(frame)
        self._last_speech_time = current_time
        self._silence_frames = 0

    def _handle_silence_frame(self) -> Optional[Tuple[np.ndarray, float, float]]:
        """Handle a silence frame. Returns completed segment if silence threshold reached."""
        if not self._current_segment:
            return None

        self._silence_frames += 1

        if self._silence_frames >= self.silence_threshold_frames:
            return self._end_segment()

        return None

    def _end_segment(self) -> Optional[Tuple[np.ndarray, float, float]]:
        """End current segment and return it if valid."""
        if not self._current_segment or not self._segment_start_time:
            return None

        # Concatenate frames
        segment_audio = np.concatenate(self._current_segment)

        # Calculate duration
        segment_duration_ms = format_duration_ms(len(segment_audio) / self.sample_rate)

        # Check minimum length
        if segment_duration_ms < self.min_segment_ms:
            logger.debug(f"Segment too short ({segment_duration_ms}ms), discarding")
            self._reset_segment()
            return None

        start_time = self._segment_start_time
        end_time = self._last_speech_time or start_time

        logger.info(f"Speech segment completed: {segment_duration_ms}ms, "
                   f"frames: {len(self._current_segment)}")

        self._reset_segment()
        return (segment_audio, start_time, segment_duration_ms)

    def _reset_segment(self) -> None:
        """Reset segment state."""
        self._current_segment = []
        self._segment_start_time = None
        self._last_speech_time = None
        self._silence_frames = 0

    def flush(self) -> Optional[Tuple[np.ndarray, float, float]]:
        """Flush any pending segment."""
        if self._current_segment:
            logger.info("Flushing pending segment")
            return self._end_segment()
        return None

    @staticmethod
    def test_vad_mode(audio_chunk: np.ndarray, sample_rate: int = 16000, mode: int = 3) -> float:
        """Test VAD on a chunk and return speech ratio."""
        vad = webrtcvad.Vad(mode)
        frame_samples = int(sample_rate * 30 / 1000)  # 30ms frames

        speech_frames = 0
        total_frames = 0

        pos = 0
        while pos + frame_samples <= len(audio_chunk):
            frame = audio_chunk[pos:pos + frame_samples]
            if vad.is_speech(frame.tobytes(), sample_rate):
                speech_frames += 1
            total_frames += 1
            pos += frame_samples

        return speech_frames / total_frames if total_frames > 0 else 0.0