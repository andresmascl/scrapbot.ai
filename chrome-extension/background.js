// --------------------------------------------------
// GLOBAL HANDLERS (Registered immediately for SW wakeup)
// --------------------------------------------------

const contentReadyResolvers = new Map();

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  console.log("📩 Received message:", msg.type || msg.action);

  // 1. Handle CONTENT_READY from content.js
  if (msg?.type === "CONTENT_READY" && sender.tab?.id) {
    console.log("✅ CONTENT_READY from tab:", sender.tab.id);
    const resolve = contentReadyResolvers.get(sender.tab.id);
    if (resolve) {
      resolve();
      contentReadyResolvers.delete(sender.tab.id);
    }
    reportState();
    return false;
  }

  // 2. Handle state requests from Bot (via offscreen)
  if (msg?.action === "request_state") {
    getAggregatedState().then((state) => {
      sendResponse({ type: "STATE_UPDATE", state: state });
    });
    return true; // Keep channel open for async response
  }

  // 3. Relay actions from Bot (via offscreen) to content script
  if (msg?.action && !msg.type) {
    relayToContent(msg).then(() => {
      // After relaying an action, send back a fresh state update
      getAggregatedState().then((state) => {
        sendResponse({ type: "STATE_UPDATE", state: state });
      });
    });
    return true; // Keep channel open for async response
  }

  return false;
});

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
// STATE MANAGEMENT & REPORTING
// --------------------------------------------------

async function getAggregatedState() {
  try {
    // Timeout-protected tab query
    const tabs = await chrome.tabs.query({ url: "https://www.youtube.com/*" });
    const hasYoutube = tabs.length > 0;

    let isPlaying = false;
    
    if (hasYoutube) {
      // Try to get playback status with a strict timeout
      try {
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error("Timeout")), 1000)
        );
        const messagePromise = chrome.tabs.sendMessage(tabs[0].id, {
          action: "get_video_state",
        });

        const response = await Promise.race([messagePromise, timeoutPromise]);
        if (response) {
          isPlaying = response.isPlaying;
        }
      } catch (e) {
        // Content script took too long or isn't ready
        console.log("⚠️ Could not get video state (timed out or not ready)");
      }
    }

    return {
      youtube_tab_open: hasYoutube,
      is_playing: isPlaying,
    };
  } catch (e) {
    console.error("❌ Error getting aggregated state:", e);
    return { youtube_tab_open: false, is_playing: false };
  }
}

let isReporting = false;
async function reportState() {
  if (isReporting) return;
  isReporting = true;

  try {
    console.log("📊 Reporting state...");
    const state = await getAggregatedState();
    console.log("📊 Current state:", state);
    
    await chrome.runtime.sendMessage({
      type: "STATE_UPDATE",
      state: state,
    });
  } catch (e) {
    console.warn("⚠️ Could not send STATE_UPDATE:", e);
  } finally {
    isReporting = false;
  }
}

// Listen for tab changes
chrome.tabs.onUpdated.addListener(reportState);
chrome.tabs.onRemoved.addListener(reportState);
chrome.tabs.onCreated.addListener(reportState);

// --------------------------------------------------
// HELPERS
// --------------------------------------------------

async function relayToContent(msg) {
  try {
    // Find active YouTube tab
    let [tab] = await chrome.tabs.query({
      url: "https://www.youtube.com/*",
      active: true,
      currentWindow: true,
    });

    if (tab) {
      // Try to ping the content script to see if it's alive
      try {
        await chrome.tabs.sendMessage(tab.id, { action: "ping" });
        console.log("⚡ Tab is alive, sending message...");
      } catch (e) {
        console.log("⏳ Tab exists but content script not ready. Waiting...");
        await new Promise((resolve) => {
          contentReadyResolvers.set(tab.id, resolve);
          // Auto-resolve after 10s to avoid hanging forever
          setTimeout(resolve, 10000);
        });
      }
    } else {
      console.log("📺 No YouTube tab found, creating one...");
      tab = await chrome.tabs.create({
        url: "https://www.youtube.com",
        active: true,
      });

      console.log("⏳ Waiting for CONTENT_READY...");
      await new Promise((resolve) => {
        contentReadyResolvers.set(tab.id, resolve);
        setTimeout(resolve, 20000); // Wait longer for new tab
      });
    }

    await chrome.tabs.sendMessage(tab.id, msg);
    console.log("✅ Message sent to content script");
  } catch (e) {
    console.warn("❌ Failed to relay message to content script", e);
  }
}

// Initial report
reportState();

// Create immediately
ensureOffscreen();
