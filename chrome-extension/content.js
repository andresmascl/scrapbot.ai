console.log("🧩 Scrapbot content script loaded");

// --------------------------------------------------
// CONSTANTS
// --------------------------------------------------

const STATE_KEY = "scrapbot_state";

// --------------------------------------------------
// STATE HELPERS
// --------------------------------------------------

function setState(state) {
  sessionStorage.setItem(STATE_KEY, JSON.stringify(state));
}

function getState() {
  const raw = sessionStorage.getItem(STATE_KEY);
  return raw ? JSON.parse(raw) : null;
}

function clearState() {
  sessionStorage.removeItem(STATE_KEY);
}

// --------------------------------------------------
// CONTENT READY HANDSHAKE
// --------------------------------------------------

chrome.runtime.sendMessage({ type: "CONTENT_READY" });

// --------------------------------------------------
// MESSAGE HANDLER
// --------------------------------------------------

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === "search" && msg.query) {
    console.log("🎯 New search request:", msg.query);

    // ALWAYS override previous intent
    setState({
      phase: "search",
      query: msg.query,
    });

    forceSearch(msg.query);
  }

  if (msg.action === "pause") pauseVideo();
  if (msg.action === "play") playVideo();
  if (msg.action === "next") nextTrack();
});

// --------------------------------------------------
// PHASE EXECUTION (RUNS ON EVERY LOAD)
// --------------------------------------------------

(async function runPhase() {
  const state = getState();
  if (!state) return;

  // -------------------------
  // SEARCH RESULTS PAGE
  // -------------------------
  if (
    state.phase === "search" &&
    location.pathname === "/results"
  ) {
    console.log("📄 Results page loaded");

    await waitFor(
      () => document.querySelector("ytd-video-renderer a#thumbnail"),
      20000
    );

    const first = document.querySelector(
      "ytd-video-renderer a#thumbnail"
    );

    if (!first) {
      console.warn("❌ No search results found");
      clearState();
      return;
    }

    console.log("▶️ Clicking first result");
    setState({
      phase: "play",
    });

    first.click();
    return;
  }

  // -------------------------
  // VIDEO PAGE
  // -------------------------
  if (
    state.phase === "play" &&
    location.pathname === "/watch"
  ) {
    console.log("🎬 Video page loaded");

    await waitFor(() => document.querySelector("video"), 20000);
    await forcePlay(document.querySelector("video"));

    clearState();
  }
})();

// --------------------------------------------------
// ACTIONS
// --------------------------------------------------

function forceSearch(query) {
  const searchUrl =
    "https://www.youtube.com/results?search_query=" +
    encodeURIComponent(query);

  console.log("🔍 Forcing search:", searchUrl);

  // Always navigate — NEVER reuse existing results
  location.href = searchUrl;
}

function pauseVideo() {
  const video = document.querySelector("video");
  if (video && !video.paused) video.pause();
}

function playVideo() {
  const video = document.querySelector("video");
  if (video && video.paused) video.play().catch(() => {});
}

function nextTrack() {
  document.querySelector(".ytp-next-button")?.click();
}

// --------------------------------------------------
// HELPERS
// --------------------------------------------------

async function forcePlay(video) {
  try {
    await video.play();
  } catch {
    setTimeout(() => video.play().catch(() => {}), 500);
  }
}

function waitFor(fn, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const timer = setInterval(() => {
      try {
        if (fn()) {
          clearInterval(timer);
          resolve();
        } else if (Date.now() - start > timeout) {
          clearInterval(timer);
          reject("Timeout");
        }
      } catch {}
    }, 100);
  });
}
