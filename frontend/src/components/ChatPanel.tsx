import { useState } from "react";
import { api } from "../api";
import { SendIcon, SparkleIcon } from "../icons";

type Message = { role: "ai" | "user"; text: string };

export function ChatPanel({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<Message[]>([
    { role: "ai", text: "Hi — I'm ready to answer questions about your lab history. Try asking about a specific test or trend." },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text }]);
    setSending(true);
    try {
      const { reply } = await api.chat(text);
      setMessages((prev) => [...prev, { role: "ai", text: reply }]);
    } catch {
      setMessages((prev) => [...prev, { role: "ai", text: "Something went wrong reaching the assistant." }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <aside className="chat-panel">
      <div className="chat-header">
        <span className="chat-title">
          <SparkleIcon size={15} />
          Ask about my results
        </span>
        <button
          onClick={onClose}
          aria-label="Close chat"
          style={{ background: "none", border: "none", cursor: "pointer", color: "var(--ink-faint)" }}
        >
          ✕
        </button>
      </div>
      <div className="chat-body">
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            {m.text}
          </div>
        ))}
        {sending && <div className="bubble ai">Thinking…</div>}
      </div>
      <div className="chat-input-row">
        <input
          className="chat-input"
          placeholder="Ask about your results…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button className="chat-send" onClick={send} disabled={sending} aria-label="Send message">
          <SendIcon />
        </button>
      </div>
    </aside>
  );
}
