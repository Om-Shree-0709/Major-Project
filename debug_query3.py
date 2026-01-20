import requests
import json

payload = {
    'user_query': 'Fetch the latest AI news and create ai_news.txt'
}

response = requests.post('http://127.0.0.1:8000/query', json=payload)
result = response.json()

print('Full Tool Call Details:')
for i, tc in enumerate(result.get('tool_calls_executed', [])):
    print(f'\nCall {i+1}:')
    print(f'  Server: {tc.get("server")}')
    print(f'  Tool: {tc.get("tool")}')
    print(f'  Result type: {type(tc.get("result"))}')
    print(f'  Result keys: {tc.get("result", {}).keys() if isinstance(tc.get("result"), dict) else "N/A"}')
    print(f'  Full result: {json.dumps(tc.get("result"), indent=2)[:500]}')
