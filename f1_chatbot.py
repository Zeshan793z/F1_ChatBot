# from langchain_community.llms import GPT4All
# from langchain_core.prompts import PromptTemplate

# MODEL_PATH = "D:/Python_Project/f1_chatbot/models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
# llm = GPT4All(model=MODEL_PATH, verbose=True)

# template = """
# You are an F1 trivia assistant.
# Answer the following question clearly and concisely:

# Question: {question}
# """

# prompt = PromptTemplate(template=template, input_variables=["question"])

# # Modern LCEL chain (no LLMChain needed)
# chain = prompt | llm

# question = "Who won the Formula 1 World Championship in 2021?"
# response = chain.invoke({"question": question})
# print(f"F1 Chatbot response: {response}")



from langchain_community.llms import GPT4All
from langchain_core.prompts import PromptTemplate

MODEL_PATH = "D:/Python_Project/f1_chatbot/models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
llm = GPT4All(model=MODEL_PATH, verbose=True)

# Ultra-simple prompt - no instructions, just Q&A format
template = "Q: {question}\nA:"

prompt = PromptTemplate(template=template, input_variables=["question"])
chain = prompt | llm

question = "Who won the 2021 Formula One World Championship?"
response = chain.invoke({"question": question})
print(f"Response: {response}")