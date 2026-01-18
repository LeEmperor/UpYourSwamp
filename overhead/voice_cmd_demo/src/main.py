#!/usr/bin/env python3
"""
Voice Command Demo - Always-on voice command listener with wake word detection.

This script continuously listens for voice commands using:
- Microphone capture or audio file input
- Voice Activity Detection (VAD) for speech segmentation
- Whisper transcription for speech-to-text
- Wake word detection for command triggering
- Event bus for decoupled communication
"""

import argparse
import signal
import sys
import threading
import queue
import time
import numpy as np
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.audio.capture import AudioCapture
from src.audio.file_input import AudioFileInput
from src.vad.segmenter import VADSegmenter
from src.stt.whisper_transcriber import WhisperTranscriber
from src.wake.wakeword import WakeWordDetector
from src.events.bus import get_event_bus, subscribe_to_event, shutdown_event_bus
from src.events.schemas import CommandDetected, AudioSegment, TranscriptionResult
from src.events.sinks import create_default_sinks
from src.utils.logging import setup_logging, get_logger
from src.utils.time import get_iso_timestamp

logger = get_logger("main")

class VoiceCommandPipeline:
    """Main voice command processing pipeline."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.running = False

        # Initialize components
        self._init_components()

        # Setup event bus and sinks
        self.event_bus = get_event_bus()
        self._setup_event_sinks()

        # Audio processing queue
        self.audio_queue = queue.Queue(maxsize=100)

        logger.info("Voice command pipeline initialized")

    def _init_components(self):
        """Initialize pipeline components."""
        # Wake word detector
        self.wake_detector = WakeWordDetector(
            wake_word=self.args.wake,
            case_sensitive=False
        )

        # Whisper transcriber
        self.transcriber = WhisperTranscriber(
            model_size=self.args.model,
            device="cpu",  # CPU for demo
            compute_type="int8"
        )

        # VAD segmenter
        self.segmenter = VADSegmenter(
            sample_rate=16000,
            silence_threshold_ms=self.args.silence_ms,
            min_segment_ms=300,
            max_utterance_s=self.args.max_utterance_s
        )

        # Audio source
        if self.args.source == "mic":
            self.audio_source = AudioCapture(
                sample_rate=16000,
                channels=1,
                dtype='int16'
            )
        else:
            self.audio_source = AudioFileInput(
                file_path=self.args.file,
                chunk_size=1024,
                target_sample_rate=16000
            )

    def _setup_event_sinks(self):
        """Setup event sinks for command detection."""
        sinks = create_default_sinks(log_file="events.log")

        for sink in sinks:
            subscribe_to_event("command_detected", sink.handle_event)

        logger.info("Event sinks configured")

    def start(self):
        """Start the voice command pipeline."""
        self.running = True
        logger.info("Starting voice command pipeline...")

        try:
            if isinstance(self.audio_source, AudioCapture):
                self._start_microphone_pipeline()
            else:
                self._start_file_pipeline()

        except KeyboardInterrupt:
            logger.info("Pipeline interrupted by user")
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
        finally:
            self.stop()

    def _start_microphone_pipeline(self):
        """Start pipeline with microphone input."""
        logger.info("Starting microphone input pipeline")

        # Start audio capture
        self.audio_source.start()

        # Process audio chunks
        while self.running:
            try:
                # Get audio chunk with timeout
                audio_chunk = self.audio_source.get_audio_chunk(timeout=0.1)

                if audio_chunk is not None:
                    self._process_audio_chunk(audio_chunk)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing microphone audio: {e}")
                time.sleep(0.1)

    def _start_file_pipeline(self):
        """Start pipeline with file input."""
        logger.info(f"Starting file input pipeline: {self.args.file}")

        # Process file chunks
        for audio_chunk in self.audio_source.get_chunks():
            if not self.running:
                break

            try:
                self._process_audio_chunk(audio_chunk)
                # Small delay to simulate real-time processing
                time.sleep(0.01)
            except Exception as e:
                logger.error(f"Error processing file audio: {e}")

        logger.info("File processing complete")

    def _process_audio_chunk(self, audio_chunk: np.ndarray):
        """Process a chunk of audio through the pipeline."""
        # Run VAD segmentation
        segment_result = self.segmenter.process_audio_chunk(audio_chunk)

        if segment_result:
            segment_audio, start_time, duration_ms = segment_result
            self._process_speech_segment(segment_audio, duration_ms)

    def _process_speech_segment(self, audio_data: np.ndarray, duration_ms: int):
        """Process a complete speech segment."""
        try:
            # Transcribe
            transcript, confidence = self.transcriber.transcribe(audio_data)

            if not transcript:
                logger.debug("Empty transcription, skipping")
                return

            # Publish transcription event
            trans_event = TranscriptionResult(
                timestamp_iso=get_iso_timestamp(),
                transcript=transcript,
                confidence=confidence,
                audio_duration_ms=duration_ms,
                utterance_id=f"utt_{int(time.time() * 1000)}"
            )
            self.event_bus.publish(trans_event)

            # Check for wake word
            wake_result = self.wake_detector.detect(transcript)

            if wake_result:
                wake_word, command_text = wake_result

                # Publish command detected event
                cmd_event = CommandDetected(
                    timestamp_iso=get_iso_timestamp(),
                    raw_transcript=transcript,
                    wake_word=wake_word,
                    command_text=command_text,
                    confidence=confidence,
                    audio_duration_ms=duration_ms,
                    utterance_id=trans_event.utterance_id
                )
                self.event_bus.publish(cmd_event)

        except Exception as e:
            logger.error(f"Error processing speech segment: {e}", exc_info=True)

    def stop(self):
        """Stop the pipeline."""
        if not self.running:
            return

        logger.info("Stopping voice command pipeline...")
        self.running = False

        # Stop audio source
        if hasattr(self.audio_source, 'stop'):
            self.audio_source.stop()

        # Flush any pending segments
        try:
            segment_result = self.segmenter.flush()
            if segment_result:
                segment_audio, start_time, duration_ms = segment_result
                self._process_speech_segment(segment_audio, duration_ms)
        except Exception as e:
            logger.error(f"Error flushing segments: {e}")

        logger.info("Pipeline stopped")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Voice Command Demo")
    parser.add_argument(
        "--source", choices=["mic", "file"], default="mic",
        help="Audio source (default: mic)"
    )
    parser.add_argument(
        "--file", type=str,
        help="Audio file path (required when source=file)"
    )
    parser.add_argument(
        "--wake", type=str, default="ai",
        help="Wake word to detect (default: ai)"
    )
    parser.add_argument(
        "--silence-ms", type=int, default=900,
        help="Silence threshold in milliseconds (default: 900)"
    )
    parser.add_argument(
        "--max-utterance-s", type=int, default=10,
        help="Maximum utterance length in seconds (default: 10)"
    )
    parser.add_argument(
        "--model", choices=["tiny", "base", "small", "medium", "large"],
        default="base", help="Whisper model size (default: base)"
    )
    parser.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO", help="Logging level (default: INFO)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.source == "file" and not args.file:
        parser.error("--file is required when source=file")

    # Setup logging
    setup_logging(level=args.log_level)

    logger.info("Voice Command Demo starting...")
    logger.info(f"Source: {args.source}")
    if args.file:
        logger.info(f"File: {args.file}")
    logger.info(f"Wake word: {args.wake}")
    logger.info(f"Model: {args.model}")

    # Create and start pipeline
    pipeline = VoiceCommandPipeline(args)

    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        pipeline.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        pipeline.start()
    finally:
        shutdown_event_bus()
        logger.info("Voice Command Demo shutdown complete")

if __name__ == "__main__":
    main()