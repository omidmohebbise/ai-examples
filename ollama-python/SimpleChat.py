import requests

def ollama_query(prompt):
    url = "http://localhost:11411/v1/ask"  # Ollama's local API endpoint
    headers = {"Content-Type": "application/json"}
    data = {"input": prompt}

    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Example usage
result = ollama_query("What is the capital of France?")
print(result)