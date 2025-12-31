import asyncio
import shlex


class YouTubePlayer:
    """
    Lua-free YouTube playback.
    yt-dlp does discovery, mpv only plays URLs.
    """

    def __init__(self):
        self._proc: asyncio.subprocess.Process | None = None
        self._lock = asyncio.Lock()

    async def _run(self, cmd: str) -> str:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
        return out.decode().strip()

    async def resolve(self, query: str) -> str | None:
        cmd = (
            "yt-dlp "
            "--quiet "
            "--no-warnings "
            "--skip-download "
            "--print webpage_url "
            f"ytsearch1:{shlex.quote(query)}"
        )

        url = await self._run(cmd)
        return url if url.startswith("http") else None

    async def play(self, query: str):
        async with self._lock:
            # Stop current playback
            if self._proc and self._proc.returncode is None:
                self._proc.terminate()
                try:
                    await asyncio.wait_for(self._proc.wait(), timeout=2)
                except asyncio.TimeoutError:
                    self._proc.kill()

            print(f"🎵 Resolving YouTube: {query}", flush=True)

            url = await self.resolve(query)
            if not url:
                raise RuntimeError("No YouTube result found")

            print("▶️ Playing via mpv", flush=True)

            self._proc = await asyncio.create_subprocess_exec(
                "mpv",
                "--no-terminal",
                "--force-window=no",
                url,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

    async def stop(self):
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
            await self._proc.wait()
