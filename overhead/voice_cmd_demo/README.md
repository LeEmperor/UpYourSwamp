# Voice Command Demo

A hackathon-ready "always-on" voice command listener that uses local AI models for speech processing. Perfect for integrating with computer vision systems or other AI pipelines.

## Features

- 🎤 **Real-time microphone listening** or **audio file processing**
- 🎯 **Voice Activity Detection (VAD)** for automatic speech segmentation
- 🗣️ **Local Whisper transcription** (no cloud APIs required)
- 🚨 **Wake word detection** (e.g., "AI turn on lights")
- 📡 **Event-driven architecture** with pluggable subscribers
- 🔄 **Demo video pipeline integration** ready

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv voice_env
voice_env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Microphone Demo

```powershell
# From voice_cmd_demo directory
.\scripts\run_mic.ps1
```

Then say: **"AI turn on the lights"** or **"AI what time is it"**

### 3. Run File Demo

```powershell
# Process a WAV file
.\scripts\run_file.ps1 -AudioFile "path\to\your\audio.wav"
```

## What You'll See

```
🎤 COMMAND DETECTED: 'turn on the lights' (wake: 'ai', confidence: 0.85)
🎬 VIDEO_PIPELINE_TRIGGER: utterance_id=utt_1703123456789 command='turn on the lights'
```

Events are also logged to `events.log` as NDJSON:

```json
{"event_type":"command_detected","timestamp_iso":"2024-01-18T10:30:56.789Z","raw_transcript":"ai turn on the lights","wake_word":"ai","command_text":"turn on the lights","confidence":0.85,"audio_duration_ms":1200,"utterance_id":"utt_1703123456789"}
```

## Architecture

```
Audio Input → VAD Segmentation → Whisper Transcription → Wake Word Detection → Event Bus → Subscribers
     ↓              ↓                    ↓                      ↓              ↓            ↓
  Mic/File      WebRTC VAD         Faster-Whisper           Regex Match    Publish     Video Pipeline
```

## Configuration

### CLI Options

```bash
python src/main.py --help
```

- `--source mic|file`: Audio source
- `--file PATH`: Audio file path (when source=file)
- `--wake WORD`: Wake word (default: "ai")
- `--model tiny|base|small|medium|large`: Whisper model size
- `--silence-ms MS`: Silence threshold (default: 900ms)
- `--max-utterance-s SEC`: Max utterance length (default: 10s)

### Settings File

Edit `config/settings.yaml` for default values:

```yaml
audio:
  sample_rate: 16000
vad:
  silence_threshold_ms: 900
whisper:
  model_size: base
wake_word:
  default_word: "ai"
```

## Requirements

- **Python 3.11+**
- **Windows 10/11** (tested on Windows)
- **Microphone** (for mic mode)
- **~2GB RAM** minimum (base model)

### Dependencies

- `faster-whisper`: Local speech-to-text
- `webrtcvad`: Voice activity detection
- `sounddevice`: Audio capture
- `scipy`: Audio processing
- `PyYAML`: Configuration
- `pydantic`: Data validation

## Troubleshooting

### Microphone Issues

**"No audio devices found"**
```python
# List available devices
from src.audio.capture import AudioCapture
AudioCapture.list_devices()
```

**"Permission denied"**
- Windows: Check microphone permissions in Settings > Privacy > Microphone
- Ensure no other apps are using the microphone

### Audio Quality Issues

**Poor transcription quality**
- Use larger Whisper model: `--model medium`
- Speak clearly and closer to microphone
- Reduce background noise

**VAD not triggering**
- Adjust silence threshold: `--silence-ms 500`
- Test with different VAD modes (modify code)

### Performance Issues

**High CPU usage**
- Use smaller model: `--model tiny`
- Close other applications

**Latency/delay**
- This is expected with local processing
- Base model: ~2-3 seconds per utterance
- Tiny model: ~0.5-1 second per utterance

### Sample Rate Issues

**"Sample rate not supported"**
- Ensure audio is 16kHz mono
- WAV files are automatically resampled
- Mic input uses 16kHz by default

## Integration with Video Pipeline

The event bus publishes `CommandDetected` events that your video system can subscribe to:

```python
from src.events.bus import subscribe_to_event
from src.events.schemas import CommandDetected

def handle_command(event: CommandDetected):
    if "turn on lights" in event.command_text:
        # Trigger video analysis or camera control
        print(f"Video pipeline: {event.command_text}")

subscribe_to_event("command_detected", handle_command)
```

## File Structure

```
voice_cmd_demo/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── config/
│   └── settings.yaml     # Default configuration
├── src/
│   ├── main.py           # Entry point
│   ├── audio/
│   │   ├── capture.py    # Microphone capture
│   │   └── file_input.py # File audio input
│   ├── vad/
│   │   └── segmenter.py  # Voice activity detection
│   ├── stt/
│   │   └── whisper_transcriber.py  # Speech-to-text
│   ├── wake/
│   │   └── wakeword.py   # Wake word detection
│   ├── events/
│   │   ├── bus.py        # Event bus implementation
│   │   ├── schemas.py    # Event data models
│   │   └── sinks.py      # Event subscribers
│   └── utils/
│       ├── logging.py    # Logging setup
│       └── time.py       # Time utilities
├── scripts/
│   ├── run_mic.ps1       # Microphone demo script
│   └── run_file.ps1      # File processing script
└── tests/
    └── test_wakeword.py  # Wake word tests
```

## Development

### Running Tests

```bash
python tests/test_wakeword.py
```

### Adding New Event Types

1. Define schema in `src/events/schemas.py`
2. Add handler in `src/events/sinks.py`
3. Subscribe in main pipeline

### Custom Audio Processing

Extend `AudioCapture` or `AudioFileInput` for custom audio sources.

## License

Hackathon project - use as needed!

---

**Happy hacking! 🎉**