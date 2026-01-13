import json
import asyncio
import subprocess
import shutil
import socket
import websockets

from config import (
    BRAVE_BINARY,
    BRAVE_PROFILE,
    BRAVE_USER_DATA_DIR,
    WS_HOST,
    WS_PORT,
)

_CLIENTS: set[websockets.WebSocketServerProtocol] = set()


# -----------------------
# Utility helpers
# -----------------------

def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def is_brave_running() -> bool:
    try:
        subprocess.check_output(
            ["pgrep", "-f", "brave-browser"],
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
        print("❌ Brave browser not found in PATH", flush=True)
        return False

    if is_brave_running():
        print("🌐 Brave already running — reusing instance", flush=True)
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
        print("🌐 Brave launched", flush=True)
        return True

    except Exception as e:
        print(f"❌ Failed to launch Brave: {e}", flush=True)
        return False


# -----------------------
# WebSocket server
# -----------------------

async def _ws_handler(ws):
    _CLIENTS.add(ws)
    try:
        async for _ in ws:
            pass
    except Exception:
        pass
    finally:
        _CLIENTS.discard(ws)


async def start_ws_server(host=WS_HOST, port=WS_PORT):
    if is_port_in_use(host, port):
        raise RuntimeError(
            f"WebSocket server already running on {host}:{port}"
        )

    server = await websockets.serve(_ws_handler, host, port)
    print(f"🎧 Scrapbot WS server running on {host}:{port}", flush=True)
    return server


# -----------------------
# Broadcast helper
# -----------------------

async def _broadcast(payload: dict, brave_was_launched: bool = False):
    if brave_was_launched:
        await asyncio.sleep(2)

    if not _CLIENTS:
        print("⚠️ No extension connected — command skipped", flush=True)
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
    brave_launched = ensure_brave_running()
    await _broadcast(
        {"action": "search", "query": query},
        brave_was_launched=brave_launched,
    )


async def play():
    brave_launched = ensure_brave_running()
    await _broadcast(
        {"action": "play"},
        brave_was_launched=brave_launched,
    )


async def pause():
    # NOTE: pause only makes sense if YouTube is already in use
    if not is_brave_running():
        print("⏸ Pause ignored — browser not running", flush=True)
        return

    await _broadcast({"action": "pause"})


async def next_track():
    brave_launched = ensure_brave_running()
    await _broadcast(
        {"action": "next"},
        brave_was_launched=brave_launched,
    )
