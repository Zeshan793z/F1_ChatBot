from langchain_community.llms import GPT4All
from langchain_core.prompts import PromptTemplate

MODEL_PATH = "./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
llm = GPT4All(model=MODEL_PATH, verbose=False)

template = """
You are an F1 trivia assistant.
Answer the following question clearly and concisely.

Question: {question}
"""

prompt = PromptTemplate(template=template, input_variables=["question"])
chain = prompt | llm

def chat(question):
    return chain.invoke({"question": question})
