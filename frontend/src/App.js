import React, { useState } from "react";
import LapTimeChart from "./components/LapTimeChart";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const [chartData, setChartData] = useState({ driver: "VER", year: 2023, gp: "Miami" });

  // Parse driver from question
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
    return null;
  };

  // Parse year from question
  const parseYearFromQuestion = (questionText) => {
    const yearMatch = questionText.match(/\b(20\d{2})\b/);
    return yearMatch ? parseInt(yearMatch[0]) : new Date().getFullYear();
  };

  // Check if question asks about specific GP
  const parseGPFromQuestion = (questionText) => {
    const upperQuestion = questionText.toUpperCase();
    const gps = {
      'Miami': ['MIAMI', 'MIAMI GP', 'MIAMI GRAND PRIX'],
      'Monaco': ['MONACO', 'MONACO GP', 'MONACO GRAND PRIX'],
      'Silverstone': ['SILVERSTONE', 'BRITISH GP', 'BRITISH GRAND PRIX'],
      'Spa': ['SPA', 'BELGIAN GP', 'BELGIAN GRAND PRIX'],
      'Monza': ['MONZA', 'ITALIAN GP', 'ITALIAN GRAND PRIX'],
      'Singapore': ['SINGAPORE', 'SINGAPORE GP'],
      'Suzuka': ['SUZUKA', 'JAPANESE GP'],
      'Austin': ['AUSTIN', 'COTA', 'US GP'],
      'Abu Dhabi': ['ABU DHABI', 'YAS MARINA']
    };
    
    for (const [gp, aliases] of Object.entries(gps)) {
      for (const alias of aliases) {
        if (upperQuestion.includes(alias)) {
          return gp;
        }
      }
    }
    return null; // Return null if no specific GP mentioned
  };

  // Check if question is asking about season-wide performance
  const isSeasonWideQuestion = (questionText) => {
    const lowerQuestion = questionText.toLowerCase();
    const seasonIndicators = [
      'season', 'whole season', 'this year', 'overall fastest', 
      'not in', 'not at', 'all races', 'every race'
    ];
    // Check for negation of specific GP
    const hasNegation = lowerQuestion.includes('not in') || lowerQuestion.includes('not at');
    const hasGpMention = parseGPFromQuestion(questionText) !== null;
    
    return (hasNegation && !hasGpMention) || 
           seasonIndicators.some(indicator => lowerQuestion.includes(indicator));
  };

  const askFastestLap = async () => {
    if (!question) {
      setAnswer("Please enter a question first!");
      return;
    }
    
    setLoading(true);
    setAnswer("Loading data...");
    setShowChart(false);
    
    const driver = parseDriverFromQuestion(question) || "VER";
    const year = parseYearFromQuestion(question);
    const specificGP = parseGPFromQuestion(question);
    const isSeasonWide = isSeasonWideQuestion(question);
    
    // Handle season-wide questions
    if (isSeasonWide || specificGP === null) {
      setAnswer(
        `🏎️ ${driver} Performance in ${year} Season:\n\n` +
        `For season-wide stats (fastest laps across all races), please use the "Ask General" button.\n\n` +
        `💡 Try asking:\n` +
        `• "Who had the most fastest laps in ${year}?"\n` +
        `• "Compare ${driver}'s performance across ${year}"\n` +
        `• "What was the overall fastest lap of the ${year} season?"\n\n` +
        `📊 Current data shows ${driver} at Miami GP:\n` +
        `• Lap Time: 91.261 seconds\n` +
        `• Lap Number: 48\n` +
        `• Tire: HARD`
      );
      setLoading(false);
      return;
    }
    
    // Handle specific GP queries
    try {
      const url = `http://localhost:8000/fastest-lap?year=${year}&gp=${specificGP}&driver=${driver}`;
      const res = await fetch(url);
      const data = await res.json();
      
      if (data.lap_data) {
        setAnswer(
          `🏎️ Fastest Lap for ${driver} at ${specificGP} GP ${year}:\n\n` +
          `• Lap Number: ${data.lap_data.lap_number}\n` +
          `• Lap Time: ${data.lap_data.lap_time}\n` +
          `• Tire Compound: ${data.lap_data.compound}`
        );
        setChartData({ driver, year, gp: specificGP });
        setShowChart(true);
      } else {
        setAnswer(`No data found for ${driver} at ${specificGP} GP ${year}.`);
      }
    } catch (err) {
      setAnswer(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Add this to your App component
const askSeasonPerformance = async () => {
  if (!question) {
    setAnswer("Please enter a question first!");
    return;
  }
  
  setLoading(true);
  setAnswer("Loading season data...");
  setShowChart(false);
  
  const driver = parseDriverFromQuestion(question) || "VER";
  const year = parseYearFromQuestion(question) || 2024;
  
  try {
    const url = `http://localhost:8000/driver-season-performance?year=${year}&driver=${driver}`;
    const res = await fetch(url);
    const data = await res.json();
    
    if (data.error) {
      setAnswer(`Error: ${data.error}`);
    } else if (data.races && data.races.length > 0) {
      setAnswer(
        `🏎️ ${driver} Performance in ${year} Season:\n\n` +
        `• Races Analyzed: ${data.races.length}\n` +
        `• Best Lap: ${data.best_lap_time_formatted || 'N/A'} at ${data.best_lap_gp || 'N/A'}\n` +
        `• Average Lap Time: ${data.avg_lap_time ? data.avg_lap_time.toFixed(3) : 'N/A'} seconds\n` +
        `• Total Fastest Laps Set: ${data.fastest_laps}\n\n` +
        `📊 Race-by-Race Fastest Laps:\n` +
        data.races.map(r => `  • ${r.gp}: ${r.fastest_lap} (Lap ${r.lap_number}, ${r.compound} tires)`).join('\n')
      );
      setChartData({ driver, year, gp: "All Races" });
      setShowChart(true);
    } else {
      setAnswer(`No data found for ${driver} in ${year}. Make sure the season has been cached.`);
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
      
      // Check if response might benefit from chart data
      const lowerQuestion = question.toLowerCase();
      if ((lowerQuestion.includes("fastest lap") || lowerQuestion.includes("lap time")) && 
          (lowerQuestion.includes("ver") || lowerQuestion.includes("max"))) {
        const driver = parseDriverFromQuestion(question) || "VER";
        const year = parseYearFromQuestion(question);
        const gp = parseGPFromQuestion(question) || "Miami";
        setChartData({ driver, year, gp });
        setShowChart(true);
      }
    } catch (err) {
      setAnswer(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const askStrategy = async () => {
    if (!question) {
      setAnswer("Please enter a question first!");
      return;
    }
    setLoading(true);
    setAnswer("Loading...");
    setShowChart(false);
    
    const driver = parseDriverFromQuestion(question) || "VER";
    const year = parseYearFromQuestion(question);
    const gp = parseGPFromQuestion(question) || "Miami";
    
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

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>🏎️ F1 Chatbot</h1>
      <div style={{ marginBottom: "10px" }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Examples:
• Who was fastest in 2024 overall?
• What was Verstappen's fastest lap at Monaco 2024?
• Best driver of 2024 season?
• Compare Hamilton and Verstappen 2024"
          style={{ width: "600px", padding: "10px", fontSize: "16px" }}
          onKeyPress={(e) => e.key === 'Enter' && askGeneral()}
        />
      </div>
      <div style={{ marginTop: "10px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
        <button onClick={askStrategy} disabled={loading} style={{ padding: "10px 20px", cursor: "pointer" }}>
          Ask Strategy
        </button>
        <button onClick={askFastestLap} disabled={loading} style={{ padding: "10px 20px", cursor: "pointer" }}>
          Get Fastest Lap
        </button>
        <button onClick={askGeneral} disabled={loading} style={{ padding: "10px 20px", cursor: "pointer", backgroundColor: "#4CAF50", color: "white" }}>
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

      <div style={{ marginTop: "30px", padding: "15px", backgroundColor: "#e3f2fd", borderRadius: "5px" }}>
        <h4>💡 For Season-Wide Questions (like "fastest in 2024"):</h4>
        <ul style={{ margin: "5px 0" }}>
          <li>✅ <strong>Use the "Ask General" (green) button</strong> - This uses the AI model's knowledge</li>
          <li>✅ The "Get Fastest Lap" button is for specific race queries</li>
          <li>✅ Example: "Who was the fastest driver overall in 2024?" → Use Ask General</li>
          <li>✅ Example: "Verstappen's fastest lap at Monaco 2024" → Use Get Fastest Lap</li>
        </ul>
      </div>
    </div>
  );
}

export default App;