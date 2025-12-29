"""Action execution - YouTube automation, etc."""
import asyncio
import urllib.parse


async def execute_action(intent_data):
    """
    Execute action based on intent.

    Args:
        intent_data: Parsed JSON from LLM containing intent, filter, etc.

    Returns:
        True if action executed successfully
    """
    if not intent_data:
        return False

    intent = intent_data.get("intent")
    filter_term = intent_data.get("filter", "")

    print(f"🎬 Executing action: {intent}", flush=True)

    if intent == "play_youtube":
        return await play_youtube(filter_term)
    elif intent == "provide_info":
        # Info is already in the feedback, just return True
        return True
    else:
        print(f"⚠️ Unknown intent: {intent}", flush=True)
        return False


async def play_youtube(search_query):
    """
    Open YouTube search in browser.

    Args:
        search_query: Search term for YouTube

    Returns:
        True if successful
    """
    if not search_query:
        print("⚠️ No search query provided", flush=True)
        return False

    print(f"▶️ Opening YouTube: {search_query}", flush=True)

    # Build YouTube search URL
    encoded_query = urllib.parse.quote(search_query)
    youtube_url = f"https://www.youtube.com/results?search_query={encoded_query}"

    try:
        # Try to open in browser (works in most Linux environments)
        proc = await asyncio.create_subprocess_exec(
            "xdg-open", youtube_url,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()

        print(f"✅ Opened YouTube for: {search_query}", flush=True)
        return True

    except Exception as e:
        print(f"⚠️ Could not open browser: {e}", flush=True)
        print(f"ℹ️ YouTube URL: {youtube_url}", flush=True)
        return False
