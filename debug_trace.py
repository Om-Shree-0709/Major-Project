import requests
import json
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG)

payload = {
    'user_query': 'Fetch the latest AI news and create ai_news.txt'
}

response = requests.post('http://127.0.0.1:8000/query', json=payload)
result = response.json()

print('=== RESPONSE ===')
print('Final Answer:', result.get('final_answer', '')[:100])
print('Tool Calls:', len(result.get('tool_calls_executed', [])))
for tc in result.get('tool_calls_executed', []):
    print(f"  - {tc.get('server')}.{tc.get('tool')}")
