import requests
import json

response = requests.post(
    "http://127.0.0.1:8000/query",
    json={"user_query": "List my GitHub repos"}
)
print(json.dumps(response.json(), indent=2))
