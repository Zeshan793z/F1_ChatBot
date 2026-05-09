import React, { useState } from "react";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const askStrategy = async () => {
    if (!question) {
      setAnswer("Please enter a question first!");
      return;
    }
    
    setLoading(true);
    setAnswer("Loading...");
    
    try {
      const url = `http://localhost:8000/strategy?year=2023&gp=Miami&driver=VER&question=${encodeURIComponent(question)}`;
      const res = await fetch(url);
      const data = await res.json();
      setAnswer(data.response || JSON.stringify(data, null, 2));
    } catch (err) {
      setAnswer(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const askFastestLap = async () => {
    setLoading(true);
    setAnswer("Loading fastest lap data...");
    
    try {
      const url = `http://localhost:8000/fastest-lap?year=2023&gp=Miami&driver=VER`;
      const res = await fetch(url);
      const data = await res.json();
      
      if (data.lap_data) {
        setAnswer(
          `🏎️ Fastest Lap for Verstappen at Miami GP 2023:\n\n` +
          `• Lap Number: ${data.lap_data.lap_number}\n` +
          `• Lap Time: ${data.lap_data.lap_time}\n` +
          `• Tire Compound: ${data.lap_data.compound}`
        );
      } else {
        setAnswer("No lap data found. Please check if the race data is available.");
      }
    } catch (err) {
      setAnswer(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const askGeneral = async () => {
    if (!question) {
      setAnswer("Please enter a question first!");
      return;
    }
    
    setLoading(true);
    setAnswer("Thinking...");
    
    try {
      const url = `http://localhost:8000/chat?question=${encodeURIComponent(question)}`;
      const res = await fetch(url);
      const data = await res.json();
      setAnswer(data.answer || JSON.stringify(data, null, 2));
    } catch (err) {
      setAnswer(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>🏎️ F1 Chatbot</h1>
      <div style={{ marginBottom: "10px" }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about F1 strategy, history, or stats..."
          style={{ width: "500px", padding: "10px", fontSize: "16px" }}
          onKeyPress={(e) => e.key === 'Enter' && askGeneral()}
        />
      </div>
      <div style={{ marginTop: "10px", display: "flex", gap: "10px" }}>
        <button 
          onClick={askStrategy} 
          style={{ padding: "10px 20px", cursor: "pointer" }}
          disabled={loading}
        >
          Ask Strategy
        </button>
        <button 
          onClick={askFastestLap} 
          style={{ padding: "10px 20px", cursor: "pointer" }}
          disabled={loading}
        >
          Get Fastest Lap
        </button>
        <button 
          onClick={askGeneral} 
          style={{ padding: "10px 20px", cursor: "pointer", backgroundColor: "#4CAF50", color: "white" }}
          disabled={loading}
        >
          Ask General
        </button>
      </div>
      <div style={{ marginTop: "20px" }}>
        <h3>Response:</h3>
        <pre style={{ 
          backgroundColor: "#f5f5f5", 
          padding: "15px", 
          borderRadius: "5px",
          border: "1px solid #ddd",
          fontFamily: "monospace",
          whiteSpace: "pre-wrap",
          wordWrap: "break-word"
        }}>
          {loading ? "⏳ Loading..." : answer}
        </pre>
      </div>
    </div>
  );
}

export default App;