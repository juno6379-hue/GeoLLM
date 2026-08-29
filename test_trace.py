# -*- coding: utf-8 -*-
import httpx
import asyncio
import json

async def run_test():
    async with httpx.AsyncClient() as client:
        print('Starting task...')
        req_body = {
            'query': 'test query',
            'user_id': 'admin',
            'organization_id': 'test',
            'spatial_context': {'map_bounds': [128.0, 34.0, 130.0, 36.0]}
        }
        
        async with client.stream('POST', 'http://localhost:8000/api/v1/tasks/stream', json=req_body) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    print('SSE Event:', data)
                    if data.get('event') == 'started':
                        task_id = data.get('task_id')
                        print(f'Fetching trace for {task_id}')
                        res = await client.get(f'http://localhost:8000/api/v1/tasks/{task_id}')
                        print('GET Response:', res.json())
                    elif data.get('event') == 'node_finished':
                        task_id = data.get('task_id', getattr(client, 'last_task_id', task_id))
                        res = await client.get(f'http://localhost:8000/api/v1/tasks/{task_id}')
                        print(f'GET Response after {data.get("node")}:', res.json())

if __name__ == '__main__':
    asyncio.run(run_test())
