import asyncio

class ListenState:
	def __init__(self):
		# initialize wake word variables
		self.listener_running: bool = True
		self.global_wake_allowed: bool = True
		# initialize audio buffer variables
		self.audio_buffer: bytes = b""
		self.len_audio_buffer: int = 0
		# initialize lock
		self._lock = asyncio.Lock()
		# initialize event and audio queues
		self.audio_queue = asyncio.Queue(maxsize=100)
		self.event_queue = asyncio.Queue()
        
	# Listener Running methods:
	async def get_listener_running(self) -> bool:
		async with self._lock:
			return self.listener_running

	async def stop_listener_running(self):
		async with self._lock:
			self.listener_running = False

	async def start_listener_running(self):
		async with self._lock:	
			self.listener_running = True
	

	# Wake Word methods
	async def allow_global_wake_word(self):
		async with self._lock:
			self.global_wake_allowed = True
			return self.global_wake_allowed

	async def block_global_wake_word(self):
		async with self._lock:
			print(f"🔀 Blocking global_wake_word", flush=True)
			self.global_wake_allowed = False
			return self.global_wake_allowed

	async def get_global_wake_word(self) -> bool:
		async with self._lock:
			return self.global_wake_allowed

	# Audio Buffer methods
	async def empty_audio_buffer(self):
		async with self._lock:
			self.len_audio_buffer = 0
			self.audio_buffer = b""
			self.len_audio_buffer = 0

	async def get_len_audio_buffer(self):
		async with self._lock:
			self.len_audio_buffer = len(self.audio_buffer)
			return self.len_audio_buffer

	async def add_to_audio_buffer(self, chunk: bytes):
		async with self._lock:
			self.audio_buffer += chunk
			self.len_audio_buffer = len(self.audio_buffer)
			return self.audio_buffer

	# Audio Queue methods
	async def add_to_audio_queue(self, item):
		async with self._lock:
			await self.audio_queue.put(item)
	async def get_audio_queue_full(self):
		async with self._lock:
			return self.audio_queue.full()
		
	# Event Queue methods
	async def add_to_event_queue(self, item):
		async with self._lock:
			await self.event_queue.put(item)


listen_state = ListenState()

