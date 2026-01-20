import requests
import json

payload = {
    'user_query': 'Fetch the latest AI news and create ai_news.txt'
}

response = requests.post('http://127.0.0.1:8000/query', json=payload)
result = response.json()

print('=== QUERY RESULT DEBUG ===')
print('Final Answer:', result.get('final_answer', 'None')[:200])
print()
print('Tool Calls Made:')
for tc in result.get('tool_calls_executed', []):
    server = tc.get('server')
    tool = tc.get('tool')
    args = tc.get('args', {})
    tool_result = tc.get('result', {})
    
    print(f'\n  Tool: {server}.{tool}')
    print(f'  Args: {json.dumps(args, indent=4)[:150]}')
    print(f'  Result: {str(tool_result)[:150]}')
