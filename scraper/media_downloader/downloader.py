"""
Media Downloader – Playwright-based automation
===============================================
Reads YouTube / Instagram URLs from a text file and downloads them as
audio (MP3-320) or video (1080p+) by automating free converter websites.

Supported sites:
    YouTube  audio  → ytmp3.sc
    YouTube  video  → app.ytdown.to/en8/
    Instagram audio → indownloader.app/download-instagram-audio
    Instagram video → snapinsta.to/en2

Input file format (one entry per line):
    <url>                       # default: audio
    <url> audio
    <url> video

Lines starting with '#' are comments.  A trailing " ✓" marks a completed
download – the script appends it automatically.
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

from playwright.async_api import (
    Download,
    Page,
    Route,
    async_playwright,
)

log = logging.getLogger(__name__)

DONE_MARKER = " ✓"

Platform = Literal["youtube", "instagram"]
Format = Literal["audio", "video"]


@dataclass
class MediaTask:
    url: str
    fmt: Format
    platform: Platform
    line_index: int
    raw_line: str


# ---------------------------------------------------------------------------
# URL classification
# ---------------------------------------------------------------------------
_YT_RE = re.compile(
    r"(youtube\.com/|youtu\.be/|youtube\.com/shorts/)", re.IGNORECASE
)
_IG_RE = re.compile(
    r"(instagram\.com/)", re.IGNORECASE
)


def classify_url(url: str) -> Platform | None:
    if _YT_RE.search(url):
        return "youtube"
    if _IG_RE.search(url):
        return "instagram"
    return None


# ---------------------------------------------------------------------------
# Input-file parsing
# ---------------------------------------------------------------------------
def _normalise_url(url: str) -> str:
    """Strip tracking params and normalise encoding so duplicates are caught."""
    url = url.split("?")[0].rstrip("/")
    return url.lower()


def parse_links_file(path: Path) -> list[MediaTask]:
    tasks: list[MediaTask] = []
    seen: set[str] = set()
    lines = path.read_text(encoding="utf-8").splitlines()

    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not line or line.startswith("#") or DONE_MARKER.strip() in line:
            continue

        parts = line.split()
        url = parts[0]
        fmt: Format = "audio"
        if len(parts) > 1 and parts[1].lower() in ("audio", "video"):
            fmt = parts[1].lower()  # type: ignore[assignment]

        norm = _normalise_url(url)
        if norm in seen:
            log.info("Skipping duplicate URL: %s", url)
            continue
        seen.add(norm)

        platform = classify_url(url)
        if platform is None:
            log.warning("Skipping unrecognised URL: %s", url)
            continue

        tasks.append(
            MediaTask(
                url=url,
                fmt=fmt,
                platform=platform,
                line_index=idx,
                raw_line=raw,
            )
        )

    return tasks


def mark_done(links_file: Path, line_index: int) -> None:
    lines = links_file.read_text(encoding="utf-8").splitlines()
    if 0 <= line_index < len(lines):
        if not lines[line_index].rstrip().endswith(DONE_MARKER.strip()):
            lines[line_index] = lines[line_index].rstrip() + DONE_MARKER
        links_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
async def _wait_and_click(page: Page, selector: str, timeout: int = 15_000) -> None:
    btn = page.locator(selector).first
    await btn.wait_for(state="visible", timeout=timeout)
    await btn.click()


async def _dismiss_popups(page: Page) -> None:
    """Close common overlay ads / cookie banners if present."""
    for sel in [
        "button:has-text('Accept')",
        "button:has-text('Close')",
        "button:has-text('No thanks')",
        "button:has-text('I agree')",
        "[class*='close']",
        "[aria-label='Close']",
    ]:
        try:
            loc = page.locator(sel).first
            await loc.wait_for(state="visible", timeout=800)
            await loc.click()
            await asyncio.sleep(0.3)
        except Exception:
            pass


async def _wait_for_download(page: Page, action, timeout: float = 180) -> Download | None:
    """
    Perform *action* (an async callable that triggers a download) and
    return the resulting Download object, or None on timeout.
    """
    try:
        async with page.expect_download(timeout=timeout * 1000) as dl_info:
            await action()
        return dl_info.value
    except Exception as exc:
        log.error("Download did not start: %s", exc)
        return None


async def _save_download(download: Download, dest_dir: Path, preferred_ext: str | None = None) -> Path | None:
    try:
        suggested = download.suggested_filename
        if preferred_ext and not suggested.endswith(preferred_ext):
            stem = Path(suggested).stem
            suggested = f"{stem}{preferred_ext}"

        dest = dest_dir / suggested
        counter = 1
        while dest.exists():
            dest = dest_dir / f"{Path(suggested).stem}_{counter}{Path(suggested).suffix}"
            counter += 1

        await download.save_as(str(dest))
        log.info("Saved: %s", dest)
        return dest
    except Exception as exc:
        log.error("Failed to save download: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Site handlers
# ---------------------------------------------------------------------------

# -- YouTube MP3  (ytmp3.sc) -----------------------------------------------
async def _download_yt_audio(page: Page, url: str, dest_dir: Path) -> Path | None:
    """Automate ytmp3.sc to convert a YouTube URL to MP3."""
    await page.goto("https://ytmp3.sc/", wait_until="domcontentloaded")
    await asyncio.sleep(2)
    await _dismiss_popups(page)

    input_sel = "input[type='text'], input[type='search'], input[type='url'], #input"
    await page.locator(input_sel).first.wait_for(state="visible", timeout=10_000)
    await page.locator(input_sel).first.fill(url)
    await asyncio.sleep(0.5)

    try:
        mp3_btn = page.locator("button:has-text('MP3'), #mp3, [data-type='mp3']").first
        await mp3_btn.wait_for(state="visible", timeout=3_000)
        await mp3_btn.click()
        await asyncio.sleep(0.3)
    except Exception:
        pass

    convert_btn = page.locator(
        "button:has-text('Convert'), button:has-text('Download'), "
        "#convertBtn, #submit, button[type='submit']"
    ).first
    await convert_btn.click()

    # Wait for conversion – poll for a download/result link
    log.info("Waiting for conversion (ytmp3.sc) …")
    dl_link = page.locator(
        "a:has-text('Download'), a[href*='download'], "
        "button:has-text('Download'), #downloadBtn"
    ).first

    await dl_link.wait_for(state="visible", timeout=120_000)
    await asyncio.sleep(1)
    await _dismiss_popups(page)

    download = await _wait_for_download(page, dl_link.click)
    if download:
        return await _save_download(download, dest_dir, ".mp3")
    return None


# -- YouTube Video  (app.ytdown.to) ----------------------------------------
async def _download_yt_video(page: Page, url: str, dest_dir: Path) -> Path | None:
    """Automate app.ytdown.to to download YouTube video in best quality."""
    await page.goto("https://app.ytdown.to/en8/", wait_until="domcontentloaded")
    await asyncio.sleep(2)
    await _dismiss_popups(page)

    input_sel = "input[type='text'], input[type='search'], input[type='url'], #url"
    await page.locator(input_sel).first.wait_for(state="visible", timeout=10_000)
    await page.locator(input_sel).first.fill(url)
    await asyncio.sleep(0.5)

    dl_btn = page.locator(
        "button:has-text('Download'), #download, button[type='submit']"
    ).first
    await dl_btn.click()

    log.info("Waiting for format options (ytdown.to) …")
    await asyncio.sleep(5)
    await _dismiss_popups(page)

    # Look for 1080p or the highest quality option
    quality_selectors = [
        "a:has-text('1080')",
        "button:has-text('1080')",
        "a:has-text('720')",
        "button:has-text('720')",
        "a:has-text('MP4')",
    ]

    dl_element = None
    for sel in quality_selectors:
        try:
            loc = page.locator(sel).first
            await loc.wait_for(state="visible", timeout=5_000)
            dl_element = loc
            break
        except Exception:
            continue

    if dl_element is None:
        # Fallback: click any download link
        dl_element = page.locator(
            "a:has-text('Download'), button:has-text('Download')"
        ).first

    await dl_element.wait_for(state="visible", timeout=60_000)
    download = await _wait_for_download(page, dl_element.click)
    if download:
        return await _save_download(download, dest_dir, ".mp4")
    return None


# -- Instagram MP3  (indownloader.app) -------------------------------------
async def _download_ig_audio(page: Page, url: str, dest_dir: Path) -> Path | None:
    """Automate indownloader.app to extract audio from an Instagram post."""
    await page.goto(
        "https://indownloader.app/download-instagram-audio",
        wait_until="domcontentloaded",
    )
    await asyncio.sleep(2)
    await _dismiss_popups(page)

    input_sel = "input[type='text'], input[type='search'], input[type='url'], #url"
    await page.locator(input_sel).first.wait_for(state="visible", timeout=10_000)
    await page.locator(input_sel).first.fill(url)
    await asyncio.sleep(0.5)

    dl_btn = page.locator(
        "button:has-text('Download'), #download, button[type='submit']"
    ).first
    await dl_btn.click()

    log.info("Waiting for audio extraction (indownloader.app) …")
    await asyncio.sleep(5)
    await _dismiss_popups(page)

    result_link = page.locator(
        "a:has-text('Download'), a[href*='.mp3'], "
        "button:has-text('Download MP3'), a:has-text('MP3')"
    ).first

    await result_link.wait_for(state="visible", timeout=120_000)
    await asyncio.sleep(1)
    await _dismiss_popups(page)

    download = await _wait_for_download(page, result_link.click)
    if download:
        return await _save_download(download, dest_dir, ".mp3")
    return None


# -- Instagram Video  (snapinsta.to) ---------------------------------------
async def _download_ig_video(page: Page, url: str, dest_dir: Path) -> Path | None:
    """Automate snapinsta.to to download Instagram video."""
    await page.goto("https://snapinsta.to/en2", wait_until="domcontentloaded")
    await asyncio.sleep(2)
    await _dismiss_popups(page)

    input_sel = "input[type='text'], input[type='search'], input[type='url'], #url"
    await page.locator(input_sel).first.wait_for(state="visible", timeout=10_000)
    await page.locator(input_sel).first.fill(url)
    await asyncio.sleep(0.5)

    dl_btn = page.locator(
        "button:has-text('Download'), #download, button[type='submit']"
    ).first
    await dl_btn.click()

    log.info("Waiting for video processing (snapinsta.to) …")
    await asyncio.sleep(5)
    await _dismiss_popups(page)

    result_link = page.locator(
        "a:has-text('Download'), a[href*='download'], "
        "button:has-text('Download Video'), a:has-text('MP4')"
    ).first

    await result_link.wait_for(state="visible", timeout=120_000)
    await asyncio.sleep(1)
    await _dismiss_popups(page)

    download = await _wait_for_download(page, result_link.click)
    if download:
        return await _save_download(download, dest_dir, ".mp4")
    return None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
_HANDLERS: dict[tuple[Platform, Format], Callable] = {
    ("youtube", "audio"): _download_yt_audio,
    ("youtube", "video"): _download_yt_video,
    ("instagram", "audio"): _download_ig_audio,
    ("instagram", "video"): _download_ig_video,
}


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------
async def run(
    links_file: Path,
    dest_dir: Path,
    headless: bool = False,
    retries: int = 2,
) -> dict[str, str]:
    """
    Process every URL in *links_file*, download to *dest_dir*, and mark done.

    Returns a dict mapping URL → status ("ok" / "failed" / "skipped").
    """
    links_file = Path(links_file)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    tasks = parse_links_file(links_file)
    if not tasks:
        log.info("No pending links found in %s", links_file)
        return {}

    log.info("Found %d pending download(s)", len(tasks))
    results: dict[str, str] = {}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = await browser.new_context(
            accept_downloads=True,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        async def _block_ads(route: Route) -> None:
            await route.abort()

        await context.route(
            re.compile(
                r"(doubleclick\.net|googlesyndication|adservice|"
                r"facebook\.com/tr|analytics|ads\.|popads|"
                r"adnxs\.com|taboola|outbrain)"
            ),
            _block_ads,
        )

        page = await context.new_page()

        for task in tasks:
            handler = _HANDLERS.get((task.platform, task.fmt))
            if handler is None:
                log.warning(
                    "No handler for %s/%s – skipping %s",
                    task.platform,
                    task.fmt,
                    task.url,
                )
                results[task.url] = "skipped"
                continue

            success = False
            for attempt in range(1, retries + 1):
                log.info(
                    "[%d/%d] %s %s (%s) – attempt %d",
                    len(results) + 1,
                    len(tasks),
                    task.platform.upper(),
                    task.fmt,
                    task.url[:80],
                    attempt,
                )
                try:
                    path = await handler(page, task.url, dest_dir)
                    if path and path.exists():
                        mark_done(links_file, task.line_index)
                        results[task.url] = "ok"
                        success = True
                        log.info("✓ Downloaded: %s", path.name)
                        break
                    else:
                        log.warning("Handler returned no file – retrying …")
                except Exception as exc:
                    log.error("Attempt %d failed: %s", attempt, exc)

                await asyncio.sleep(3)

            if not success:
                results[task.url] = "failed"
                log.error("✗ Failed after %d attempts: %s", retries, task.url)

        await browser.close()

    # Summary
    ok = sum(1 for v in results.values() if v == "ok")
    fail = sum(1 for v in results.values() if v == "failed")
    skip = sum(1 for v in results.values() if v == "skipped")
    log.info("Done – %d ok, %d failed, %d skipped", ok, fail, skip)
    return results
