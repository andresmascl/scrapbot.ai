import asyncio
from playwright.async_api import async_playwright, BrowserContext, Page
from config import BROWSER_BINARY_PATH, BRAVE_PROFILE_PATH


class BrowserManager:
    """
    Persistent Brave browser controller (non-headless).
    Uses system Brave + real user profile.
    """

    def __init__(self):
        self._playwright = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._lock = asyncio.Lock()

    async def _ensure_browser(self):
        async with self._lock:
            if self._context and self._page:
                return

            self._playwright = await async_playwright().start()

            self._context = await self._playwright.chromium.launch_persistent_context(
                executable_path=BROWSER_BINARY_PATH,
                user_data_dir=BRAVE_PROFILE_PATH,
                headless=False,
                args=[
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-infobars",
                    "--disable-session-crashed-bubble",
                ],
            )

            pages = self._context.pages
            self._page = pages[0] if pages else await self._context.new_page()

    async def play_youtube(self, query: str):
        await self._ensure_browser()
        page = self._page

        print(f"▶️ Opening YouTube and searching: {query}", flush=True)

        await page.goto("https://www.youtube.com", wait_until="domcontentloaded")

        try:
            await page.get_by_role("button", name="Accept all").click(timeout=3000)
        except Exception:
            pass

        search_box = page.locator("input#search")
        await search_box.wait_for(timeout=10000)
        await search_box.fill(query)
        await search_box.press("Enter")

        first_video = page.locator("ytd-video-renderer a#thumbnail").first
        await first_video.wait_for(timeout=15000)
        await first_video.click()

    async def shutdown(self):
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
