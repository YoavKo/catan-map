import base64
import struct
import unittest

from catan_map.imagesize import data_uri_size, image_size


class ImageSize(unittest.TestCase):
    def test_png(self):
        png = bytes.fromhex("89504e470d0a1a0a0000000d49484452") + struct.pack(">II", 480, 160) + b"\x08\x06\x00\x00\x00"
        self.assertEqual(image_size(png), (480, 160))

    def test_gif(self):
        self.assertEqual(image_size(b"GIF89a" + struct.pack("<HH", 300, 200) + b"\x00" * 10), (300, 200))

    def test_jpeg(self):
        jpeg = b"\xff\xd8" + b"\xff\xe0\x00\x04\x00\x00" + b"\xff\xc0\x00\x11\x08" + struct.pack(">HH", 200, 640) + b"\x03" + b"\x00" * 9
        self.assertEqual(image_size(jpeg), (640, 200))                     # (width, height)

    def test_webp_extended(self):
        webp = b"RIFF\x00\x00\x00\x00WEBPVP8X" + b"\x0a\x00\x00\x00" + b"\x00" * 4 + (319).to_bytes(3, "little") + (99).to_bytes(3, "little")
        self.assertEqual(image_size(webp), (320, 100))

    def test_svg(self):
        self.assertEqual(image_size(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 40"></svg>'), (120, 40))
        self.assertEqual(image_size(b'<?xml version="1.0"?><svg width="50" height="25"></svg>'), (50, 25))

    def test_unknown_gives_none(self):
        self.assertIsNone(image_size(b"not an image"))
        self.assertIsNone(data_uri_size("data:image/png;base64,@@@"))
        self.assertIsNone(data_uri_size("nonsense"))

    def test_data_uri(self):
        png = bytes.fromhex("89504e470d0a1a0a0000000d49484452") + struct.pack(">II", 10, 20) + b"\x08\x06\x00\x00\x00"
        self.assertEqual(data_uri_size("data:image/png;base64," + base64.b64encode(png).decode()), (10, 20))


if __name__ == "__main__":
    unittest.main()
