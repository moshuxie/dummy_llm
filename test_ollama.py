
# 在 test_ollama.py 和 rag_system.py 中使用
from langchain_ollama.llms import OllamaLLM as Ollama
def test_ollama():
    try:
        llm = Ollama(model="llama2")
        response = llm.invoke("Hello, how are you?")
        print("Ollama connection successful!")
        print("Response:", response)
    except Exception as e:
        print("Ollama connection failed:", str(e))

if __name__ == "__main__":
    test_ollama()