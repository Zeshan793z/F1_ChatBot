import React, { useState } from "react";
import LapTimeChart from "./components/LapTimeChart";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const [chartData, setChartData] = useState({ driver: "VER", year: 2023, gp: "Miami" });
  const [selectedMode, setSelectedMode] = useState(null);

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
    return null;
  };

  // Check if question is asking about season-wide performance
  const isSeasonWideQuestion = (questionText) => {
    const lowerQuestion = questionText.toLowerCase();
    const seasonIndicators = [
      'season', 'whole season', 'this year', 'overall fastest', 
      'not in', 'not at', 'all races', 'every race'
    ];
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
    setSelectedMode('fastest');
    setAnswer("🔍 Searching for fastest lap data...");
    setShowChart(false);
    
    const driver = parseDriverFromQuestion(question) || "VER";
    const year = parseYearFromQuestion(question);
    const specificGP = parseGPFromQuestion(question);
    const isSeasonWide = isSeasonWideQuestion(question);
    
    if (isSeasonWide || specificGP === null) {
      setAnswer(
        `🏎️ **${driver} Performance in ${year} Season**\n\n` +
        `For season-wide stats, please use the **"Ask General"** button.\n\n` +
        `💡 **Try asking:**\n` +
        `• "Who had the most fastest laps in ${year}?"\n` +
        `• "Compare ${driver}'s performance across ${year}"\n` +
        `• "What was the overall fastest lap of the ${year} season?"\n\n` +
        `📊 **Current data shows ${driver} at Miami GP:**\n` +
        `• Lap Time: 91.261 seconds\n` +
        `• Lap Number: 48\n` +
        `• Tire: HARD`
      );
      setLoading(false);
      return;
    }
    
    try {
      const url = `http://localhost:8000/fastest-lap?year=${year}&gp=${specificGP}&driver=${driver}`;
      const res = await fetch(url);
      const data = await res.json();
      
      if (data.lap_data) {
        setAnswer(
          `🏎️ **Fastest Lap for ${driver} at ${specificGP} GP ${year}**\n\n` +
          `• **Lap Number:** ${data.lap_data.lap_number}\n` +
          `• **Lap Time:** ${data.lap_data.lap_time}\n` +
          `• **Tire Compound:** ${data.lap_data.compound}`
        );
        setChartData({ driver, year, gp: specificGP });
        setShowChart(true);
      } else {
        setAnswer(`❌ No data found for ${driver} at ${specificGP} GP ${year}.`);
      }
    } catch (err) {
      setAnswer(`⚠️ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const askSeasonPerformance = async () => {
    if (!question) {
      setAnswer("Please enter a question first!");
      return;
    }
    
    setLoading(true);
    setSelectedMode('general');
    setAnswer("📊 Analyzing season performance...");
    setShowChart(false);
    
    const driver = parseDriverFromQuestion(question) || "VER";
    const year = parseYearFromQuestion(question) || 2024;
    
    try {
      const url = `http://localhost:8000/driver-season-performance?year=${year}&driver=${driver}`;
      const res = await fetch(url);
      const data = await res.json();
      
      if (data.error) {
        setAnswer(`❌ Error: ${data.error}`);
      } else if (data.races && data.races.length > 0) {
        setAnswer(
          `🏎️ **${driver} Performance in ${year} Season**\n\n` +
          `• **Races Analyzed:** ${data.races.length}\n` +
          `• **Best Lap:** ${data.best_lap_time_formatted || 'N/A'} at ${data.best_lap_gp || 'N/A'}\n` +
          `• **Average Lap Time:** ${data.avg_lap_time ? data.avg_lap_time.toFixed(3) : 'N/A'} seconds\n` +
          `• **Total Fastest Laps Set:** ${data.fastest_laps}\n\n` +
          `📊 **Race-by-Race Fastest Laps:**\n` +
          data.races.map(r => `  • ${r.gp}: ${r.fastest_lap} (Lap ${r.lap_number}, ${r.compound} tires)`).join('\n')
        );
        setChartData({ driver, year, gp: "All Races" });
        setShowChart(true);
      } else {
        setAnswer(`❌ No data found for ${driver} in ${year}. Make sure the season has been cached.`);
      }
    } catch (err) {
      setAnswer(`⚠️ Error: ${err.message}`);
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
    setSelectedMode('general');
    setAnswer("🤔 Thinking...");
    setShowChart(false);
    try {
      const url = `http://localhost:8000/chat?question=${encodeURIComponent(question)}`;
      const res = await fetch(url);
      const data = await res.json();
      setAnswer(data.answer || JSON.stringify(data, null, 2));
      
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
      setAnswer(`⚠️ Error: ${err.message}`);
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
    setSelectedMode('strategy');
    setAnswer("🏁 Analyzing race strategy...");
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
      setAnswer(`⚠️ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      askGeneral();
    }
  };

  const handleQuickQuery = (query) => {
    setQuestion(query);
    setTimeout(() => askGeneral(), 100);
  };

  return (
    <div className="app-container">
      <div className="glass-card">
        {/* Header */}
        <div className="header">
          <span className="flag">🏎️</span>
          <h1>F1 Chatbot</h1>
          <span className="version-badge">v2.0</span>
        </div>

        {/* Query Input */}
        <div className="query-area">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything about F1... (e.g., 'Who was fastest in 2024?')"
            onKeyPress={handleKeyPress}
            className="query-input"
          />
          <button 
            onClick={askGeneral} 
            className="ask-button"
            disabled={loading}
          >
            ⏎ Ask
          </button>
        </div>

        {/* Quick Action Pills */}
        <div className="pill-grid">
          <button 
            className={`pill strategy ${selectedMode === 'strategy' ? 'active' : ''}`}
            onClick={askStrategy}
            disabled={loading}
          >
            <span className="badge strategy-badge"></span>
            Ask Strategy
          </button>
          <button 
            className={`pill fastest ${selectedMode === 'fastest' ? 'active' : ''}`}
            onClick={askFastestLap}
            disabled={loading}
          >
            <span className="badge fastest-badge"></span>
            Get Fastest Lap
          </button>
          <button 
            className={`pill general ${selectedMode === 'general' ? 'active' : ''}`}
            onClick={askGeneral}
            disabled={loading}
          >
            <span className="badge general-badge"></span>
            Ask General
          </button>
        </div>

        {/* Quick Examples */}
        <div className="quick-examples">
          <span className="examples-label">💡 Quick examples:</span>
          <button className="example-chip" onClick={() => handleQuickQuery("Who was fastest in 2024 overall?")}>
            Fastest 2024
          </button>
          <button className="example-chip" onClick={() => handleQuickQuery("Verstappen's fastest lap at Monaco 2024")}>
            Verstappen Monaco
          </button>
          <button className="example-chip" onClick={() => handleQuickQuery("Best strategy for Monaco GP?")}>
            Monaco Strategy
          </button>
        </div>

        {/* Response Card */}
        <div className="response-box">
          <div className="response-label">
            {loading ? '⏳ Loading...' : '💬 Response'}
          </div>
          <div className="response-text">
            {loading ? (
              <div className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            ) : (
              answer || <span className="placeholder">Ask me anything about F1 🏁</span>
            )}
          </div>
        </div>

        {/* Chart Section */}
        {showChart && (
          <div className="chart-section">
            <LapTimeChart 
              driver={chartData.driver} 
              year={chartData.year} 
              gp={chartData.gp} 
            />
          </div>
        )}

        {/* Help Footer */}
        <div className="help-footer">
          <div className="help-item">
            <span className="dot green"></span>
            <span><strong>Ask General</strong> – Season-wide questions</span>
          </div>
          <div className="help-item">
            <span className="dot orange"></span>
            <span><strong>Fastest Lap</strong> – Specific race queries</span>
          </div>
          <div className="help-item">
            <span className="dot blue"></span>
            <span><strong>Strategy</strong> – Race tactics &amp; analysis</span>
          </div>
          <div className="help-item">
            <span className="dot red"></span>
            <span>⚠️ 2026 data not yet available</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;