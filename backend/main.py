from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

# Use relative imports (note the dots before agents)
from .agents.data_agent import get_driver_fastest_lap, get_season_fastest_laps, get_season_driver_performance
from .agents.strategy_agent import explain_strategy
from .agents.chat_agent import chat
from .agents.rag_agent import F1RAGAgent

app = FastAPI(title="F1 Chatbot API")

# Initialize RAG agent
rag_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize RAG agent on startup"""
    global rag_agent
    print("🚀 Initializing F1 RAG Agent...")
    rag_agent = F1RAGAgent()
    rag_agent.initialize_knowledge_base()
    print("✅ F1 RAG Agent ready!")

# Allow CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "F1 Chatbot API is running",
        "status": "healthy",
        "rag_enabled": rag_agent is not None,
        "endpoints": [
            "/fastest-lap?year=2023&gp=Miami&driver=VER",
            "/season-fastest-laps?year=2024&driver=VER",
            "/driver-season-performance?year=2024&driver=VER",
            "/multiple-seasons?years=2023,2024&driver=VER",
            "/strategy?year=2023&gp=Miami&driver=VER&question=...",
            "/chat?question=... (now with RAG!)",
            "/chat/legacy?question=... (original without RAG)"
        ]
    }

@app.get("/fastest-lap")
def fastest_lap(year: int, gp: str, driver: str):
    """Get the fastest lap data for a specific driver at a Grand Prix"""
    lap_data = get_driver_fastest_lap(year, gp, driver)
    return {"driver": driver, "year": year, "gp": gp, "lap_data": lap_data}

@app.get("/season-fastest-laps")
def season_fastest_laps(
    year: int, 
    driver: Optional[str] = Query(None, description="Optional driver code (e.g., VER, HAM)")
):
    """
    Get fastest lap data for all races in a season
    Optionally filter by driver
    """
    try:
        results = get_season_fastest_laps(year, driver)
        return {
            "year": year,
            "driver_filter": driver,
            "total_races": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/driver-season-performance")
def driver_season_performance(year: int, driver: str):
    """
    Get comprehensive performance data for a driver across a season
    """
    try:
        performance = get_season_driver_performance(year, driver)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/multiple-seasons")
def multiple_seasons(
    years: str, 
    driver: Optional[str] = Query(None, description="Optional driver code")
):
    """
    Get data across multiple seasons
    Example: /multiple-seasons?years=2023,2024&driver=VER
    """
    try:
        year_list = [int(y.strip()) for y in years.split(',')]
        results = {}
        
        for year in year_list:
            if driver:
                results[str(year)] = get_season_driver_performance(year, driver)
            else:
                results[str(year)] = get_season_fastest_laps(year)
        
        return {
            "years": year_list,
            "driver": driver,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategy")
def strategy(year: int, gp: str, driver: str, question: str):
    """Get strategy explanation for a driver at a specific GP"""
    lap_data = get_driver_fastest_lap(year, gp, driver)
    if lap_data:
        data_str = f"Lap {lap_data['lap_number']} - {lap_data['lap_time']} on {lap_data['compound']} tires."
    else:
        data_str = "No lap data found."
    response = explain_strategy(data_str, question)
    return {"response": response}

@app.get("/chat")
def chat_endpoint(question: str):
    """General F1 chat endpoint with RAG (Intelligent, F1-focused)"""
    if rag_agent is None:
        return {
            "question": question, 
            "answer": "RAG agent not initialized yet. Please try again in a moment.",
            "mode": "error"
        }
    
    answer = rag_agent.chat(question)
    return {
        "question": question, 
        "answer": answer,
        "mode": "rag"
    }

@app.get("/chat/legacy")
def chat_legacy_endpoint(question: str):
    """Legacy chat endpoint without RAG (original behavior)"""
    answer = chat(question)
    return {
        "question": question, 
        "answer": answer,
        "mode": "legacy"
    }

@app.get("/chat/health")
def chat_health():
    """Check RAG agent status"""
    if rag_agent is None:
        return {"status": "not_initialized", "rag_enabled": False}
    return {
        "status": "ready", 
        "rag_enabled": True,
        "knowledge_base_loaded": rag_agent.is_initialized
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)