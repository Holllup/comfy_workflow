import unittest
from unittest.mock import patch


class _LargeResponse:
    headers = {}

    def __init__(self):
        self.read_bytes = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, count):
        self.read_bytes += count
        return b"x" * count


class NetworkPreflightTests(unittest.TestCase):
    def test_probe_reads_bounded_sample_instead_of_entire_model(self):
        from masterpiece_flight2.scripts import network_preflight

        response = _LargeResponse()
        with patch.object(network_preflight, "urlopen", return_value=response):
            count, elapsed = network_preflight.probe_url("https://example.com/model", max_bytes=64 * 1024, max_seconds=3)
        self.assertEqual(count, 64 * 1024)
        self.assertEqual(response.read_bytes, 64 * 1024)
        self.assertGreater(elapsed, 0)

    def test_projected_download_time_makes_slow_link_visible(self):
        from masterpiece_flight2.scripts.network_preflight import projected_hours

        self.assertGreater(projected_hours(62_000_000_000, 100_000), 100)
        self.assertLess(projected_hours(62_000_000_000, 10_000_000), 2)


if __name__ == "__main__":
    unittest.main()
