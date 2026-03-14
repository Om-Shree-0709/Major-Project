import requests
import time
import sys

# Try to connect to the server
for i in range(10):
    try:
        resp = requests.get('http://127.0.0.1:8000/health', timeout=1)
        if resp.status_code == 200:
            print('Server is running and responding')
            break
    except:
        if i < 9:
            print(f'Waiting for server... attempt {i+1}/10')
            time.sleep(1)
        else:
            print('Server not responding after 10 attempts')
            sys.exit(1)

# Now test the query
payload = {
    'user_query': 'Fetch the latest AI news and create ai_news.txt'
}

print('\nMaking query...')
response = requests.post('http://127.0.0.1:8000/query', json=payload)
result = response.json()

print('Final Answer:', result.get('final_answer', '')[:100])
print('Tool Calls:', len(result.get('tool_calls_executed', [])))
for tc in result.get('tool_calls_executed', []):
    tool_name = tc.get('tool', '')
    server = tc.get('server', '')
    print(f'  - {server}.{tool_name}')

# Check if file was created
print('\nChecking sandbox directory...')
import os
sandbox_dir = 'e:\\Major Project\\backend\\mcp_sandbox'
files = os.listdir(sandbox_dir)
print(f'Files in sandbox: {files}')
if 'ai_news.txt' in files:
    print('✅ ai_news.txt was created!')
    with open(os.path.join(sandbox_dir, 'ai_news.txt')) as f:
        content = f.read()
        print(f'File size: {len(content)} bytes')
        print(f'Content preview: {content[:200]}...')
else:
    print('❌ ai_news.txt was NOT created')
