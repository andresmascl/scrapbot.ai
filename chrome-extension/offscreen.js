const WS_URL = "ws://127.0.0.1:8765";
let socket;

function connect() {
  socket = new WebSocket(WS_URL);

  socket.onopen = () =>
    console.log("✅ Scrapbot WS connected");

  socket.onmessage = (event) => {
    chrome.runtime.sendMessage(JSON.parse(event.data));
  };

  socket.onclose = () => {
    setTimeout(connect, 1000);
  };
}

connect();
