import requests
import json

prompt = {
    "model": "mistral",
    "messages": [{"role": "user", "content": "Vertel me iets over dijkontwerpen in Nederland"}],
    "stream": False
}

response = requests.post("http://localhost:11434/api/chat", json=prompt)
print(response.json()["message"]["content"])