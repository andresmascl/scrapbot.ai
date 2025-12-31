import asyncio


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
    # Listener run control (NEW)
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


# Singleton used across modules
listen_state = ListenState()
