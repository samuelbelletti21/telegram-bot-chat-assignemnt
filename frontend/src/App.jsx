import { useEffect, useRef, useState } from "react";
import "./index.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const wsRef = useRef(null);

  useEffect(() => {
    const socket = new WebSocket("ws://127.0.0.1:8000/ws");
    wsRef.current = socket;

    socket.onopen = () => {
      console.log("Connected to WebSocket");

      socket.send(
        JSON.stringify({
          type: "get_messages",
        })
      );
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "messages_list") {
        setMessages(data.payload);
      }

      if (data.type === "message_created") {
        setMessages((prev) => [...prev, data.payload]);
      }

      if (data.type === "error") {
        console.error("Server error:", data.payload.message);
      }
    };

    socket.onclose = () => {
      console.log("Disconnected from WebSocket");
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    return () => {
      socket.close();
    };
  }, []);

  const sendMessage = () => {
    const socket = wsRef.current;

    if (!input.trim()) return;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      console.error("WebSocket is not connected");
      return;
    }
    // Let the server handle state (single source of truth)
    socket.send(
      JSON.stringify({
        type: "send_message",
        payload: {
          text: input,
          direction: "outgoing",
        },
      })
    );

    setInput("");
  };

  return (
    <div className="chat-page">
      <div className="chat-container">
        <header className="chat-header">
          <h2>Telegram Chat</h2>
        </header>

        <div className="chat-messages">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`chat-message ${msg.direction}`}
            >
              <div className="chat-bubble">
                <div className="chat-text">{msg.text}</div>
                <div className="chat-timestamp">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="chat-input">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;
