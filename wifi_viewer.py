"""
EDITH WiFi Camera Viewer
Receives MJPEG stream from XIAO ESP32S3 over WiFi and displays it.

Usage:
1. Connect XIAO via USB once to get its IP address from Serial Monitor
2. Update STREAM_URL below with that IP
3. Power XIAO with battery (no USB needed)
4. Run: python wifi_viewer.py
5. Press 'q' to quit
"""

import cv2
import urllib.request
import numpy as np
import sys

# ============================================
# CHANGE THIS TO YOUR XIAO'S IP ADDRESS
# ============================================
CAMERA_IP = "10.185.235.138"  # <-- Update this!
# ============================================

STREAM_URL = f"http://{CAMERA_IP}/stream"

def main():
    print(f"Connecting to EDITH camera at {STREAM_URL}...")
    print("Press 'q' to quit\n")

    try:
        stream = urllib.request.urlopen(STREAM_URL, timeout=10)
    except Exception as e:
        print(f"ERROR: Could not connect to camera at {CAMERA_IP}")
        print(f"  - Is the XIAO powered on?")
        print(f"  - Is it connected to WiFi '{CAMERA_IP}'?")
        print(f"  - Are you on the same network?")
        print(f"\nDetails: {e}")
        sys.exit(1)

    print("Connected! Streaming...")

    bytes_data = b''
    frame_count = 0

    while True:
        try:
            bytes_data += stream.read(1024)

            # Find JPEG frame boundaries
            a = bytes_data.find(b'\xff\xd8')  # JPEG start marker
            b = bytes_data.find(b'\xff\xd9')  # JPEG end marker

            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]

                # Decode and display frame
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

                if frame is not None:
                    frame_count += 1
                    # Add frame counter overlay
                    cv2.putText(frame, f"Frame: {frame_count}", (10, 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.imshow('EDITH Camera', frame)

            # Check for quit key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Stream error: {e}")
            break

    print(f"\nTotal frames received: {frame_count}")
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
