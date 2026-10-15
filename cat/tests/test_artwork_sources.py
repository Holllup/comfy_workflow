"""Tests for downloading a documented painting image and its source record."""

import importlib
from contextlib import redirect_stdout
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


STARRY_THUMB = (
    "https://thumb.wikimedia.org/wikipedia/commons/thumb/e/ea/"
    "Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/"
    "3840px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg"
)


class FakeOpener:
    def __init__(self, responses):
        self.responses = responses
        self.requested = []

    def __call__(self, request):
        url = request.full_url if hasattr(request, "full_url") else request
        self.requested.append(url)
        if urlsplit(url).path == "/w/api.php":
            return io.BytesIO(json.dumps(self.responses["mediawiki"]).encode())
        if url in self.responses:
            return io.BytesIO(self.responses[url])
        raise AssertionError(f"Unexpected HTTP request: {url}")


class ArtworkSourcesTests(unittest.TestCase):
    def test_starry_night_downloads_3840_thumb_and_source_manifest(self):
        # Catches using the 664 MB original or omitting the rights/source record.
        try:
            sources = importlib.import_module("masterpiece_flight.artwork_sources")
        except ModuleNotFoundError as exc:
            self.fail(f"artwork download module is missing: {exc}")
        api_reply = {
            "query": {"pages": {"123": {"title": "File:Van Gogh - Starry Night - Google Art Project.jpg", "imageinfo": [{
                "url": "https://upload.wikimedia.org/wikipedia/commons/e/ea/original.jpg",
                "thumburl": STARRY_THUMB,
                "thumbwidth": 3840,
                "thumbheight": 3041,
                "extmetadata": {
                    "LicenseShortName": {"value": "Public domain"},
                    "License": {"value": "pd"},
                    "Copyrighted": {"value": "False"},
                },
            }]}}}
        }
        opener = FakeOpener({"mediawiki": api_reply, STARRY_THUMB: b"small-jpeg"})

        with tempfile.TemporaryDirectory() as directory:
            sources.fetch_starry_night(directory, opener=opener)
            output = Path(directory)
            self.assertEqual((output / "starry_night.jpg").read_bytes(), b"small-jpeg")
            manifest = json.loads((output / "manifest.json").read_text())

        query = parse_qs(urlsplit(opener.requested[0]).query)
        self.assertEqual(query["iiurlwidth"], ["3840"])
        self.assertEqual(opener.requested[1:], [STARRY_THUMB])
        self.assertEqual(manifest["artwork"]["title"], "The Starry Night")
        self.assertEqual(manifest["rights"]["label"], "Public domain")
        self.assertEqual(manifest["source"]["file_url"], "https://commons.wikimedia.org/wiki/File:Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg")
        self.assertEqual(manifest["image"]["url"], STARRY_THUMB)

    def test_met_downloads_public_domain_image_and_manifest(self):
        # Catches choosing a preview over the original image or losing source data.
        sources = importlib.import_module("masterpiece_flight.artwork_sources")
        self.assertTrue(hasattr(sources, "fetch_met_artwork"), "The Met downloader is missing")
        api_url = "https://collectionapi.metmuseum.org/public/collection/v1/objects/436535"
        image_url = "https://images.metmuseum.org/CRDImages/ep/original/DT1567.jpg"
        opener = FakeOpener({
            api_url: json.dumps({
                "objectID": 436535,
                "isPublicDomain": True,
                "primaryImage": image_url,
                "primaryImageSmall": "https://images.metmuseum.org/CRDImages/ep/web-large/DT1567.jpg",
                "title": "Wheat Field with Cypresses",
                "artistDisplayName": "Vincent van Gogh",
                "objectDate": "1889",
                "objectURL": "https://www.metmuseum.org/art/collection/search/436535",
                "accessionNumber": "1993.132",
                "rightsAndReproduction": "",
            }).encode(),
            image_url: b"met-jpeg",
        })

        with tempfile.TemporaryDirectory() as directory:
            sources.fetch_met_artwork(436535, directory, opener=opener)
            output = Path(directory)
            self.assertEqual((output / "met_436535.jpg").read_bytes(), b"met-jpeg")
            manifest = json.loads((output / "manifest.json").read_text())

        self.assertEqual(opener.requested, [api_url, image_url])
        self.assertEqual(manifest["artwork"]["title"], "Wheat Field with Cypresses")
        self.assertEqual(manifest["artwork"]["artist"], "Vincent van Gogh")
        self.assertEqual(manifest["source"]["object_url"], "https://www.metmuseum.org/art/collection/search/436535")
        self.assertEqual(manifest["rights"]["label"], "Public domain / The Met Open Access")

    def test_met_rejects_non_public_domain_before_downloading(self):
        # Catches a copyright check being skipped before image retrieval.
        sources = importlib.import_module("masterpiece_flight.artwork_sources")
        api_url = "https://collectionapi.metmuseum.org/public/collection/v1/objects/100"
        image_url = "https://images.metmuseum.org/CRDImages/ep/original/restricted.jpg"
        opener = FakeOpener({
            api_url: json.dumps({
                "objectID": 100,
                "isPublicDomain": False,
                "primaryImage": image_url,
            }).encode(),
            image_url: b"restricted-jpeg",
        })

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(sources.ArtworkSourceError):
                sources.fetch_met_artwork(100, Path(directory) / "result", opener=opener)
            self.assertFalse((Path(directory) / "result").exists())
        self.assertEqual(opener.requested, [api_url])

    def test_met_rejects_missing_image_with_clear_reason(self):
        # Catches attempting a request for an empty primary-image field.
        sources = importlib.import_module("masterpiece_flight.artwork_sources")
        api_url = "https://collectionapi.metmuseum.org/public/collection/v1/objects/101"
        opener = FakeOpener({
            api_url: json.dumps({
                "objectID": 101,
                "isPublicDomain": True,
                "primaryImage": "",
                "primaryImageSmall": "https://images.metmuseum.org/CRDImages/ep/web-large/preview.jpg",
            }).encode(),
        })

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(sources.ArtworkSourceError, "no Open Access primary image"):
                sources.fetch_met_artwork(101, Path(directory) / "result", opener=opener)
            self.assertFalse((Path(directory) / "result").exists())
        self.assertEqual(opener.requested, [api_url])

    def test_met_cli_writes_requested_object(self):
        # Catches a CLI command that parses the ID but never downloads its image.
        sources = importlib.import_module("masterpiece_flight.artwork_sources")
        self.assertTrue(hasattr(sources, "main"), "Artwork downloader CLI is missing")
        api_url = "https://collectionapi.metmuseum.org/public/collection/v1/objects/436535"
        image_url = "https://images.metmuseum.org/CRDImages/ep/original/DT1567.jpg"
        opener = FakeOpener({
            api_url: json.dumps({"objectID": 436535, "isPublicDomain": True, "primaryImage": image_url}).encode(),
            image_url: b"met-jpeg",
        })

        with tempfile.TemporaryDirectory() as directory:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = sources.main(["met", "436535", directory], opener=opener)
            self.assertEqual(exit_code, 0)
            self.assertEqual((Path(directory) / "met_436535.jpg").read_bytes(), b"met-jpeg")
            self.assertIn("manifest.json", stdout.getvalue())

    def test_starry_night_cli_uses_its_documented_file(self):
        # Catches routing the Commons command to the wrong source or asset.
        sources = importlib.import_module("masterpiece_flight.artwork_sources")
        self.assertTrue(hasattr(sources, "main"), "Artwork downloader CLI is missing")
        api_reply = {"query": {"pages": {"123": {"imageinfo": [{
            "thumburl": STARRY_THUMB,
            "thumbwidth": 3840,
            "thumbheight": 3041,
            "extmetadata": {
                "LicenseShortName": {"value": "Public domain"},
                "License": {"value": "pd"},
                "Copyrighted": {"value": "False"},
            },
        }]}}}}
        opener = FakeOpener({"mediawiki": api_reply, STARRY_THUMB: b"starry-jpeg"})

        with tempfile.TemporaryDirectory() as directory:
            with redirect_stdout(io.StringIO()):
                exit_code = sources.main(["starry-night", directory], opener=opener)
            self.assertEqual(exit_code, 0)
            self.assertEqual((Path(directory) / "starry_night.jpg").read_bytes(), b"starry-jpeg")


if __name__ == "__main__":
    unittest.main()
