"""The size of an image, read from its header (png, gif, jpeg, webp, svg), with no libraries."""
from __future__ import annotations

import base64
import re
import struct


def _png(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        return struct.unpack(">II", data[16:24])


def _gif(data):
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", data[6:10])


def _jpeg(data):
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):    # a start-of-frame marker
            height, width = struct.unpack(">HH", data[i + 5:i + 9])
            return width, height
        i += 2 + length


def _webp(data):
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    kind = data[12:16]
    if kind == b"VP8X":
        return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
    if kind == b"VP8 ":
        width, height = struct.unpack("<HH", data[26:30])
        return width & 0x3FFF, height & 0x3FFF
    if kind == b"VP8L":
        bits = int.from_bytes(data[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1


def _svg(data):
    text = data[:4096].decode("utf-8", "ignore")
    tag = re.search(r"<svg\b[^>]*>", text)
    if not tag:
        return None
    tag = tag.group(0)
    box = re.search(r'viewBox\s*=\s*"\s*[-\d.]+[ ,]+[-\d.]+[ ,]+([\d.]+)[ ,]+([\d.]+)', tag)
    if box:
        return float(box.group(1)), float(box.group(2))
    width, height = (re.search(rf'\b{name}\s*=\s*"([\d.]+)', tag) for name in ("width", "height"))
    if width and height:
        return float(width.group(1)), float(height.group(1))


def image_size(data):
    """(width, height) of the image bytes, or None when the format is not known."""
    for reader in (_png, _gif, _jpeg, _webp, _svg):
        try:
            size = reader(data)
        except (struct.error, ValueError):
            size = None
        if size and size[0] > 0 and size[1] > 0:
            return size
    return None


def data_uri_size(uri):
    """(width, height) of the image in a data: URI, or None."""
    try:
        return image_size(base64.b64decode(uri.split(",", 1)[1]))
    except (IndexError, ValueError):
        return None
