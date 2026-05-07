# import fastf1
# from langchain_community.llms import GPT4All
# from langchain_core.prompts import PromptTemplate
# from pathlib import Path
# import os

# # Path to Meta-Llama model 
# MODEL_PATH = "D:/Python_Project/f1_chatbot/models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"

# # Initialize GPT4All with Meta-Llama
# llm = GPT4All(model=MODEL_PATH, verbose=True)

# # Modern prompt template (LCEL style)
# template = """
# You are an F1 assistant. Use the following race data when available.
# If no data is provided, answer from general F1 knowledge.

# Question: {question}
# Data: {data}
# """

# prompt = PromptTemplate(template=template, input_variables=["question", "data"])
# chain = prompt | llm

# # FIX 1: Create cache directory if it doesn't exist
# cache_dir = Path("D:/Python_Project/f1_chatbot/data/fastf1_cache")
# cache_dir.mkdir(parents=True, exist_ok=True)  # This creates the directory
# fastf1.Cache.enable_cache(str(cache_dir))

# print("✅ FastF1 cache enabled at:", cache_dir)

# try:
#     # Load the session
#     print("📊 Loading Miami GP 2023 data...")
#     session = fastf1.get_session(2023, "Miami", "R")
#     session.load()
#     print("✅ Session loaded successfully")
    
#     # Get Verstappen's laps
#     verstappen_laps = session.laps.pick_driver("VER")
    
#     # Get the fastest lap
#     fastest_lap = verstappen_laps.pick_fastest()
    
#     # Convert LapTime to a readable string
#     lap_time_seconds = fastest_lap['LapTime'].total_seconds()
#     lap_time_str = f"{lap_time_seconds:.3f} seconds"
    
#     # Optional: Get additional useful info
#     lap_number = fastest_lap['LapNumber']
#     compound = fastest_lap['Compound']
    
#     # Prepare data for the LLM
#     data = f"Verstappen's fastest lap: Lap {lap_number} - {lap_time_str} on {compound} tires."
    
#     # Ask the question
#     question = "What was Verstappen's fastest lap in Miami GP 2023?"
    
#     # Run the chain
#     print("🤔 Generating response...")
#     response = chain.invoke({"question": question, "data": data})
#     print("\n🤖 F1 Chatbot Response:", response)
    
# except Exception as e:
#     print(f"❌ Error loading session data: {e}")
#     print("Falling back to general knowledge...")
    
#     # Fallback without FastF1 data
#     question = "What was Verstappen's fastest lap in Miami GP 2023?"
#     data = "No race data available."
#     response = chain.invoke({"question": question, "data": data})
#     print("\n🤖 F1 Chatbot Response:", response)


import fastf1
from langchain_community.llms import GPT4All
from langchain_core.prompts import PromptTemplate
from pathlib import Path
import warnings
import os

# Suppress DLL warnings
warnings.filterwarnings("ignore", message="Failed to load llamamodel*")
warnings.filterwarnings("ignore", message="pick_driver is deprecated")

# Set absolute paths consistently
PROJECT_ROOT = Path("D:/Python_Project/f1_chatbot").resolve()
MODEL_PATH = PROJECT_ROOT / "models" / "Meta-Llama-3-8B-Instruct.Q4_0.gguf"
CACHE_DIR = PROJECT_ROOT / "data" / "fastf1_cache"

# Verify model exists
if not MODEL_PATH.exists():
    print(f"❌ Model not found at: {MODEL_PATH}")
    exit(1)

print(f"✅ Model found at: {MODEL_PATH}")

# Initialize GPT4All with absolute path as string
llm = GPT4All(model=str(MODEL_PATH), verbose=True)

# Prompt template
template = """
You are an F1 assistant. Use the following race data when available.
If no data is provided, answer from general F1 knowledge.

Question: {question}
Data: {data}
"""

prompt = PromptTemplate(template=template, input_variables=["question", "data"])
chain = prompt | llm

# Create cache directory
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

print(f"✅ FastF1 cache enabled at: {CACHE_DIR}")

try:
    # Load the session
    print("📊 Loading Miami GP 2023 data...")
    session = fastf1.get_session(2023, "Miami", "R")
    session.load()
    print("✅ Session loaded successfully")
    
    # FIX: Use pick_drivers instead of pick_driver (deprecated)
    verstappen_laps = session.laps.pick_drivers(["VER"])  # Note: pick_drivers (plural) with list
    
    if len(verstappen_laps) == 0:
        print("⚠️ No laps found for VER")
        fastest_lap = None
    else:
        fastest_lap = verstappen_laps.pick_fastest()
    
    if fastest_lap is not None and not fastest_lap.empty:
        # Convert LapTime to a readable string
        lap_time_seconds = fastest_lap['LapTime'].total_seconds()
        lap_time_str = f"{lap_time_seconds:.3f} seconds"
        
        # Additional info
        lap_number = fastest_lap['LapNumber']
        compound = fastest_lap['Compound']
        
        # Prepare data for the LLM
        data = f"Verstappen's fastest lap: Lap {lap_number} - {lap_time_str} on {compound} tires."
        
        # Ask the question
        question = "What was Verstappen's fastest lap in Miami GP 2023?"
        
        # Run the chain
        print("🤔 Generating response...")
        response = chain.invoke({"question": question, "data": data})
        print("\n🤖 F1 Chatbot Response:", response)
    else:
        print("⚠️ No fastest lap data found")
        
except Exception as e:
    print(f"❌ Error loading session data: {e}")
    import traceback
    traceback.print_exc()