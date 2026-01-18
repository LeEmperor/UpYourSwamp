import re
from typing import Optional, Tuple
from ..utils.logging import get_logger

logger = get_logger("wakeword_detector")

class WakeWordDetector:
    """Detects wake words in transcribed text."""

    def __init__(self, wake_word: str = "ai", case_sensitive: bool = False):
        """
        Initialize wake word detector.

        Args:
            wake_word: The wake word to detect
            case_sensitive: Whether detection should be case sensitive
        """
        self.wake_word = wake_word
        self.case_sensitive = case_sensitive

        # Compile regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        # Word boundaries to avoid partial matches
        self.pattern = re.compile(rf'\b{re.escape(wake_word)}\b', flags)

        logger.info(f"WakeWordDetector initialized: '{wake_word}' (case_sensitive={case_sensitive})")

    def detect(self, transcript: str) -> Optional[Tuple[str, str]]:
        """
        Detect wake word in transcript and extract command.

        Args:
            transcript: Full transcribed text

        Returns:
            Tuple of (wake_word, command_text) if detected, None otherwise
        """
        if not transcript:
            return None

        # Find wake word
        match = self.pattern.search(transcript)

        if not match:
            return None

        wake_word_found = match.group()
        wake_word_end = match.end()

        # Extract everything after the wake word as command
        command_text = transcript[wake_word_end:].strip()

        # Clean up command text (remove extra punctuation, normalize spaces)
        command_text = self._clean_command_text(command_text)

        if not command_text:
            logger.debug(f"Wake word detected but no command text: '{transcript}'")
            return None

        logger.info(f"Wake word detected: '{wake_word_found}' -> command: '{command_text}'")
        return (wake_word_found, command_text)

    def _clean_command_text(self, text: str) -> str:
        """Clean and normalize command text."""
        if not text:
            return ""

        # Remove leading/trailing punctuation and whitespace
        text = text.strip('.,!?;:')

        # Normalize multiple spaces
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def set_wake_word(self, wake_word: str) -> None:
        """Update the wake word."""
        self.wake_word = wake_word
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self.pattern = re.compile(rf'\b{re.escape(wake_word)}\b', flags)
        logger.info(f"Wake word updated to: '{wake_word}'")

    def test_detection(self, test_transcripts: list[str]) -> list[Tuple[str, Optional[Tuple[str, str]]]]:
        """Test wake word detection on sample transcripts.

        Args:
            test_transcripts: List of transcripts to test

        Returns:
            List of (transcript, detection_result) pairs
        """
        results = []
        for transcript in test_transcripts:
            result = self.detect(transcript)
            results.append((transcript, result))
        return results