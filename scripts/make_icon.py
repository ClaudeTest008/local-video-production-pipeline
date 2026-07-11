"""Generate the app icon (1024px PNG) with stdlib only — a tungsten tally
light on a slate frame, matching the studio theme. Run once; `tauri icon`
derives all platform sizes from the output."""

import math
import struct
import zlib


def png(width: int, height: int, rgba_rows: list[bytes]) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + row for row in rgba_rows)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


SIZE = 1024
BG = (16, 19, 24)  # slate
EDGE = (38, 44, 54)
AMBER = (232, 163, 61)
AMBER_DIM = (232, 163, 61)


def pixel(x: int, y: int) -> tuple[int, int, int, int]:
    cx, cy = SIZE / 2, SIZE / 2
    # rounded-square background
    rx, ry = abs(x - cx), abs(y - cy)
    radius = 200
    half = SIZE / 2
    inside = rx <= half - radius or ry <= half - radius or (
        (rx - (half - radius)) ** 2 + (ry - (half - radius)) ** 2 <= radius**2
    )
    if not inside:
        return (0, 0, 0, 0)
    # film-strip frames along the bottom
    if 780 <= y <= 850:
        frame = (x - 132) % 110
        if 0 <= frame <= 78 and 132 <= x <= 892:
            lit = 132 + 4 * 110 <= x <= 132 + 4 * 110 + 78  # one lit frame
            return (*(AMBER if lit else EDGE), 255)
    # tally-light dot with glow
    d = math.hypot(x - cx, y - cy - 60)
    if d <= 150:
        return (*AMBER, 255)
    if d <= 260:
        t = 1 - (d - 150) / 110
        return (
            int(BG[0] + (AMBER_DIM[0] - BG[0]) * t * 0.35),
            int(BG[1] + (AMBER_DIM[1] - BG[1]) * t * 0.35),
            int(BG[2] + (AMBER_DIM[2] - BG[2]) * t * 0.35),
            255,
        )
    return (*BG, 255)


rows = [
    b"".join(struct.pack("4B", *pixel(x, y)) for x in range(SIZE)) for y in range(SIZE)
]
with open("app-icon.png", "wb") as f:
    f.write(png(SIZE, SIZE, rows))
print("wrote app-icon.png")
