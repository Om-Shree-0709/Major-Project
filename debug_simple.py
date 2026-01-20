import requests
import json

payload = {
    'user_query': 'Fetch the latest AI news and create ai_news.txt'
}

response = requests.post('http://127.0.0.1:8000/query', json=payload)
result = response.json()

print('Final Answer:')
print(result.get('final_answer', 'None'))
print()
print('Tool Calls Count:', len(result.get('tool_calls_executed', [])))
