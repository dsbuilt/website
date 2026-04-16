#!/usr/bin/env python3
"""Refresh feed.html with the latest posts from the DSBuilt Instagram account."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
FEED_HTML = ROOT / "feed.html"
FEED_IMAGE_DIR = ROOT / "images" / "feed"
START_MARKER = "<!-- instagram-feed:start -->"
END_MARKER = "<!-- instagram-feed:end -->"
GRAPH_API_BASE = os.environ.get("INSTAGRAM_GRAPH_API_BASE", "https://graph.facebook.com/v23.0")
DEFAULT_LIMIT = 9
SVG_OVERLAY = (
    '<span class="feed-item-overlay"><svg viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
    'stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" />'
    '<circle cx="12" cy="12" r="5" /><circle cx="17.5" cy="6.5" r="1.5" '
    'fill="currentColor" stroke="none" /></svg></span>'
)
EXTENSIONS_BY_CONTENT_TYPE = {
    "image/avif": ".avif",
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update feed.html and images/feed from the latest Instagram posts."
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Use a local JSON response fixture instead of calling the Instagram Graph API.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=int(os.environ.get("INSTAGRAM_FEED_LIMIT", DEFAULT_LIMIT)),
        help=f"Maximum number of posts to publish on the feed page (default: {DEFAULT_LIMIT}).",
    )
    return parser.parse_args()


def fetch_json(url: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "DSBuiltInstagramFeedBot/1.0",
        },
    )

    try:
        with urlopen(request) as response:
            return json.load(response)
    except HTTPError as error:
        payload = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Instagram API request failed ({error.code}): {payload}") from error
    except URLError as error:
        raise RuntimeError(f"Instagram API request failed: {error.reason}") from error


def load_posts_from_fixture(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            return data
    raise RuntimeError("Fixture must be a JSON array or an object with a top-level 'data' array.")


def fetch_latest_posts(limit: int) -> list[dict[str, Any]]:
    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    user_id = os.environ.get("INSTAGRAM_USER_ID")

    if not access_token or not user_id:
        raise RuntimeError(
            "Missing required environment variables INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID."
        )

    fields = ",".join(
        [
            "id",
            "caption",
            "media_type",
            "media_url",
            "permalink",
            "thumbnail_url",
            "timestamp",
            "children{media_type,media_url,thumbnail_url}",
        ]
    )
    params = {
        "access_token": access_token,
        "fields": fields,
        "limit": max(limit * 3, limit),
    }
    url = f"{GRAPH_API_BASE.rstrip('/')}/{user_id}/media?{urlencode(params)}"
    posts: list[dict[str, Any]] = []

    while url and len(posts) < limit * 3:
        payload = fetch_json(url)
        posts.extend(item for item in payload.get("data", []) if isinstance(item, dict))
        url = payload.get("paging", {}).get("next")

    return posts


def pick_image_url(post: dict[str, Any]) -> str | None:
    media_type = post.get("media_type")

    if media_type == "VIDEO":
        return post.get("thumbnail_url") or post.get("media_url")

    if media_type in {"IMAGE", "CAROUSEL_ALBUM"} and post.get("media_url"):
        return post["media_url"]

    children = post.get("children", {}).get("data", [])
    for child in children:
        if not isinstance(child, dict):
            continue
        child_type = child.get("media_type")
        if child_type == "VIDEO" and child.get("thumbnail_url"):
            return child["thumbnail_url"]
        if child.get("media_url"):
            return child["media_url"]

    return None


def guess_extension(content_type: str | None, source_url: str) -> str:
    if content_type:
        stripped = content_type.split(";", 1)[0].strip().lower()
        if stripped in EXTENSIONS_BY_CONTENT_TYPE:
            return EXTENSIONS_BY_CONTENT_TYPE[stripped]

    parsed = urlparse(source_url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix in {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}:
        return ".jpg" if suffix == ".jpeg" else suffix

    return ".jpg"


def clear_slot(slot: int, keep: Path | None = None) -> None:
    for candidate in FEED_IMAGE_DIR.glob(f"feed-{slot}.*"):
        if keep and candidate == keep:
            continue
        candidate.unlink()


def download_image(source_url: str, slot: int) -> str:
    request = Request(
        source_url,
        headers={"User-Agent": "DSBuiltInstagramFeedBot/1.0"},
    )

    try:
        with urlopen(request) as response:
            payload = response.read()
            content_type = response.headers.get("Content-Type")
    except HTTPError as error:
        response_body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Image download failed ({error.code}): {response_body}") from error
    except URLError as error:
        raise RuntimeError(f"Image download failed: {error.reason}") from error

    extension = guess_extension(content_type, source_url)
    destination = FEED_IMAGE_DIR / f"feed-{slot}{extension}"
    FEED_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    clear_slot(slot, keep=destination)
    destination.write_bytes(payload)
    return destination.relative_to(ROOT).as_posix()


def cleanup_unused_slots(used_slots: set[int]) -> None:
    pattern = re.compile(r"feed-(\d+)\.[A-Za-z0-9]+$")
    for candidate in FEED_IMAGE_DIR.glob("feed-*.*"):
        match = pattern.fullmatch(candidate.name)
        if match and int(match.group(1)) not in used_slots:
            candidate.unlink()


def normalise_caption(value: Any) -> str:
    if not isinstance(value, str):
        return "Instagram post from DSBuilt"

    collapsed = " ".join(value.split())
    if not collapsed:
        return "Instagram post from DSBuilt"
    if len(collapsed) > 110:
        return f"{collapsed[:107].rstrip()}..."
    return collapsed


def render_feed_items(posts: list[dict[str, str]]) -> str:
    lines: list[str] = []

    for post in posts:
        permalink = html.escape(post["permalink"], quote=True)
        image_path = html.escape(post["image_path"], quote=True)
        alt_text = html.escape(post["alt"], quote=True)

        lines.extend(
            [
                f'          <a class="feed-item" href="{permalink}" target="_blank" rel="noopener">',
                f'            <img src="{image_path}" alt="{alt_text}" loading="lazy" />',
                f"            {SVG_OVERLAY}",
                "          </a>",
            ]
        )

    return "\n".join(lines)


def replace_generated_block(document: str, replacement: str) -> str:
    marker_pattern = re.compile(
        rf"(?P<start>[ \t]*{re.escape(START_MARKER)}\n)(?P<body>.*?)(?P<end>[ \t]*{re.escape(END_MARKER)})",
        re.DOTALL,
    )
    match = marker_pattern.search(document)
    if not match:
        raise RuntimeError("Could not find instagram feed markers in feed.html.")

    return f"{document[:match.start()]}{match.group('start')}{replacement}\n{match.group('end')}{document[match.end():]}"


def build_feed_posts(raw_posts: list[dict[str, Any]], limit: int) -> list[dict[str, str]]:
    rendered_posts: list[dict[str, str]] = []
    used_slots: set[int] = set()

    for raw_post in raw_posts:
        if len(rendered_posts) >= limit:
            break

        permalink = raw_post.get("permalink")
        image_url = pick_image_url(raw_post)
        if not permalink or not image_url:
            continue

        slot = len(rendered_posts) + 1
        image_path = download_image(image_url, slot)
        used_slots.add(slot)
        rendered_posts.append(
            {
                "alt": normalise_caption(raw_post.get("caption")),
                "image_path": image_path,
                "permalink": permalink,
            }
        )

    cleanup_unused_slots(used_slots)

    if not rendered_posts:
        raise RuntimeError("No Instagram posts with usable media were returned.")

    return rendered_posts


def main() -> None:
    args = parse_args()
    raw_posts = (
        load_posts_from_fixture(args.fixture)
        if args.fixture
        else fetch_latest_posts(args.limit)
    )
    rendered_posts = build_feed_posts(raw_posts, args.limit)
    replacement = render_feed_items(rendered_posts)
    updated_document = replace_generated_block(FEED_HTML.read_text(encoding="utf-8"), replacement)
    FEED_HTML.write_text(updated_document, encoding="utf-8")
    print(f"Updated feed.html with {len(rendered_posts)} Instagram posts.")


if __name__ == "__main__":
    main()
