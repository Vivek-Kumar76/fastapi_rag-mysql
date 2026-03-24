import { useState } from "react";
import "./App.css";

function App() {
  const [chats, setChats] = useState([
    { id: 1, messages: [] }
  ]);
  const [activeChat, setActiveChat] = useState(1);
  const [input, setInput] = useState("");

  const currentChat = chats.find(c => c.id === activeChat);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", text: input };
    const newChats = chats.map(chat =>
      chat.id === activeChat
        ? { ...chat, messages: [...chat.messages, userMsg] }
        : chat
    );

    setChats(newChats);
    setInput("");

    try {
      const res = await fetch(`http://localhost:8000/ask?query=${input}`);
      const data = await res.json();

      let answer = data.results.length
        ? data.results.map(r => r.answer).join("\n\n")
        : "No relevant answer found.";

      let botText = "";
      for (let i = 0; i < answer.length; i++) {
        botText += answer[i];

        setChats(prev =>
          prev.map(chat =>
            chat.id === activeChat
              ? {
                  ...chat,
                  messages: [
                    ...chat.messages.filter(m => m.role !== "typing"),
                    { role: "typing", text: botText }
                  ]
                }
              : chat
          )
        );

        await new Promise(r => setTimeout(r, 10));
      }

      setChats(prev =>
        prev.map(chat =>
          chat.id === activeChat
            ? {
                ...chat,
                messages: [
                  ...chat.messages.filter(m => m.role !== "typing"),
                  { role: "bot", text: answer }
                ]
              }
            : chat
        )
      );

    } catch (err) {
      console.error(err);
    }
  };

  const newChat = () => {
    const newId = chats.length + 1;
    setChats([...chats, { id: newId, messages: [] }]);
    setActiveChat(newId);
  };

  return (
    <div className="app">
      <div className="sidebar">
        <button onClick={newChat}>+ New Chat</button>
        {chats.map(chat => (
          <div
            key={chat.id}
            className={`chat-item ${chat.id === activeChat ? "active" : ""}`}
            onClick={() => setActiveChat(chat.id)}
          >
            Chat {chat.id}
          </div>
        ))}
      </div>
      <div className="chat-container">
        <div className="chat-box">
          {currentChat.messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              {msg.text}
            </div>
          ))}
        </div>

        <div className="input-box">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask something..."
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;