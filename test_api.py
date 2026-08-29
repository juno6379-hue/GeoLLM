import urllib.request, json

req = urllib.request.Request('http://localhost:8000/api/v1/tasks/stream', 
    data=json.dumps({'query':'침선 분석', 'organization_id':'org1', 'user_id':'user1'}).encode(), 
    headers={'Content-Type': 'application/json'})

with urllib.request.urlopen(req) as response:
    with open('test_api_output.json', 'w', encoding='utf-8') as f:
        for line in response:
            line_str = line.decode('utf-8').strip()
            if line_str.startswith('data: '):
                f.write(line_str[6:] + '\n')
