async function ensureOffscreen() {
  if (await chrome.offscreen.hasDocument()) {
    return;
  }

  await chrome.offscreen.createDocument({
    url: "offscreen.html",
    reasons: ["DOM_PARSER"],
    justification: "Maintain persistent WebSocket connection to Scrapbot",
  });

  console.log("🧠 Offscreen document created");
}

chrome.runtime.onStartup.addListener(ensureOffscreen);
chrome.runtime.onInstalled.addListener(ensureOffscreen);

// Relay messages from offscreen → content script
chrome.runtime.onMessage.addListener(async (msg) => {
  const tabs = await chrome.tabs.query({
    url: "https://www.youtube.com/*"
  });

  let tab;

  if (tabs.length > 0) {
    tab = tabs[0];
  } else {
    tab = await chrome.tabs.create({
      url: "https://www.youtube.com",
      active: true
    });

    // Wait for content script to load
    await new Promise((r) => setTimeout(r, 1500));
  }

  try {
    await chrome.tabs.sendMessage(tab.id, msg);
  } catch (e) {
    console.warn("❌ Failed to send message to content script", e);
  }
});

// Create immediately
ensureOffscreen();
