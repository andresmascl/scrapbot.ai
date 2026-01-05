async function ensureOffscreen() {
  if (await chrome.offscreen.hasDocument()) return;

  await chrome.offscreen.createDocument({
    url: "offscreen.html",
    reasons: ["DOM_PARSER"],
    justification: "Maintain persistent WebSocket connection to Scrapbot",
  });

  console.log("🧠 Offscreen document created");
}

chrome.runtime.onStartup.addListener(ensureOffscreen);
chrome.runtime.onInstalled.addListener(ensureOffscreen);

// --------------------------------------------------
// CONTENT READY HANDSHAKE
// --------------------------------------------------

const contentReadyResolvers = new Map();

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg?.type === "CONTENT_READY" && sender.tab?.id) {
    const resolve = contentReadyResolvers.get(sender.tab.id);
    if (resolve) {
      resolve();
      contentReadyResolvers.delete(sender.tab.id);
    }
  }
});

// --------------------------------------------------
// MAIN RELAY: offscreen → content
// --------------------------------------------------

chrome.runtime.onMessage.addListener(async (msg) => {
  // Find active YouTube tab in current window
  let [tab] = await chrome.tabs.query({
    url: "https://www.youtube.com/*",
    active: true,
    currentWindow: true,
  });

  // If none, create one
  if (!tab) {
    tab = await chrome.tabs.create({
      url: "https://www.youtube.com",
      active: true,
    });

    // Wait for content script to confirm readiness
    await new Promise((resolve) => {
      contentReadyResolvers.set(tab.id, resolve);
    });
  }

  try {
    await chrome.tabs.sendMessage(tab.id, msg);
  } catch (e) {
    console.warn("❌ Failed to send message to content script", e);
  }
});

// Create immediately
ensureOffscreen();
