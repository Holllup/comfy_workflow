"""Download openly documented painting images for a ComfyUI reference frame."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


COMMONS_FILE = "File:Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg"
COMMONS_PAGE = "https://commons.wikimedia.org/wiki/" + COMMONS_FILE
MOMA_PAGE = "https://www.moma.org/collection/works/79802"
MET_API = "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
USER_AGENT = "masterpiece-flight/1.0 (artwork image provenance downloader)"


class ArtworkSourceError(ValueError):
    """The source record does not license or provide the requested image."""


def _request(url: str) -> Request:
    return Request(url, headers={"User-Agent": USER_AGENT})


def _read_json(url: str, opener):
    with opener(_request(url)) as response:
        return json.load(response)


def _download(url: str, destination: Path, opener):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            with opener(_request(url)) as response:
                shutil.copyfileobj(response, temporary)
        except BaseException:
            temporary_path.unlink(missing_ok=True)
            raise
    os.replace(temporary_path, destination)


def _save_manifest(destination: Path, manifest: dict):
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def fetch_starry_night(output_dir: str | Path, opener=urlopen) -> dict:
    """Fetch the 3840 px Commons thumbnail of MoMA's *The Starry Night*."""
    metadata_url = "https://commons.wikimedia.org/w/api.php?" + urlencode({
        "action": "query",
        "titles": COMMONS_FILE,
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata",
        "iiurlwidth": 3840,
        "format": "json",
    })
    metadata = _read_json(metadata_url, opener)
    try:
        page = next(iter(metadata["query"]["pages"].values()))
        image_info = page["imageinfo"][0]
        image_url = image_info["thumburl"]
        width = image_info["thumbwidth"]
        height = image_info["thumbheight"]
        rights = image_info["extmetadata"]
        label = rights["LicenseShortName"]["value"]
        license_code = rights["License"]["value"]
        copyrighted = rights["Copyrighted"]["value"]
    except (KeyError, IndexError, StopIteration, TypeError) as exc:
        raise ArtworkSourceError("Commons did not provide a usable 3840 px image record") from exc
    if width < 3840 or license_code.lower() != "pd" or copyrighted.lower() != "false":
        raise ArtworkSourceError("Commons image is too small or no longer marked public domain")
    if urlsplit(image_url).scheme != "https" or urlsplit(image_url).hostname not in {
        "thumb.wikimedia.org", "upload.wikimedia.org"
    }:
        raise ArtworkSourceError("Commons returned an unexpected image host")

    output = Path(output_dir)
    _download(image_url, output / "starry_night.jpg", opener)
    manifest = {
        "artwork": {
            "title": "The Starry Night",
            "artist": "Vincent van Gogh",
            "year": 1889,
            "holding_institution": "Museum of Modern Art",
            "accession_number": "472.1941",
        },
        "source": {
            "provider": "Wikimedia Commons",
            "file_url": COMMONS_PAGE,
            "object_url": MOMA_PAGE,
            "metadata_url": metadata_url,
        },
        "rights": {
            "label": label,
            "source_url": COMMONS_PAGE,
            "note": "Commons' PD-Art assessment; check reuse rules in your jurisdiction.",
        },
        "image": {
            "file": "starry_night.jpg",
            "url": image_url,
            "width": width,
            "height": height,
        },
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    return _save_manifest(output / "manifest.json", manifest)


def fetch_met_artwork(object_id: int, output_dir: str | Path, opener=urlopen) -> dict:
    """Fetch a known, public-domain Met object and its original JPEG."""
    if isinstance(object_id, bool) or not isinstance(object_id, int) or object_id <= 0:
        raise ArtworkSourceError("The Met object ID must be a positive integer")
    api_url = MET_API + str(object_id)
    record = _read_json(api_url, opener)
    if record.get("objectID") != object_id:
        raise ArtworkSourceError("The Met returned a different object record")
    if record.get("isPublicDomain") is not True:
        raise ArtworkSourceError("The Met object is not marked public domain")
    image_url = record.get("primaryImage")
    if not image_url:
        raise ArtworkSourceError("The Met object has no Open Access primary image")
    if urlsplit(image_url).scheme != "https" or urlsplit(image_url).hostname != "images.metmuseum.org":
        raise ArtworkSourceError("The Met returned an unexpected image host")

    output = Path(output_dir)
    file_name = f"met_{object_id}.jpg"
    _download(image_url, output / file_name, opener)
    manifest = {
        "artwork": {
            "title": record.get("title"),
            "artist": record.get("artistDisplayName"),
            "date": record.get("objectDate"),
            "holding_institution": "The Metropolitan Museum of Art",
            "accession_number": record.get("accessionNumber"),
            "object_id": object_id,
        },
        "source": {
            "provider": "The Met Open Access",
            "object_url": record.get("objectURL"),
            "metadata_url": api_url,
        },
        "rights": {
            "label": "Public domain / The Met Open Access",
            "source_url": "https://metmuseum.github.io/",
            "museum_rights_and_reproduction": record.get("rightsAndReproduction"),
        },
        "image": {
            "file": file_name,
            "url": image_url,
        },
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    return _save_manifest(output / "manifest.json", manifest)


def main(argv: list[str] | None = None, opener=urlopen) -> int:
    """Run ``starry-night OUTPUT_DIR`` or ``met OBJECT_ID OUTPUT_DIR``."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="source", required=True)
    starry = commands.add_parser("starry-night", help="Fetch the 3840 px Commons image")
    starry.add_argument("output_dir")
    met = commands.add_parser("met", help="Fetch one public-domain Met object")
    met.add_argument("object_id", type=int)
    met.add_argument("output_dir")
    args = parser.parse_args(argv)

    if args.source == "starry-night":
        fetch_starry_night(args.output_dir, opener=opener)
    else:
        fetch_met_artwork(args.object_id, args.output_dir, opener=opener)
    print(Path(args.output_dir) / "manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
