# from langchain_community.llms import GPT4All

# MODEL_PATH = "./backend/models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
# llm = GPT4All(model=MODEL_PATH, verbose=False)

# def explain_strategy(data, question):
#     prompt = f"""
#     You are an F1 strategy analyst.
#     Use the following race data to explain strategy decisions.

#     Data: {data}
#     Question: {question}
#     """
#     return llm.invoke(prompt)


from langchain_community.llms import GPT4All
from pathlib import Path

# The model is in backend/models/, not root/models/
BACKEND_ROOT = Path(__file__).parent.parent  # This goes to backend folder
MODEL_PATH = BACKEND_ROOT / "models" / "Meta-Llama-3-8B-Instruct.Q4_0.gguf"

print(f"Looking for model at: {MODEL_PATH}")
print(f"Model exists: {MODEL_PATH.exists()}")

if not MODEL_PATH.exists():
    # If not found, list all files in backend/models for debugging
    models_dir = BACKEND_ROOT / "models"
    if models_dir.exists():
        print(f"\nFiles in {models_dir}:")
        for f in models_dir.iterdir():
            print(f"  - {f.name}")
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

print("✅ Loading model...")
llm = GPT4All(model=str(MODEL_PATH), verbose=False)

def explain_strategy(data: str, question: str) -> str:
    prompt = f"""
You are an expert F1 strategy analyst. Use the provided race data to answer questions about strategy decisions.

Race Data:
{data}

Question: {question}

Provide a clear, concise answer focusing on strategic aspects like tire compounds, pit stops, track position, and race context.
"""
    try:
        return llm.invoke(prompt)
    except Exception as e:
        return f"Error generating strategy explanation: {str(e)}"