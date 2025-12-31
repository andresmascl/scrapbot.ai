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
            # If browser exists, verify it's still alive
            if self._context and self._page:
                try:
                    await self._page.title()
                    return
                except Exception:
                    # Brave was closed manually
                    self._context = None
                    self._page = None

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

        await page.goto(
            "https://www.youtube.com",
            wait_until="domcontentloaded",
        )

        # Handle cookie / consent dialog if present
        try:
            consent = page.get_by_role("button", name="Accept all")
            if await consent.is_visible(timeout=3000):
                await consent.click()
        except Exception:
            pass

        # ✅ Correct YouTube search selector
        search_box = page.locator('input[name="search_query"]')
        await search_box.wait_for(state="visible", timeout=15000)

        await search_box.click()
        await search_box.fill(query)
        await search_box.press("Enter")

        # Wait for results
        await page.wait_for_selector("ytd-video-renderer", timeout=15000)

        # Click first video result
        first_video = page.locator("ytd-video-renderer a#thumbnail").first
        await first_video.wait_for(state="visible", timeout=15000)
        await first_video.click()

    async def shutdown(self):
        if self._context:
            await self._context.close()
            self._context = None
            self._page = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
