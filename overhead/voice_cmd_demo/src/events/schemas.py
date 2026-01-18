from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from uuid import uuid4
import json

class BaseEvent(BaseModel):
    """Base event class with common fields."""
    event_type: str = Field(..., description="Type of event")
    timestamp_iso: str = Field(..., description="ISO 8601 timestamp")
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event ID")

class CommandDetected(BaseEvent):
    """Event fired when a voice command is detected after wake word."""
    event_type: str = "command_detected"
    raw_transcript: str = Field(..., description="Full transcribed text")
    wake_word: str = Field(..., description="Detected wake word")
    command_text: str = Field(..., description="Command text after wake word")
    confidence: Optional[float] = Field(None, description="Transcription confidence score")
    audio_duration_ms: int = Field(..., description="Duration of audio segment in ms")
    utterance_id: str = Field(..., description="Unique ID for this utterance")

class AudioSegment(BaseEvent):
    """Event fired when an audio segment is captured."""
    event_type: str = "audio_segment"
    audio_data: bytes = Field(..., description="Raw audio data")
    duration_ms: int = Field(..., description="Duration in milliseconds")
    sample_rate: int = Field(..., description="Sample rate")
    channels: int = Field(..., description="Number of channels")

class TranscriptionResult(BaseEvent):
    """Event fired when transcription is complete."""
    event_type: str = "transcription_result"
    transcript: str = Field(..., description="Transcribed text")
    confidence: Optional[float] = Field(None, description="Confidence score")
    audio_duration_ms: int = Field(..., description="Audio duration in ms")
    utterance_id: str = Field(..., description="Unique utterance ID")

def event_to_dict(event: BaseEvent) -> Dict[str, Any]:
    """Convert event to dictionary for serialization."""
    return event.model_dump()

def event_to_json(event: BaseEvent) -> str:
    """Convert event to JSON string."""
    return event.model_dump_json()

def dict_to_event(data: Dict[str, Any]) -> BaseEvent:
    """Convert dictionary back to event object."""
    event_type = data.get("event_type")
    if event_type == "command_detected":
        return CommandDetected(**data)
    elif event_type == "audio_segment":
        return AudioSegment(**data)
    elif event_type == "transcription_result":
        return TranscriptionResult(**data)
    else:
        raise ValueError(f"Unknown event type: {event_type}")