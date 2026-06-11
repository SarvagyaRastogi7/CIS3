#!/usr/bin/env python3
"""Print the first available TCP port on 127.0.0.1, starting from a given port."""

from __future__ import annotations

import socket
import sys


def find_free_port(start: int = 8000, end: int = 8999) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No free port in range {start}-{end}")


if __name__ == "__main__":
    start_port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    end_port = int(sys.argv[2]) if len(sys.argv) > 2 else start_port + 999
    try:
        print(find_free_port(start_port, end_port))
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
