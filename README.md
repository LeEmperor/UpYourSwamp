# UpYourSwamp: Automated Helping Hands for Soldering and Workshop Assistance

UpYourSwamp is an automated “helping hands” system for soldering and general electronics workbenches. The goal is to let a user speak natural requests such as:

* “Can you hold this for me?”
* “Can you find me a Raspberry Pi in my workspace?”
* “What resistor value is this part?”
* “What’s the pinout/spec for this IC?”

The system combines:

* A workspace camera (ESP32-CAM) for visual context
* A microphone and conversational interface (LiveKit AI)
* A vision understanding layer (Overshoot AI) that outputs structured results
* A reasoning/action layer (Google Gemini) that chooses the system response or physical action
* An embedded controller (IMU + steppers) that moves the helping hands to requested positions

## High-level Architecture

### Data flow (end-to-end)

1. **User speech → LiveKit AI**

   * User speaks a request.
   * LiveKit handles audio capture and speech-to-text.
   * The transcribed text becomes the system’s request prompt.

2. **Workspace video → Overshoot AI**

   * ESP32-CAM provides a live view of the workspace.
   * Video is processed by Overshoot AI using the prompt context (e.g., “find a Raspberry Pi”).
   * Overshoot returns either free-text or structured JSON describing relevant objects and scene information.

3. **Overshoot JSON → Google Gemini**

   * Gemini receives:

     * The user’s request (intent)
     * Overshoot’s structured output (grounding)
     * Any relevant system state (optional)
   * Gemini decides what to do next:

     * Answer informational questions (possibly with internet lookup)
     * Or produce an action plan for the helping hands

4. **Gemini action → Embedded controller**

   * For physical tasks, Gemini outputs an action request (target object, target region).
   * The embedded controller estimates pose/position using IMU and camera-based measurements and moves stepper motors accordingly.
   * A Kalman filter fuses IMU + camera observations to stabilize motion in the workspace frame.

5. **System response → LiveKit AI (TTS)**

   * For informational tasks or confirmations, LiveKit speaks the response back to the user.

## Repository Layout

* `Camera_Code/`

  * `overshoot_runner/`

    * `run_overshoot_video.mjs`
      Node script that runs Overshoot AI on a video clip and emits JSON lines.
    * `process_esp_cam_with_overshoot.py`
      Python script that captures video from ESP32-CAM, writes a short clip, calls the Node runner, and prints the results.
    * `package.json`, `package-lock.json`
      Node dependencies for Overshoot SDK.
  * `finger_tip_tracking/`
    OpenCV experiments related to fingertip tracking and setup.
* `LiveKit_runner/`
  Placeholder for voice agent integration (planned / WIP).
* `README.md`

## Current Implementation Status

### Implemented

* ESP32-CAM stream ingestion on laptop (Python/OpenCV)
* Windowed clip generation (`.mp4`)
* Overshoot runner (Node) operating on a video file source
* JSON output emitted by Overshoot runner and collected by Python

### Planned / In progress

* LiveKit AI microphone pipeline (speech-to-text and text-to-speech)
* Gemini integration (reasoning + tool calls)
* Actuation pipeline to embedded controller (IMU + stepper control)
* Sensor fusion (Kalman filter) and workspace calibration

## Requirements (Laptop Dev)

### Python

* Python 3.x
* Recommended: virtual environment

### Node.js

* Node 18+ recommended
* npm

## Setup (Laptop)

### 1) Clone the repo

```powershell
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>
```

### 2) Install Node dependencies for Overshoot

```powershell
cd Camera_Code\overshoot_runner
npm install
```

### 3) Create and activate Python venv

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -U pip
pip install opencv-python
```

### 4) Set environment variables

Do not hardcode API keys into source.

```powershell
setx OVERSHOOT_API_KEY "YOUR_OVERSHOOT_KEY"
setx ESP_CAM_URL "http://192.168.4.1:81/stream"
setx OVERSHOOT_PROMPT "describe what you see"
```

Close and reopen your terminal after `setx`.

### 5) Run the pipeline

From `Camera_Code\overshoot_runner`:

```powershell
.\.venv\Scripts\activate
python .\process_esp_cam_with_overshoot.py
```

Expected behavior:

* Captures a short clip from `ESP_CAM_URL`
* Calls:

  * `node run_overshoot_video.mjs <clip_path>`
* Prints JSON results to stdout

## Notes on Overshoot Video Input

Overshoot SDK supports:

* `camera` input in a browser
* `video file` input in a browser/SDK environment

This repository currently uses a windowed approach:

* ESP32-CAM stream → short clip → Overshoot inference → JSON output

This is not true frame-by-frame “live inference,” but it is sufficient for many workshop assistance tasks.

## Suggested Message Format (for downstream Gemini)

For reliable debugging and tracing, all stages should share a `request_id` and timestamps.

Example payload to Gemini:

```json
{
  "request_id": "uuid-or-counter",
  "user_text": "can you find me a raspberry pi in my workspace",
  "overshoot": {
    "ts": 1730000000,
    "text": "I see a PCB and a small computer board near the center..."
  }
}
```

## Roadmap

* Integrate LiveKit: audio capture, STT, and TTS responses
* Add Gemini action planner:

  * structured action JSON
  * tool calls for “look up specs”
* Add workspace calibration:

  * reference frame markers (AprilTag recommended)
* Add actuator stack:

  * IMU + steppers
  * Kalman filter for stable positioning
* Add logging + request tracing:

  * consistent request IDs across modules
  * persistent logs for replay

## Safety Notes

This system is intended for controlled bench-top environments. Actuation should include:

* speed limits
* emergency stop
* collision/obstacle detection
* confirmation prompts for risky actions
