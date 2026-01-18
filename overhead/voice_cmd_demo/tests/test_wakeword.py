#!/usr/bin/env python3
"""
Simple test suite for wake word detection (standalone).
"""

import re

class SimpleWakeWordDetector:
    """Simplified wake word detector for testing."""

    def __init__(self, wake_word: str = "ai", case_sensitive: bool = False):
        self.wake_word = wake_word
        self.case_sensitive = case_sensitive
        flags = 0 if case_sensitive else re.IGNORECASE
        self.pattern = re.compile(rf'\b{re.escape(wake_word)}\b', flags)

    def detect(self, transcript: str):
        if not transcript:
            return None

        match = self.pattern.search(transcript)
        if not match:
            return None

        wake_word_found = match.group()
        wake_word_end = match.end()
        command_text = transcript[wake_word_end:].strip()

        # Clean up command text
        command_text = command_text.strip('.,!?;:')
        command_text = re.sub(r'\s+', ' ', command_text)

        if not command_text:
            return None

        return (wake_word_found, command_text)

def test_wakeword_detection():
    """Test wake word detection with various inputs."""

    detector = SimpleWakeWordDetector(wake_word="ai", case_sensitive=False)

    test_cases = [
        # (input_text, expected_result)
        ("ai turn on the lights", ("ai", "turn on the lights")),
        ("AI what time is it", ("AI", "what time is it")),
        ("hey ai play some music", ("ai", "play some music")),
        ("artificial intelligence is cool", None),  # Should not match partial
        ("I like ai", None),  # Should not match without word boundary
        ("ai", ("ai", "")),  # Wake word only
        ("", None),  # Empty string
        ("hello world", None),  # No wake word
        ("ai, what is the weather like", ("ai", "what is the weather like")),
    ]

    print("Testing wake word detection...")
    print("=" * 50)

    passed = 0
    total = len(test_cases)

    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = detector.detect(input_text)

        status = "PASS" if result == expected else "FAIL"

        print("2d")
        print(f"    Expected: {expected}")
        print(f"    Got:      {result}")
        print()

        if result == expected:
            passed += 1

    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\033[92mAll tests passed! ✓\033[0m")
        return True
    else:
        print("\033[91mSome tests failed! ✗\033[0m")
        return False

if __name__ == "__main__":
    import sys
    success = test_wakeword_detection()
    sys.exit(0 if success else 1)

def test_wakeword_detection():
    """Test wake word detection with various inputs."""

    detector = WakeWordDetector(wake_word="ai", case_sensitive=False)

    test_cases = [
        # (input_text, expected_result)
        ("ai turn on the lights", ("ai", "turn on the lights")),
        ("AI what time is it", ("AI", "what time is it")),
        ("hey ai play some music", ("ai", "play some music")),
        ("artificial intelligence is cool", None),  # Should not match partial
        ("I like ai", None),  # Should not match without word boundary
        ("ai", ("ai", "")),  # Wake word only
        ("", None),  # Empty string
        ("hello world", None),  # No wake word
        ("ai, what is the weather like", ("ai", "what is the weather like")),
    ]

    print("Testing wake word detection...")
    print("=" * 50)

    passed = 0
    total = len(test_cases)

    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = detector.detect(input_text)

        status = "PASS" if result == expected else "FAIL"
        color = "\033[92m" if status == "PASS" else "\033[91m"
        reset = "\033[0m"

        print("2d")
        print(f"    Expected: {expected}")
        print(f"    Got:      {result}")
        print()

        if result == expected:
            passed += 1

    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\033[92mAll tests passed! ✓\033[0m")
        return True
    else:
        print("\033[91mSome tests failed! ✗\033[0m")
        return False

if __name__ == "__main__":
    success = test_wakeword_detection()
    sys.exit(0 if success else 1)