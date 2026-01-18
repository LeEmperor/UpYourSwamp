# import json
# import os
# import subprocess
# import time
# from pathlib import Path

# import cv2

# OVERSHOOT_NODE = str(Path("overshoot_runner") / "run_overshoot_video.mjs")

# def require_env(name: str) -> str:
#     v = os.getenv(name)
#     if not v:
#         raise RuntimeError(f"Missing env var: {name}")
#     return v

# def record_clip_mjpeg(url: str, out_path: str, seconds: float = 3.0, fps: float = 20.0) -> None:
#     cap = cv2.VideoCapture(url)
#     if not cap.isOpened():
#         raise RuntimeError(f"Could not open stream: {url}")

#     width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
#     height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

#     fourcc = cv2.VideoWriter_fourcc(*"mp4v")
#     writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
#     if not writer.isOpened():
#         cap.release()
#         raise RuntimeError("Could not open VideoWriter (mp4v). Try installing codecs or use AVI.")

#     deadline = time.time() + seconds
#     try:
#         while time.time() < deadline:
#             ok, frame = cap.read()
#             if not ok:
#                 time.sleep(0.02)
#                 continue
#             if frame.shape[1] != width or frame.shape[0] != height:
#                 frame = cv2.resize(frame, (width, height))
#             writer.write(frame)
#     finally:
#         writer.release()
#         cap.release()

# def run_overshoot(video_path: str) -> list[dict]:
#     env = os.environ.copy()
#     require_env("OVERSHOOT_API_KEY")  

#     proc = subprocess.Popen(
#         ["node", OVERSHOOT_NODE, video_path],
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         text=True,
#         env=env
#     )

#     results: list[dict] = []
#     assert proc.stdout is not None

#     for line in proc.stdout:
#         line = line.strip()
#         if not line:
#             continue
#         try:
#             results.append(json.loads(line))
#         except json.JSONDecodeError:
#             results.append({"raw_line": line})

#     stderr = proc.stderr.read() if proc.stderr else ""
#     rc = proc.wait()

#     if rc != 0:
#         raise RuntimeError(f"Overshoot runner failed (rc={rc}). stderr:\n{stderr}")

#     return results

# def prepare_for_gemini(overshoot_results: list[dict]) -> dict:
#     return {
#         "source": "overshoot",
#         "results": overshoot_results
#     }

# def main():
#     # Example ESP32-CAM MJPEG URL
#     esp_url = os.getenv("ESP_CAM_URL", "http://192.168.4.1:81/stream")

#     tmp_dir = Path("tmp_clips")
#     tmp_dir.mkdir(exist_ok=True)

#     clip_path = str(tmp_dir / "clip.mp4")
#     record_clip_mjpeg(esp_url, clip_path, seconds=3.0, fps=20.0)

#     overshoot_results = run_overshoot(clip_path)
#     payload = prepare_for_gemini(overshoot_results)

#     print(json.dumps(payload, indent=2))

# if __name__ == "__main__":
#     main()


# process_live_esp_to_overshoot.py
import json
import os
import subprocess
import time
from pathlib import Path

import cv2


def require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def record_clip_mjpeg(url: str, out_path: str, seconds: float, fps: float) -> None:
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open stream: {url}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError("Could not open VideoWriter (mp4v). Try installing codecs or use AVI/MJPG.")

    deadline = time.time() + seconds
    try:
        while time.time() < deadline:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.02)
                continue
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height))
            writer.write(frame)
    finally:
        writer.release()
        cap.release()


def run_overshoot(node_runner_path: str, video_path: str) -> list[dict]:
    require_env("OVERSHOOT_API_KEY")

    env = os.environ.copy()
    proc = subprocess.Popen(
        ["node", node_runner_path, video_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )

    results: list[dict] = []
    assert proc.stdout is not None

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            results.append({"raw_line": line})

    stderr = proc.stderr.read() if proc.stderr else ""
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"Overshoot runner failed (rc={rc}). stderr:\n{stderr}")

    return results


def prepare_for_gemini(overshoot_results: list[dict]) -> dict:
    return {"source": "overshoot", "results": overshoot_results}


def main() -> None:
    esp_url = os.getenv("ESP_CAM_URL", "http://192.168.4.1:81/stream")

    node_runner = (Path(__file__).parent / "overshoot_runner" / "run_overshoot_video.mjs").resolve()
    if not node_runner.exists():
        raise RuntimeError(f"Node runner not found: {node_runner}")

    tmp_dir = (Path(__file__).parent / "tmp_clips")
    tmp_dir.mkdir(exist_ok=True)

    clip_seconds = float(os.getenv("CLIP_SECONDS", "2.0"))
    clip_fps = float(os.getenv("CLIP_FPS", "15.0"))
    gap_seconds = float(os.getenv("GAP_SECONDS", "0.2"))

    i = 0
    while True:
        clip_path = str(tmp_dir / f"clip_{i:04d}.mp4")
        record_clip_mjpeg(esp_url, clip_path, seconds=clip_seconds, fps=clip_fps)

        overshoot_results = run_overshoot(str(node_runner), clip_path)
        payload = prepare_for_gemini(overshoot_results)

        print(json.dumps(payload, indent=2))

        i += 1
        time.sleep(gap_seconds)


if __name__ == "__main__":
    main()
