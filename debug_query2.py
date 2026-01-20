import requests
import json

payload = {
    'user_query': 'Fetch the latest AI news and create ai_news.txt'
}

response = requests.post('http://127.0.0.1:8000/query', json=payload)
result = response.json()

print('Tool Calls Count:', len(result.get('tool_calls_executed', [])))
for i, tc in enumerate(result.get('tool_calls_executed', [])):
    print(f'\nCall {i+1}:')
    print(f'  Server: {tc.get("server")}')
    print(f'  Tool: {tc.get("tool")}')
    print(f'  Args: {json.dumps(tc.get("args", {}), indent=4)}')
