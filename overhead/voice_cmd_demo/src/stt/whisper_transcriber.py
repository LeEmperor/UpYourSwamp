import numpy as np
from faster_whisper import WhisperModel
from typing import Optional, Tuple
from ..utils.logging import get_logger
from ..utils.time import format_duration_ms

logger = get_logger("whisper_transcriber")

class WhisperTranscriber:
    """Speech-to-text using Faster Whisper."""

    def __init__(self,
                 model_size: str = "base",
                 device: str = "cpu",
                 compute_type: str = "int8",
                 download_root: Optional[str] = None):
        """
        Initialize Whisper transcriber.

        Args:
            model_size: Model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            compute_type: Compute type for optimization
            download_root: Custom download directory for models
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

        logger.info(f"Loading Whisper model: {model_size} on {device}")

        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root=download_root
            )
            logger.info("Whisper model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(self,
                   audio_data: np.ndarray,
                   sample_rate: int = 16000,
                   language: Optional[str] = None) -> Tuple[str, Optional[float]]:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Audio as numpy array (int16 or float32)
            sample_rate: Sample rate of audio
            language: Language code (None for auto-detection)

        Returns:
            Tuple of (transcribed_text, confidence_score)
        """
        try:
            # Convert to float32 if needed
            if audio_data.dtype == np.int16:
                audio_float = audio_data.astype(np.float32) / 32768.0
            else:
                audio_float = audio_data.astype(np.float32)

            # Transcribe
            segments, info = self.model.transcribe(
                audio_float,
                language=language,
                beam_size=5,
                patience=1,
                length_penalty=1,
                repetition_penalty=1,
                no_repeat_ngram_size=0,
                initial_prompt=None,
                suppress_blank=True,
                suppress_tokens=[-1],
                without_timestamps=True,
                max_initial_timestamp=1.0,
                hallucination_silence_threshold=None
            )

            # Combine all segments
            text_parts = []
            total_confidence = 0.0
            segment_count = 0

            for segment in segments:
                text_parts.append(segment.text)
                if hasattr(segment, 'avg_logprob'):
                    # Convert log probability to confidence (rough approximation)
                    confidence = min(1.0, max(0.0, segment.avg_logprob + 4) / 4)
                    total_confidence += confidence
                    segment_count += 1

            full_text = "".join(text_parts).strip()

            # Average confidence
            avg_confidence = total_confidence / segment_count if segment_count > 0 else None

            duration_ms = format_duration_ms(len(audio_data) / sample_rate)

            logger.info(f"Transcription complete: '{full_text}' ({duration_ms}ms, conf: {avg_confidence})")

            return full_text, avg_confidence

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return "", None

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type
        }

    @staticmethod
    def list_available_models() -> list[str]:
        """List available Whisper model sizes."""
        return ["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3", "large"]

    @staticmethod
    def estimate_model_size(model_size: str) -> str:
        """Estimate model size requirements."""
        sizes = {
            "tiny": "~39 MB",
            "base": "~74 MB",
            "small": "~244 MB",
            "medium": "~769 MB",
            "large": "~1550 MB"
        }
        return sizes.get(model_size, "Unknown")