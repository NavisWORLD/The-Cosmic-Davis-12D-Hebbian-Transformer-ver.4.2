import ollama
import sys

models = ["llama3.1:8b", "llama3.2", "llama3.2:latest", "deepseek-r1:8b", "phi3"]
for m in models:
    try:
        res = ollama.chat(model=m, messages=[{'role': 'user', 'content': 'hi'}])
        print(f"{m}: Success")
    except Exception as e:
        print(f"{m}: Error {e}")
