import asyncio


class ListenState:
    def __init__(self):
        self.listener_running = True
        self.global_wake_allowed = True
        self._lock = asyncio.Lock()

    async def get_listener_running(self):
        return self.listener_running

    async def stop_listener_running(self):
        self.listener_running = False

    async def allow_global_wake_word(self):
        self.global_wake_allowed = True

    async def block_global_wake_word(self):
        print("🔀 Blocking global wake word", flush=True)
        self.global_wake_allowed = False

    async def get_global_wake_word(self):
        return self.global_wake_allowed


listen_state = ListenState()
