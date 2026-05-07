from langchain_community.llms import GPT4All

MODEL_PATH = "./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
llm = GPT4All(model=MODEL_PATH, verbose=False)

def explain_strategy(data, question):
    prompt = f"""
    You are an F1 strategy analyst.
    Use the following race data to explain strategy decisions.

    Data: {data}
    Question: {question}
    """
    return llm.invoke(prompt)
