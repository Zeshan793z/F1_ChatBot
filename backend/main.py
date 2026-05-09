from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.agents.data_agent import get_driver_fastest_lap
from backend.agents.strategy_agent import explain_strategy
from backend.agents.chat_agent import chat

app = FastAPI(title="F1 Chatbot API", description="API for F1 race data and strategy analysis")

# Allow CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "F1 Chatbot API is running",
        "status": "healthy",
        "endpoints": [
            "/fastest-lap?year=2023&gp=Miami&driver=VER",
            "/strategy?year=2023&gp=Miami&driver=VER&question=...",
            "/chat?question=..."
        ]
    }

@app.get("/fastest-lap")
def fastest_lap(year: int, gp: str, driver: str):
    """Get the fastest lap data for a specific driver at a Grand Prix"""
    lap_data = get_driver_fastest_lap(year, gp, driver)
    return {"driver": driver, "year": year, "gp": gp, "lap_data": lap_data}

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
    """General F1 chat endpoint"""
    answer = chat(question)
    return {"question": question, "answer": answer}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)