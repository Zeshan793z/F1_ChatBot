from langchain_community.llms import GPT4All
from langchain_core.prompts import PromptTemplate
from pathlib import Path
import warnings
import re

warnings.filterwarnings("ignore", message="Failed to load llamamodel*")

BACKEND_ROOT = Path(__file__).parent.parent
MODEL_PATH = BACKEND_ROOT / "models" / "Meta-Llama-3-8B-Instruct.Q4_0.gguf"

print(f"Looking for model at: {MODEL_PATH}")
print(f"Model exists: {MODEL_PATH.exists()}")

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

print("✅ Loading chat model...")

llm = GPT4All(
    model=str(MODEL_PATH),
    verbose=False
)

# Llama 3 chat format with system prompt
template = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an F1 expert. Answer questions with ONE short sentence only. Never add notes, follow-ups, or explanations. Just the answer.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{question}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

prompt = PromptTemplate(template=template, input_variables=["question"])
chain = prompt | llm

def clean_response(response: str) -> str:
    """Remove Llama 3 special tokens and clean up"""
    # Remove all Llama 3 special tokens
    tokens_to_remove = [
        "<|begin_of_text|>",
        "<|end_of_text|>",
        "<|start_header_id|>",
        "<|end_header_id|>",
        "<|eot_id|>",
        "system",
        "user",
        "assistant"
    ]
    
    for token in tokens_to_remove:
        response = response.replace(token, "")
    
    # Remove any leftover angle bracket content
    response = re.sub(r'<[^>]+>', '', response)
    
    # Remove extra whitespace
    response = re.sub(r'\s+', ' ', response)
    
    # Remove any "A:" prefix
    response = re.sub(r'^A:\s*', '', response, flags=re.IGNORECASE)
    
    # Take only first sentence if there are multiple
    sentences = re.split(r'[.!?]+', response)
    if sentences:
        response = sentences[0].strip()
        # Add period if missing and not empty
        if response and not response.endswith('.'):
            response += '.'
    
    return response.strip()

def chat(question: str) -> str:
    """Answer any F1 question concisely"""
    try:
        response = chain.invoke({"question": question})
        cleaned = clean_response(response)
        
        # If cleaning removed everything, return fallback
        if not cleaned or len(cleaned) < 2:
            # Try to extract answer from raw response
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line and not any(token in line for token in ['<|', 'system', 'user', 'assistant']):
                    if len(line) < 100:  # Reasonable answer length
                        cleaned = line
                        break
        
        return cleaned if cleaned else "I don't know"
        
    except Exception as e:
        return f"Error: {str(e)}"