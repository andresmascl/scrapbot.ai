const WS_URL = "ws://127.0.0.1:8765";
let socket;

function connect() {
  socket = new WebSocket(WS_URL);

  socket.onopen = () =>
    console.log("✅ Scrapbot WS connected");

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("📥 Received from WS:", data.action || data.type);

    // Relay to background script and handle its response
    console.log("📤 Relaying to background script...");
    chrome.runtime.sendMessage(data, (response) => {
      if (chrome.runtime.lastError) {
        console.warn("⚠️ Relay error:", chrome.runtime.lastError.message);
        return;
      }
      console.log("📥 Received response from background:", response ? response.type : "null");
      if (response && response.type === "STATE_UPDATE") {
        console.log("📤 Sending response back to WS:", response.type);
        socket.send(JSON.stringify(response));
      }
    });
  };

  socket.onclose = () => {
    setTimeout(connect, 1000);
  };
}

chrome.runtime.onMessage.addListener((msg) => {
  // Only relay messages to the Bot that have a 'type' (e.g., STATE_UPDATE)
  // This avoids re-sending actions that came FROM the Bot.
  if (msg.type && socket && socket.readyState === WebSocket.OPEN) {
    console.log("📤 Sending to WS:", msg.type);
    socket.send(JSON.stringify(msg));
  }
});

connect();
