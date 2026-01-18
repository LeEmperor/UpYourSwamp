# UpYourSwamp

**Automated Helping Hands for Soldering and Workshop Assistance**

UpYourSwamp is an AI-assisted robotic “helping hands” system for soldering and general electronics workbenches. The system allows a user to speak natural language requests such as:

* “Can you hold this for me?”
* “Can you find me a Raspberry Pi in my workspace?”
* “What resistor value is this?”
* “What are the specs of this IC?”

The system integrates **audio understanding**, **dual-camera geometric vision**, **AI reasoning**, and **closed-loop robotic actuation** to assist users hands-free during technical work.

---

## System Architecture Overview

### End-to-End Pipeline

```
User Speech
   ↓
LiveKit AI (Speech-to-Text)
   ↓
User Intent (Text Prompt)
   ↓
Overshoot AI (Vision Grounding)
   ↓
Structured Vision JSON
   ↓
Geometry & Triangulation
   ↓
Workspace Coordinates
   ↓
Google Gemini (Planning & Decision)
   ↓
Action Output
   ├── Verbal Response → LiveKit AI (TTS)
   └── Physical Action → Embedded Controller
```

Each stage communicates using **explicit, structured JSON**, enabling debugging, logging, and deterministic behavior.

---

## Hardware Configuration

### Cameras (Dual ESP32-CAM Setup)

* **Camera A (Top-Down)**

  * Mounted orthogonal to the workspace plane
  * Primary source for **x–y localization**
* **Camera B (Angled / Side View)**

  * Mounted with known baseline relative to Camera A
  * Used for **depth (z) estimation via triangulation**

Both cameras are rigidly mounted and treated as static sensors.

### Actuation Hardware

* Stepper motors controlling helping hands
* IMU mounted on end-effector
* Embedded controller (MCU)
* Emergency stop and motion limits (required)

---

## Workspace Coordinate System

All positions are expressed in a **shared workspace frame**:

* Origin: fixed point on the bench (e.g., fiducial origin)
* Axes:

  * +X → right
  * +Y → away from user
  * +Z → upward from table

All vision outputs, estimated poses, and actuator commands are expressed in this frame.

---

## Camera Calibration

### Intrinsic Calibration (Per Camera)

Performed once using a checkerboard or Charuco board.

Parameters:

* Focal length
* Principal point
* Lens distortion

Output:

* Camera matrix `K`
* Distortion coefficients

### Extrinsic Calibration (Camera → Workspace)

Each camera computes a rigid transform:

```
T_workspace_camera = [ R | t ]
```

This is done by observing a fixed fiducial (AprilTag / Charuco board) rigidly mounted in the workspace.

---

## Geometric Triangulation (Core Vision Math)

### Inputs

From Overshoot AI (per camera):

* Object or keypoint pixel coordinates `(u, v)`
* Camera ID
* Confidence score

### Projection Model

Each camera obeys:

```
s [u v 1]^T = K [R | t] [X Y Z 1]^T
```

Where:

* `(X, Y, Z)` is the workspace coordinate
* `K` is intrinsic matrix
* `[R | t]` is camera extrinsic transform

### Triangulation Process

1. Convert pixel coordinates → normalized camera rays
2. Transform rays into workspace frame
3. Compute closest point between rays from Camera A and Camera B
4. Use midpoint of shortest line segment as 3D estimate
5. Reject or downweight estimates with poor ray intersection geometry

### Output

A metric 3D point in workspace coordinates:

```json
{
  "x": 124.2,
  "y": 87.5,
  "z": 18.3,
  "units": "mm",
  "confidence": 0.89
}
```

---

## Camera Placement Constraints (Critical)

To ensure stable triangulation:

* Cameras must have a **non-zero baseline** (recommended ≥ 10–15 cm)
* Optical axes must not be parallel
* Workspace must lie within overlapping fields of view
* Avoid extremely shallow angles (<10° between rays)

Poor placement results in large depth uncertainty.

---

## Overshoot AI Role (Vision Grounding)

Overshoot AI **does not decide actions**. It only answers:

> “What is visible and relevant given this prompt?”

### Overshoot Output Contract (Per Camera)

```json
{
  "camera_id": "top_down",
  "detections": [
    {
      "object": "raspberry_pi",
      "bbox": [x_min, y_min, x_max, y_max],
      "confidence": 0.92
    }
  ],
  "timestamp": 1730000000
}
```

Bounding boxes or keypoints are converted into pixel coordinates for triangulation.

---

## Geometry Module Contract

### Input (From Overshoot)

```json
{
  "request_id": "uuid",
  "detections": {
    "top_down": { "bbox": [...] },
    "side_view": { "bbox": [...] }
  }
}
```

### Output (To Gemini)

```json
{
  "request_id": "uuid",
  "object": "raspberry_pi",
  "workspace_position": {
    "x": 124.2,
    "y": 87.5,
    "z": 18.3,
    "units": "mm"
  }
}
```

---

## Google Gemini Role (Planning, Not Geometry)

Gemini **never outputs motor coordinates**.

Gemini responsibilities:

* Interpret user intent
* Decide response type:

  * Informational
  * Physical assistance
* Output **high-level action directives**

### Gemini Action Output Contract

```json
{
  "request_id": "uuid",
  "action": "hold",
  "target": {
    "object": "pcb",
    "reference_point": "center"
  },
  "constraints": {
    "stability": "high",
    "force": "light"
  }
}
```

---

## End-Effector Pose Estimation

### State Vector (Example)

```
[x, y, z, vx, vy, vz]
```

Optional:

* Orientation quaternion

### Sensors

* Vision (absolute position)
* IMU (orientation, short-term dynamics)
* Motor commands (prediction)

### Filter

A Kalman filter fuses:

* Kinematic prediction from steppers
* Vision-based corrections
* IMU orientation updates

Vision corrects drift; IMU smooths motion.

---

## Controller Interface

### Input (From Planner)

```json
{
  "target_pose": {
    "x": 124.2,
    "y": 87.5,
    "z": 18.3
  },
  "mode": "hold"
}
```

### Output

* Stepper trajectories
* Velocity and acceleration limits
* Continuous pose updates

---

## Safety Considerations

* Emergency stop
* Velocity and acceleration limits
* Collision avoidance zones
* Confirmation for risky actions
* Timeout on ambiguous commands

---

## Repository Structure

```
UPYOURSWAMP/
├── Camera_Code/
│   ├── overshoot_runner/
│   │   ├── run_overshoot_video.mjs
│   │   ├── process_esp_cam_with_overshoot.py
│   │   ├── package.json
│   │   └── node_modules/
│   ├── finger_tip_tracking/
│   └── LiveKit_runner/        (planned)
└── README.md
```

---

## Design Philosophy

* **Geometry is deterministic**
* **LLMs reason, not measure**
* **All inter-module communication is structured**
* **Perception, planning, and control are isolated**
* **Human safety overrides autonomy**

---

## Roadmap

* LiveKit audio integration
* AprilTag workspace calibration
* End-effector visual marker
* Closed-loop holding control
* Multi-tool attachments
* Real-time clip window reduction

---
