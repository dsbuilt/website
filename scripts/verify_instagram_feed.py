#!/usr/bin/env python3
"""Verify that feed.html matches the latest Instagram posts and downloaded images."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from update_instagram_feed import (
    DEFAULT_LIMIT,
    END_MARKER,
    FEED_HTML,
    ROOT,
    START_MARKER,
    fetch_latest_posts,
    load_posts_from_fixture,
    select_feed_posts,
)


FEED_ITEM_PATTERN = re.compile(
    r'<a class="feed-item" href="(?P<href>[^"]+)"[^>]*>.*?<img src="(?P<src>[^"]+)"',
    re.DOTALL,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that feed.html matches the latest Instagram posts and images."
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Use a local JSON response fixture instead of calling the Instagram Graph API.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Expected number of feed items to validate (default: {DEFAULT_LIMIT}).",
    )
    return parser.parse_args()


def get_generated_block(document: str) -> str:
    start = document.find(START_MARKER)
    end = document.find(END_MARKER)
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError("Could not find instagram feed markers in feed.html.")

    return document[start + len(START_MARKER) : end]


def parse_feed_items(document: str) -> list[dict[str, str]]:
    block = get_generated_block(document)
    items = [
        {"permalink": match.group("href"), "image_path": match.group("src")}
        for match in FEED_ITEM_PATTERN.finditer(block)
    ]
    if not items:
        raise RuntimeError("No feed items were found between the instagram feed markers.")
    return items


def fetch_binary(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "DSBuiltInstagramFeedBot/1.0"})

    try:
        with urlopen(request) as response:
            return response.read()
    except HTTPError as error:
        payload = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Image verification download failed ({error.code}): {payload}") from error
    except URLError as error:
        raise RuntimeError(f"Image verification download failed: {error.reason}") from error


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_items(expected_items: list[dict[str, str]], actual_items: list[dict[str, str]]) -> None:
    if len(actual_items) != len(expected_items):
        raise RuntimeError(
            f"Feed item count mismatch: expected {len(expected_items)}, found {len(actual_items)}."
        )

    for index, (expected, actual) in enumerate(zip(expected_items, actual_items, strict=True), start=1):
        if actual["permalink"] != expected["permalink"]:
            raise RuntimeError(
                f"Feed item {index} permalink mismatch: expected {expected['permalink']}, "
                f"found {actual['permalink']}."
            )

        local_image = ROOT / actual["image_path"]
        if not local_image.is_file():
            raise RuntimeError(f"Feed item {index} image is missing: {local_image}")

        local_hash = sha256_bytes(local_image.read_bytes())
        remote_hash = sha256_bytes(fetch_binary(expected["image_url"]))
        if local_hash != remote_hash:
            raise RuntimeError(
                f"Feed item {index} image bytes do not match the latest Instagram media for "
                f"{expected['permalink']}."
            )


def main() -> None:
    args = parse_args()
    raw_posts = (
        load_posts_from_fixture(args.fixture)
        if args.fixture
        else fetch_latest_posts(args.limit)
    )
    expected_items = select_feed_posts(raw_posts, args.limit)
    actual_items = parse_feed_items(FEED_HTML.read_text(encoding="utf-8"))
    verify_items(expected_items, actual_items)
    print(f"Verified {len(actual_items)} feed items against the latest Instagram posts.")


if __name__ == "__main__":
    main()
