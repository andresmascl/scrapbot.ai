console.log("🧩 Scrapbot content script loaded");

chrome.runtime.onMessage.addListener((msg) => {
  switch (msg.action) {
    case "search":
      searchAndPlay(msg.query);
      break;
    case "pause":
      pauseVideo();
      break;
    case "play":
      playVideo();
      break;
    case "next":
      nextTrack();
      break;
  }
});

/* -------------------------
   CORE ACTIONS
------------------------- */

async function searchAndPlay(query) {
  console.log("🔍 SEARCH & PLAY:", query);

  // ALWAYS force a real navigation
  const searchUrl =
    "https://www.youtube.com/results?search_query=" +
    encodeURIComponent(query);

  location.href = searchUrl;

  // Wait for results
  await waitFor(
    () => document.querySelector("ytd-video-renderer a#thumbnail"),
    20000
  );

  const first = document.querySelector(
    "ytd-video-renderer a#thumbnail"
  );

  if (!first || !first.href) {
    console.warn("❌ No playable result");
    return;
  }

  console.log("▶️ Opening first result");
  location.href = first.href;

  // Wait for player
  await waitFor(() => document.querySelector("video"), 20000);

  const video = document.querySelector("video");

  // Force play
  await forcePlay(video);
}

function pauseVideo() {
  const video = document.querySelector("video");
  if (!video) return;

  if (!video.paused) {
    console.log("⏸ Pausing");
    video.pause();
  }
}

function playVideo() {
  const video = document.querySelector("video");
  if (!video) return;

  if (video.paused) {
    console.log("▶️ Playing");
    video.play().catch(() => {});
  }
}

function nextTrack() {
  const btn = document.querySelector(".ytp-next-button");
  btn?.click();
}

/* -------------------------
   HELPERS
------------------------- */

async function forcePlay(video) {
  try {
    await video.play();
    console.log("▶️ Playback started");
  } catch {
    console.warn("⚠️ Autoplay blocked, retrying");
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
