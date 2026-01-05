const WS_URL = "ws://127.0.0.1:8765";
let socket = null;

function connect() {
  console.log("🔌 Connecting to Scrapbot WS…");

  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    console.log("🧩 Scrapbot WS connected");
  };

  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    chrome.tabs.query(
      { active: true, lastFocusedWindow: true },
      (tabs) => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, msg);
        }
      }
    );
  };

  socket.onclose = () => {
    console.warn("🔌 WS closed, retrying in 2s");
    setTimeout(connect, 2000);
  };

  socket.onerror = () => {
    socket.close();
  };
}

// Keep service worker alive
chrome.runtime.onStartup.addListener(connect);
chrome.runtime.onInstalled.addListener(connect);

// Also connect immediately
connect();
