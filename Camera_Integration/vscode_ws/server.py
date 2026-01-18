import argparse
import socket
import struct
import time


HOST = "0.0.0.0"
PORT = 5000
INTERVAL = 0.1


def build_packet(sequence: int) -> bytes:
    payload = f"dummy frame {sequence}".encode("utf-8")
    length_prefix = struct.pack("!I", len(payload))
    return length_prefix + payload


def stream_dummy_data(host: str, port: int, interval: float, iterations: int | None) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"Listening for client on {host}:{port}")

    data, addr = sock.recvfrom(1024)
    print(f"Client registered from {addr}")

    sequence = 0
    try:
        while True:
            packet = build_packet(sequence)
            sock.sendto(packet, addr)
            sequence += 1
            if iterations is not None and sequence >= iterations:
                break
            time.sleep(interval)
    finally:
        sock.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--interval", type=float, default=INTERVAL)
    parser.add_argument("--iterations", type=int, default=0)
    args = parser.parse_args()

    iterations: int | None = args.iterations if args.iterations > 0 else None
    stream_dummy_data(args.host, args.port, args.interval, iterations)


if __name__ == "__main__":
    main()

