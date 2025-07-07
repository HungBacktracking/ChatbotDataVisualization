"use client";
import { useState, useRef, useEffect } from "react";
import Chart from "chart.js/auto";
import ReactMarkdown from "react-markdown";
import "./../style/visual.less";

type Message =
  | { type: "text"; content: string }
  | { type: "chart"; id: string; title: string; data: any };

export default function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chartInstances = useRef<{ [key: string]: Chart }>({});

  const cleanContent = (raw: string) => {
    let s = raw.replace(/\\n/g, "\n");
    s = s.replace(/\n{3,}/g, "\n\n");
    const bolds: string[] = [];
    s = s.replace(/\*\*(.*?)\*\*/g, (_, txt) => {
      bolds.push(txt);
      return `@@B${bolds.length - 1}@@`;
    });
    s = s.replace(/\*(?!\*)/g, "");
    s = s.replace(/@@B(\d+)@@/g, (_, i) => `**${bolds[+i]}**`);
    return s.trim();
  };

  const updateLatestBotMessage = (text: string) => {
    setMessages(prev => {
      const msgs = [...prev];
      const last = msgs[msgs.length - 1];
      if (last && last.type === "text" && last.content.startsWith("🤖")) {
        last.content = "🤖 " + text;
      } else {
        msgs.push({ type: "text", content: "🤖 " + text });
      }
      return msgs;
    });
  };

  const sendMessage = async () => {
    const question = input.trim();
    if (!question) return;
    setMessages(m => [...m, { type: "text", content: `👤 ${question}` }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("https://validity-meetings-alabama-silent.trycloudflare.com/api/v1/chat/generate-response", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({
          session_id: "user456",
          content: question,
          history: [],
          role: "user",
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const reader = res.body?.getReader();
      if (!reader) throw new Error("No reader");

      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let rawText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");

        for (let i = 0; i < parts.length - 1; i++) {
          const ev = parts[i].trim();
          if (!ev) continue;
          const lines = ev.split("\n");
          let evtType = "", evtData = "";
          for (const l of lines) {
            if (l.startsWith("event:")) evtType = l.slice(6).trim();
            else if (l.startsWith("data:")) evtData = l.slice(5).trim();
          }
          if (!evtData || evtData === "[DONE]") continue;

          if (evtType === "chart" && evtData.startsWith("{") && evtData.endsWith("}")) {
            try {
              const p = JSON.parse(evtData);
              if (p.type === "chart") {
                const id = `chart-${Date.now()}-${Math.random().toString(36).slice(2)}`;
                if (p.description) {
                  setMessages(m => [...m, { type: "text", content: `🤖 ${p.description}` }]);
                }
                setMessages(m => [...m, { type: "chart", id, title: p.config?.title || p.title || "Biểu đồ", data: p }]);
              }
            } catch {}
            continue;
          }

          if (evtData.startsWith("{") && evtData.endsWith("}")) {
            try {
              const p = JSON.parse(evtData);
              if (p.type === "text" && p.content) {
                rawText += p.content;
                updateLatestBotMessage(rawText);
                continue;
              }
            } catch {}
          }

          rawText += evtData;
          updateLatestBotMessage(rawText);
        }

        buffer = parts[parts.length - 1];
      }

      const cleaned = cleanContent(rawText);
      updateLatestBotMessage(cleaned);
    } catch (err: any) {
      setMessages(m => [...m, { type: "text", content: `⚠️ Lỗi khi kết nối: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) sendMessage();
  };

  useEffect(() => {
    messages.forEach(msg => {
      if (msg.type === "chart") {
        const canvas = document.getElementById(msg.id) as HTMLCanvasElement;
        if (canvas && !chartInstances.current[msg.id]) {
          const ctx = canvas.getContext("2d");
          if (!ctx) return;
          try {
            const data = { ...msg.data.data };
            const colors = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"];
            if (data.datasets) {
              data.datasets = data.datasets.map((ds: any) => ({
                ...ds,
                backgroundColor: ds.backgroundColor === "auto" ? colors : ds.backgroundColor,
                borderColor: ds.borderColor === "auto" ? colors : ds.borderColor,
              }));
            }
            const chart = new Chart(ctx, {
              type: msg.data.config?.type || msg.data.type || "bar",
              data,
              options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  title: { display: true, text: msg.title },
                  legend: { display: true, position: "top" },
                },
                scales: {
                  y: { beginAtZero: true },
                },
                ...msg.data.config?.options,
              },
            });
            chartInstances.current[msg.id] = chart;
          } catch {
            setMessages(m => [...m, { type: "text", content: "⚠️ Lỗi tạo biểu đồ." }]);
          }
        }
      }
    });
  }, [messages]);

  useEffect(() => {
    return () => {
      Object.values(chartInstances.current).forEach(c => c.destroy());
      chartInstances.current = {};
    };
  }, []);

  return (
    <div className="chatContainer">
      <div className="chatHeader">Tiki Chatbot</div>
      <div className="chatBox">
        {messages.map((msg, idx) => {
          const isUser = msg.type === "text" && msg.content.startsWith("👤");
          return (
            <div
              key={idx}
              className={`$"chatMessage" ${isUser ? "userMessage" : "botMessage"}`}
            >
              {msg.type === "text" ? (
                <div className="markdownMessage">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                <div>
                  <div style={{ fontWeight: "bold", marginBottom: 8 }}>📊 {msg.title}</div>
                  <div style={{ position: "relative", height: 250 }}>
                    <canvas id={msg.id} style={{ width: "100%", height: "100%" }} />
                  </div>
                </div>
              )}
            </div>
          );
        })}
        {loading && (
          <div className="chatMessage">
            <div>⏳ Đang xử lý...</div>
          </div>
        )}
      </div>
      <div className="chatInputArea">
        <input
          className="chatInput"
          placeholder="Nhập câu hỏi..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          disabled={loading}
        />
        <button
          className="chatButton"
          onClick={sendMessage}
          disabled={loading}
        >
          {loading ? "..." : "Gửi"}
        </button>
      </div>
    </div>
  );
}
