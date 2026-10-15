import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import time
import unittest

from cat_vlog_h3.scripts import ensure_models as downloader


PAYLOAD = (b"known-public-model-fixture-" * 4096)


class RangeHandler(BaseHTTPRequestHandler):
    requests_seen = []

    def log_message(self, *_args):
        pass

    def do_GET(self):
        self.requests_seen.append((self.path, self.headers.get("Range")))
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/range")
            self.end_headers()
            return
        if self.path == "/html":
            self.send_response(206)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html>not a model</html>")
            return
        value = self.headers.get("Range", "bytes=0-")
        start, _, end = value.removeprefix("bytes=").partition("-")
        start, end = int(start), int(end) if end else len(PAYLOAD) - 1
        data = PAYLOAD[start:end + 1]
        if self.path == "/ignore":
            data = PAYLOAD
            self.send_response(200)
        else:
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{len(PAYLOAD)}")
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            if self.path == "/slow":
                for offset in range(0, len(data), 256):
                    self.wfile.write(data[offset:offset+256])
                    self.wfile.flush()
                    time.sleep(0.1)
            else:
                self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass


class DownloadSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), RangeHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_audio_vae_verifier_rejects_same_size_with_wrong_content(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "audio.safetensors"
            good = b"verified-model"
            path.write_bytes(good)
            digest = hashlib.sha256(good).hexdigest()
            self.assertTrue(downloader.verify_audio_file(path, len(good), digest))
            path.write_bytes(b"corrupt!-model")
            self.assertFalse(downloader.verify_audio_file(path, len(good), digest))

    def test_probe_reads_bounded_range_and_rejects_non_model_or_unbounded_response(self):
        received, elapsed = downloader.probe_source(self.base + "/redirect", max_bytes=4096, max_seconds=2)
        self.assertEqual(received, 4096)
        self.assertGreater(elapsed, 0)
        for path in ("/html", "/ignore"):
            with self.assertRaises(RuntimeError):
                downloader.probe_source(self.base + path, max_bytes=4096, max_seconds=2)

    def test_probe_wall_clock_deadline_is_enforced_while_data_drips(self):
        start = time.monotonic()
        with self.assertRaises((RuntimeError, TimeoutError)):
            downloader.probe_source(self.base + "/slow", max_bytes=4096, max_seconds=0.4)
        self.assertLess(time.monotonic() - start, 0.9)

    def test_direct_transfer_resumes_same_url_then_verifies_before_install(self):
        self.assertTrue(hasattr(downloader, "fetch_verified"), "Need a direct transfer, without the ModelScope SDK")
        with tempfile.TemporaryDirectory() as temp:
            partial, destination = Path(temp) / "model.part", Path(temp) / "model.safetensors"
            partial.write_bytes(PAYLOAD[:2048])
            RangeHandler.requests_seen.clear()
            downloader.fetch_verified(self.base + "/range", partial, destination,
                                      expected_bytes=len(PAYLOAD), expected_sha256=hashlib.sha256(PAYLOAD).hexdigest(),
                                      min_bytes_per_second=1, max_seconds=3)
            self.assertEqual(destination.read_bytes(), PAYLOAD)
            self.assertIn(("/range", "bytes=2048-"), RangeHandler.requests_seen)
            self.assertFalse(partial.exists())

    def test_failed_checksum_does_not_replace_existing_destination(self):
        self.assertTrue(hasattr(downloader, "fetch_verified"))
        with tempfile.TemporaryDirectory() as temp:
            partial, destination = Path(temp) / "model.part", Path(temp) / "model.safetensors"
            destination.write_bytes(b"old model stays until a verified replacement")
            with self.assertRaisesRegex(RuntimeError, "SHA256"):
                downloader.fetch_verified(self.base + "/range", partial, destination,
                                          expected_bytes=len(PAYLOAD), expected_sha256="0" * 64,
                                          min_bytes_per_second=1, max_seconds=3)
            self.assertEqual(destination.read_bytes(), b"old model stays until a verified replacement")
            self.assertTrue(partial.exists())


if __name__ == "__main__":
    unittest.main()
