import asyncio
import time


class BrowserState:
    def __init__(self):
        self.connected = False
        self.youtube_tab_open = False
        self.is_playing = False
        self.ready = False
        self.last_update = 0
        self._lock = asyncio.Lock()

    async def update(self, **kwargs):
        async with self._lock:
            for k, v in kwargs.items():
                if hasattr(self, k):
                    setattr(self, k, v)
            self.last_update = time.time()

    async def get_state(self):
        async with self._lock:
            return {
                "connected": self.connected,
                "youtube_tab_open": self.youtube_tab_open,
                "is_playing": self.is_playing,
                "ready": self.ready,
                "last_update": self.last_update,
            }


class ListenState:
    def __init__(self):
        # Wake-word gate
        self._global_wake_allowed = True
        self._wake_lock = asyncio.Lock()

        # Listener run gate (NEW)
        self._listener_running = True
        self._listener_lock = asyncio.Lock()

    # -------------------------
    # Wake-word control
    # -------------------------
    async def get_global_wake_word(self) -> bool:
        async with self._wake_lock:
            return self._global_wake_allowed

    async def block_global_wake_word(self):
        async with self._wake_lock:
            self._global_wake_allowed = False

    async def allow_global_wake_word(self):
        async with self._wake_lock:
            self._global_wake_allowed = True

    # -------------------------
    # Listener run control
    # -------------------------
    async def get_listener_running(self) -> bool:
        async with self._listener_lock:
            return self._listener_running

    async def block_listener(self):
        async with self._listener_lock:
            self._listener_running = False

    async def allow_listener(self):
        async with self._listener_lock:
            self._listener_running = True


# Singletons used across modules
listen_state = ListenState()
browser_state = BrowserState()
