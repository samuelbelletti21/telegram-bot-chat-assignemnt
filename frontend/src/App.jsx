import { useEffect, useState } from "react";
import "./index.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  useEffect(() => {
    loadMessages();
  }, []);

  const loadMessages = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/messages`);
      const data = await response.json();
      setMessages(data);
    } catch (error) {
      console.error("Failed to load messages:", error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const payload = {
      text: input,
      direction: "outgoing",
    };

    try {
      const response = await fetch(`${API_BASE_URL}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const newMessage = await response.json();

      setMessages((prev) => [...prev, newMessage]);
      setInput("");
    } catch (error) {
      console.error("Failed to send message:", error);
    }
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
