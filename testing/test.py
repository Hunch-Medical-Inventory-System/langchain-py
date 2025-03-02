from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen2.5:0.5b", temperature=0.5, verbose=True)

print(llm.invoke("hello"))