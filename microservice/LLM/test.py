import requests
import json


url = 'http://localhost:11434/api/generate'

data = {
    "model": "llama3",
    "prompt": "Why is the sky blue?"
}

response = requests.post(url, json=data, stream=True)

if response.status_code == 200:
    for line in response.iter_lines():
        if line:
            json_data = json.loads(line.decode('utf-8'))
            print(json_data) 
else:
    print("Failed to get valid response, status code:", response.status_code)
