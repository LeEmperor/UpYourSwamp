"""
EDITH USB Serial Camera Viewer
Displays camera feed from the XIAO ESP32S3 over USB serial.

Usage:
  1. Close the PlatformIO Serial Monitor first!
  2. Run: python serial_viewer.py
  3. Press 'q' to quit
"""

import serial
import serial.tools.list_ports
import cv2
import numpy as np
import sys

BAUD_RATE = 921600

def list_ports():
    """List all available serial ports."""
    ports = serial.tools.list_ports.comports()
    print("\nAvailable serial ports:")
    for i, port in enumerate(ports):
        print(f"  {i+1}. {port.device} - {port.description}")
    return ports

def main():
    print("=== EDITH USB Serial Camera Viewer ===\n")

    # List all ports and let user choose
    ports = list_ports()

    if not ports:
        print("No serial ports found! Is the XIAO connected?")
        sys.exit(1)

    if len(ports) == 1:
        port = ports[0].device
        print(f"\nUsing only available port: {port}")
    else:
        print("\nEnter port number (or type COM port like 'COM8'): ", end="")
        choice = input().strip()

        if choice.upper().startswith("COM"):
            port = choice.upper()
        else:
            try:
                idx = int(choice) - 1
                port = ports[idx].device
            except (ValueError, IndexError):
                print("Invalid choice!")
                sys.exit(1)

    print(f"Connecting to {port} at {BAUD_RATE} baud...")

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=3)
    except serial.SerialException as e:
        print(f"Error: {e}")
        print("\nMake sure to CLOSE the PlatformIO Serial Monitor first!")
        sys.exit(1)

    print("Connected! Waiting for frames...")
    print("Press 'q' in the image window to quit.\n")

    # Reset the ESP32 by toggling DTR
    ser.dtr = False
    ser.dtr = True

    cv2.namedWindow("EDITH Camera (USB Serial)", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("EDITH Camera (USB Serial)", 640, 480)

    frame_count = 0

    # Clear any garbage in buffer
    ser.reset_input_buffer()

    while True:
        try:
            # Read bytes until we find "FRAME:"
            line = b""
            while True:
                byte = ser.read(1)
                if not byte:
                    break
                if byte == b'\n':
                    break
                line += byte

            line_str = line.decode('utf-8', errors='ignore').strip()

            if line_str.startswith("FRAME:"):
                # Get frame size
                try:
                    size = int(line_str.split(":")[1])
                except ValueError:
                    continue

                if size <= 0 or size > 100000:
                    continue

                # Read exactly 'size' bytes of JPEG data
                jpeg_data = b""
                remaining = size
                while remaining > 0:
                    chunk = ser.read(min(remaining, 4096))
                    if not chunk:
                        break
                    jpeg_data += chunk
                    remaining -= len(chunk)

                # Read until we hit END marker
                for _ in range(10):
                    end_line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if end_line == "END":
                        break

                # Decode and display
                if len(jpeg_data) >= size * 0.9:
                    nparr = np.frombuffer(jpeg_data[:size], np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if frame is not None:
                        frame_count += 1
                        cv2.putText(frame, f"Frame: {frame_count} (USB)", (10, 25),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv2.imshow("EDITH Camera (USB Serial)", frame)
                        print(f"\rFrame {frame_count}: {len(jpeg_data)} bytes    ", end="", flush=True)
                    else:
                        print(f"\rDecode failed ({len(jpeg_data)} bytes)    ", end="", flush=True)
                else:
                    print(f"\rIncomplete: {len(jpeg_data)}/{size} bytes    ", end="", flush=True)

            elif line_str == "CAMERA_READY":
                print("Camera initialized!")
            elif line_str.startswith("IP:"):
                print(f"\nWiFi also available at: http://{line_str[3:]}")
            elif line_str and len(line_str) < 100:
                # Print other short messages from ESP32
                if "fail" in line_str.lower() or "error" in line_str.lower():
                    print(f"\nESP32: {line_str}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError: {e}")
            continue

        # Check for quit key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    ser.close()
    cv2.destroyAllWindows()
    print(f"\n\nTotal frames received: {frame_count}")
    print("Viewer closed.")

if __name__ == "__main__":
    main()
