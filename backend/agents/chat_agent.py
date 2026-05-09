# from langchain_community.llms import GPT4All
# from langchain_core.prompts import PromptTemplate

# MODEL_PATH = "./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
# llm = GPT4All(model=MODEL_PATH, verbose=False)

# template = """
# You are an F1 trivia assistant.
# Answer the following question clearly and concisely.

# Question: {question}
# """

# prompt = PromptTemplate(template=template, input_variables=["question"])
# chain = prompt | llm

# def chat(question):
#     return chain.invoke({"question": question})


from langchain_community.llms import GPT4All
from langchain_core.prompts import PromptTemplate
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent
MODEL_PATH = BACKEND_ROOT / "models" / "Meta-Llama-3-8B-Instruct.Q4_0.gguf"

print(f"Looking for model at: {MODEL_PATH}")
print(f"Model exists: {MODEL_PATH.exists()}")

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

print("✅ Loading chat model...")
llm = GPT4All(model=str(MODEL_PATH), verbose=False)

# More explicit instructions to prevent echoing
template = """Answer the following F1 question directly and concisely without repeating the question.

Question: {question}
Answer:"""

prompt = PromptTemplate(template=template, input_variables=["question"])
chain = prompt | llm

def chat(question: str) -> str:
    """Answer general F1 questions"""
    try:
        response = chain.invoke({"question": question})
        # Clean up: remove any "Answer:" prefix if present
        if "Answer:" in response[:20]:
            response = response.split("Answer:", 1)[-1].strip()
        # Also remove any quoted question at the beginning
        lines = response.split('\n')
        if len(lines) > 1 and "?" in lines[0]:
            response = '\n'.join(lines[1:]).strip()
        return response
    except Exception as e:
        return f"Error: {str(e)}"