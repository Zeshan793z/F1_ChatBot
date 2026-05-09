import React, { useState } from "react";
import LapTimeChart from "./components/LapTimeChart";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const [chartData, setChartData] = useState({ driver: "VER", year: 2023, gp: "Miami" });

  // Helper function to parse driver from question
  const parseDriverFromQuestion = (questionText) => {
    const upperQuestion = questionText.toUpperCase();
    const drivers = {
      'VER': ['VER', 'VERSTAPPEN', 'MAX'],
      'HAM': ['HAM', 'HAMILTON', 'LEWIS'],
      'LEC': ['LEC', 'LECLERC', 'CHARLES'],
      'PER': ['PER', 'PEREZ', 'CHECO'],
      'NOR': ['NOR', 'NORRIS', 'LANDO'],
      'SAI': ['SAI', 'SAINZ', 'CARLOS'],
      'RUS': ['RUS', 'RUSSELL', 'GEORGE'],
      'PIA': ['PIA', 'PIASTRI', 'OSCAR'],
      'ALO': ['ALO', 'ALONSO', 'FERNANDO']
    };
    
    for (const [code, aliases] of Object.entries(drivers)) {
      for (const alias of aliases) {
        if (upperQuestion.includes(alias)) {
          return code;
        }
      }
    }
    return null; // Return null if no driver found
  };

  // Helper function to parse year from question
  const parseYearFromQuestion = (questionText) => {
    const yearMatch = questionText.match(/\b(20\d{2})\b/);
    return yearMatch ? parseInt(yearMatch[0]) : null;
  };

  // Helper function to parse GP from question
  const parseGPFromQuestion = (questionText) => {
    const upperQuestion = questionText.toUpperCase();
    const gps = {
      'Miami': ['MIAMI', 'MIAMI GP', 'MIAMI GRAND PRIX'],
      'Monaco': ['MONACO', 'MONACO GP', 'MONACO GRAND PRIX'],
      'Silverstone': ['SILVERSTONE', 'BRITISH GP', 'BRITISH GRAND PRIX'],
      'Spa': ['SPA', 'BELGIAN GP', 'BELGIAN GRAND PRIX', 'SPA-FRANCORCHAMPS'],
      'Monza': ['MONZA', 'ITALIAN GP', 'ITALIAN GRAND PRIX'],
      'Singapore': ['SINGAPORE', 'SINGAPORE GP', 'SINGAPORE GRAND PRIX'],
      'Suzuka': ['SUZUKA', 'JAPANESE GP', 'JAPANESE GRAND PRIX'],
      'Austin': ['AUSTIN', 'COTA', 'US GP', 'UNITED STATES GP'],
      'Abu Dhabi': ['ABU DHABI', 'YAS MARINA', 'ABU DHABI GP']
    };
    
    for (const [gp, aliases] of Object.entries(gps)) {
      for (const alias of aliases) {
        if (upperQuestion.includes(alias)) {
          return gp;
        }
      }
    }
    return "Miami"; // Default to Miami
  };

  const askStrategy = async () => {
    if (!question) {
      setAnswer("Please enter a question first!");
      return;
    }
    setLoading(true);
    setAnswer("Loading...");
    setShowChart(false);
    
    // Parse dynamic parameters from question
    const driver = parseDriverFromQuestion(question) || "VER";
    const year = parseYearFromQuestion(question) || 2023;
    const gp = parseGPFromQuestion(question);
    
    try {
      const url = `http://localhost:8000/strategy?year=${year}&gp=${gp}&driver=${driver}&question=${encodeURIComponent(question)}`;
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
    if (!question) {
      setAnswer("Please enter a question first!\nExample: 'What was Verstappen's fastest lap in Miami 2024?'");
      return;
    }
    
    setLoading(true);
    setAnswer("Loading fastest lap data...");
    setShowChart(false);
    
    // Parse dynamic parameters from question
    const driver = parseDriverFromQuestion(question) || "VER";
    const year = parseYearFromQuestion(question) || 2023;
    const gp = parseGPFromQuestion(question);
    
    try {
      const url = `http://localhost:8000/fastest-lap?year=${year}&gp=${gp}&driver=${driver}`;
      const res = await fetch(url);
      const data = await res.json();
      
      if (data.lap_data) {
        setAnswer(
          `🏎️ Fastest Lap for ${driver} at ${gp} GP ${year}:\n\n` +
          `• Lap Number: ${data.lap_data.lap_number}\n` +
          `• Lap Time: ${data.lap_data.lap_time}\n` +
          `• Tire Compound: ${data.lap_data.compound}`
        );
        // Optionally show chart for fastest lap
        setChartData({ driver, year, gp });
        setShowChart(true);
      } else {
        setAnswer(`No lap data found for ${driver} at ${gp} GP ${year}.\n\nPossible reasons:\n• Year might be too recent (2024 data may not be available yet)\n• Driver didn't participate\n• Check your spelling`);
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
    setShowChart(false);
    try {
      const url = `http://localhost:8000/chat?question=${encodeURIComponent(question)}`;
      const res = await fetch(url);
      const data = await res.json();
      setAnswer(data.answer || JSON.stringify(data, null, 2));

      // Check if question is about lap times and show chart
      const lowerQuestion = question.toLowerCase();
      if ((lowerQuestion.includes("fastest lap") || lowerQuestion.includes("lap time")) && 
          (lowerQuestion.includes("ver") || lowerQuestion.includes("max"))) {
        const driver = parseDriverFromQuestion(question) || "VER";
        const year = parseYearFromQuestion(question) || 2023;
        const gp = parseGPFromQuestion(question);
        setChartData({ driver, year, gp });
        setShowChart(true);
      }
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
          placeholder="Ask about F1... Examples:
• 'Who was fastest in 2024?'
• 'What was Verstappen's fastest lap in Miami 2024?'
• 'Show me Hamilton's lap times at Monaco 2023'
• 'Compare Verstappen and Norris lap times'"
          style={{ width: "600px", padding: "10px", fontSize: "16px" }}
          onKeyPress={(e) => e.key === 'Enter' && askGeneral()}
        />
      </div>
      <div style={{ marginTop: "10px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
        <button 
          onClick={askStrategy} 
          disabled={loading}
          style={{ padding: "10px 20px", cursor: "pointer" }}
        >
          Ask Strategy
        </button>
        <button 
          onClick={askFastestLap} 
          disabled={loading}
          style={{ padding: "10px 20px", cursor: "pointer" }}
        >
          Get Fastest Lap
        </button>
        <button 
          onClick={askGeneral} 
          disabled={loading}
          style={{ padding: "10px 20px", cursor: "pointer", backgroundColor: "#4CAF50", color: "white" }}
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
          wordWrap: "break-word",
          maxHeight: "300px",
          overflowY: "auto"
        }}>
          {loading ? "⏳ Loading..." : answer}
        </pre>
      </div>

      {/* Chart appears when backend says so or for lap time queries */}
      {showChart && (
        <div style={{ marginTop: "40px" }}>
          <h3>📊 Lap Time Visualization</h3>
          <LapTimeChart 
            driver={chartData.driver} 
            year={chartData.year} 
            gp={chartData.gp} 
          />
        </div>
      )}

      {/* Tips for users */}
      <div style={{ marginTop: "30px", padding: "15px", backgroundColor: "#e3f2fd", borderRadius: "5px" }}>
        <h4>💡 Tips:</h4>
        <ul style={{ margin: "5px 0" }}>
          <li><strong>"Who was fastest in 2024?"</strong> - Use <strong>Ask General</strong> button</li>
          <li><strong>"What was Verstappen's fastest lap?"</strong> - Use <strong>Get Fastest Lap</strong> button</li>
          <li><strong>"Compare drivers"</strong> - Use <strong>Ask General</strong> button</li>
          <li>For 2024 data, note that some information may be limited until the season progresses</li>
        </ul>
      </div>
    </div>
  );
}

export default App;