import json
import asyncio
import time
import logging
import subprocess
import shutil
import socket
import websockets

from src.config import (
    BRAVE_BINARY,
    BRAVE_PROFILE,
    BRAVE_USER_DATA_DIR,
    WS_HOST,
    WS_PORT,
)

from src.app_state import browser_state
from src.speaker import speak

_CLIENTS: set = set()


# -----------------------
# Utility helpers
# -----------------------

def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def is_brave_running() -> bool:
    try:
        # Check for both the script name and the binary name
        subprocess.check_output(
            ["pgrep", "-f", "brave"],
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def ensure_brave_running() -> bool:
    """
    Ensure a Brave instance exists.

    Returns:
        True  -> Brave was launched by this call
        False -> Brave was already running
    """
    if not shutil.which("brave-browser"):
        logging.error("❌ Brave browser not found in PATH")
        return False

    if is_brave_running():
        logging.info("🌐 Brave already running — reusing instance")
        return False

    try:
        subprocess.Popen(
            [
                BRAVE_BINARY,
                f"--user-data-dir={BRAVE_USER_DATA_DIR}",
                f"--profile-directory={BRAVE_PROFILE}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        logging.info("🌐 Brave launched")
        return True

    except Exception as e:
        logging.error(f"❌ Failed to launch Brave: {e}")
        return False


# -----------------------
# WebSocket server
# -----------------------

async def _ws_handler(ws):
    _CLIENTS.add(ws)
    await browser_state.update(connected=True)
    logging.info("🔌 Extension connected to WebSocket")

    try:
        async for message in ws:
            logging.debug(f"📥 Received from WS: {message[:100]}...")
            try:
                data = json.loads(message)
                if data.get("type") == "STATE_UPDATE":
                    new_state = data.get("state", {})
                    await browser_state.update(ready=True, **new_state)
                    logging.debug(f"📊 Browser state updated: {new_state}")
                elif data.get("type") == "CONTENT_READY":
                    # If we get CONTENT_READY, we know at least one YouTube tab is open
                    await browser_state.update(youtube_tab_open=True, ready=True)
                    logging.info("📊 Received CONTENT_READY (YouTube tab confirmed)")
                else:
                    logging.warning(f"❓ Unknown message type: {data.get('type')}")
            except json.JSONDecodeError:
                logging.error("❌ Failed to decode JSON message")
    except Exception as e:
        logging.error(f"❌ WS Handler error: {e}")
        pass
    finally:
        _CLIENTS.discard(ws)
        if not _CLIENTS:
            await browser_state.update(
                connected=False, youtube_tab_open=False, ready=False
            )
            logging.info("🔌 Extension disconnected from WebSocket")


async def start_ws_server(host=WS_HOST, port=WS_PORT):
    if is_port_in_use(host, port):
        raise RuntimeError(
            f"WebSocket server already running on {host}:{port}"
        )

    server = await websockets.serve(_ws_handler, host, port)
    logging.info(f"🎧 Scrapbot WS server running on {host}:{port}")
    return server


# -----------------------
# State Helpers
# -----------------------

async def request_browser_state():
    """Ask the extension to report its current state."""
    await _broadcast({"action": "request_state"})


async def wait_for_ready(timeout=60, needs_youtube=False):
    """
    Wait for extension to connect and optionally for YouTube to be open.
    Returns True if ready, False otherwise.
    """
    logging.info(f"⏳ Waiting for ready (needs_youtube={needs_youtube})...")
    call_time = time.time()
    start_time = asyncio.get_event_loop().time()
    warned = False

    while True:
        state = await browser_state.get_state()
        elapsed = asyncio.get_event_loop().time() - start_time

        # We want a state update that happened AFTER this function was called
        # OR if we are already ready and just need to confirm.
        if state["ready"] and state["last_update"] >= call_time:
            if not needs_youtube or state["youtube_tab_open"]:
                logging.info(f"✅ Browser & Extension ready (elapsed={elapsed:.1f}s)")
                return True

        if elapsed > 7.0 and not warned:
            logging.warning("📣 Warning user: browser taking time")
            await speak("Waiting for browser to be ready...", language="en")
            warned = True

        if elapsed > timeout:
            logging.error(f"❌ Timeout waiting for ready (state={state})")
            return False

        # Proactively request state while waiting
        if state["connected"]:
            # Reduce frequency of requests to avoid overwhelming the extension
            if int(elapsed) % 2 == 0:
                logging.debug("📡 Requesting browser state...")
                await request_browser_state()

        await asyncio.sleep(1.0)


# -----------------------
# Broadcast helper
# -----------------------

async def _broadcast(payload: dict):
    if not _CLIENTS:
        return

    msg = json.dumps(payload)
    await asyncio.gather(
        *(ws.send(msg) for ws in _CLIENTS),
        return_exceptions=True,
    )


# -----------------------
# Public API (YouTube only)
# -----------------------

async def search_and_play(query: str):
    ensure_brave_running()
    if await wait_for_ready(needs_youtube=False):
        await _broadcast({"action": "search", "query": query})
    else:
        logging.error("❌ Search failed: Browser not ready")


async def play():
    ensure_brave_running()
    if await wait_for_ready(needs_youtube=True):
        await _broadcast({"action": "play"})
    else:
        logging.error("❌ Play failed: YouTube not ready")


async def pause():
    if not is_brave_running():
        return

    if await wait_for_ready(needs_youtube=True):
        await _broadcast({"action": "pause"})


async def next_track():
    ensure_brave_running()
    if await wait_for_ready(needs_youtube=True):
        await _broadcast({"action": "next"})
