import { useEffect, useRef, useState } from "react";
import "./index.css";
import { EventType, Direction } from "./const";

// Dev: connect directly to the backend. Production (Docker): go through the nginx proxy.
const WS_URL = import.meta.env.DEV
  ? "ws://localhost:8000/ws"
  : `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws`;

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const wsRef = useRef(null);

  useEffect(() => {
    function connect() {
      const socket = new WebSocket(WS_URL);
      wsRef.current = socket;

      socket.onopen = () => {
        socket.send(JSON.stringify({ type: EventType.GET_MESSAGES }));
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === EventType.MESSAGES_LIST) {
          setMessages(data.payload);
        } else if (data.type === EventType.MESSAGE_CREATED) {
          setMessages((prev) => [...prev, data.payload]);
        } else if (data.type === EventType.ERROR) {
          console.error("Server error:", data.payload.message);
        }
      };

      socket.onclose = () => {
        console.log("Disconnected from WebSocket, reconnecting in 2s...");
        setTimeout(connect, 2000);
      };

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
      };
    }

    connect();

    return () => {
      const socket = wsRef.current;
      if (socket) {
        socket.onclose = null; // prevent reconnect on intentional unmount
        socket.close();
      }
    };
  }, []);

  const sendMessage = () => {
    const socket = wsRef.current;
    if (!input.trim()) return;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      console.error("Not connected to the server.");
      return;
    }
    socket.send(
      JSON.stringify({
        type: EventType.SEND_MESSAGE,
        payload: { text: input, direction: Direction.OUTGOING },
      })
    );
    setInput("");
  };

  const hasActiveChat = messages.length > 0;
  const canSend = hasActiveChat && !!input.trim();

  return (
    <div className="chat-page">
      <div className="chat-container">
        <header className="chat-header">
          <h2>Telegram Chat</h2>
        </header>

        <div className="chat-messages">
          {!hasActiveChat ? (
            <div className="chat-placeholder">
              Waiting for the Telegram participant to send the first message...
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`chat-message ${msg.direction}`}>
                <div className="chat-bubble">
                  <div className="chat-text">{msg.text}</div>
                  <div className="chat-timestamp">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="chat-input">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              hasActiveChat
                ? "Type a message..."
                : "Waiting for Telegram participant…"
            }
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            disabled={!hasActiveChat}
          />
          <button onClick={sendMessage} disabled={!canSend}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
