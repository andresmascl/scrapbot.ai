import json
import asyncio
import subprocess
import shutil
import os
import websockets

_CLIENTS: set[websockets.WebSocketServerProtocol] = set()

# Brave root data directory (NOT a profile subdir)
BRAVE_USER_DATA_DIR = "/home/a-mo/.config/BraveSoftware/Brave-Browser"
BRAVE_PROFILE = "Profile 2"

_BRAVE_STARTED = False


# -----------------------
# Brave launcher (LAZY, ONE-SHOT)
# -----------------------

def ensure_brave_running():
    """
    Launch Brave ONLY if the agent has not launched it before.
    Called lazily from YouTube-related actions.
    """
    global _BRAVE_STARTED

    if _BRAVE_STARTED:
        return

    brave_path = "/usr/bin/brave-browser"

    if not shutil.which("brave-browser"):
        print("❌ Brave browser not found", flush=True)
        return

    try:
        subprocess.Popen(
            [
                brave_path,
                f"--user-data-dir={BRAVE_USER_DATA_DIR}",
                f"--profile-directory={BRAVE_PROFILE}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        _BRAVE_STARTED = True
        print("🌐 Brave launched on-demand (YouTube intent)", flush=True)

    except Exception as e:
        print(f"❌ Failed to launch Brave: {e}", flush=True)


# -----------------------
# WebSocket server
# -----------------------

async def _ws_handler(ws):
    _CLIENTS.add(ws)
    try:
        async for _ in ws:
            pass
    finally:
        _CLIENTS.discard(ws)


async def start_ws_server(host="127.0.0.1", port=8765):
    server = await websockets.serve(_ws_handler, host, port)
    print(f"🎧 Scrapbot WS server running on {host}:{port}", flush=True)
    return server


# -----------------------
# Broadcast helper
# -----------------------

async def _broadcast(payload: dict):
    if not _CLIENTS:
        print("⚠️ No extension connected — command skipped", flush=True)
        return

    msg = json.dumps(payload)

    await asyncio.gather(
        *(ws.send(msg) for ws in _CLIENTS),
        return_exceptions=True,
    )


# -----------------------
# Public API (YouTube-related)
# -----------------------

async def search_and_play(query: str):
    ensure_brave_running()
    await _broadcast({
        "action": "search",
        "query": query,
    })


async def play():
    ensure_brave_running()
    await _broadcast({
        "action": "play",
    })


async def pause():
    ensure_brave_running()
    await _broadcast({
        "action": "pause",
    })


async def next_track():
    ensure_brave_running()
    await _broadcast({
        "action": "next",
    })
