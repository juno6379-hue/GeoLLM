import ast
try:
    with open('d:/An_GeoLLM/services/spatial_analysis_agent/agent.py', 'r', encoding='utf-8') as f:
        ast.parse(f.read())
    print('Syntax OK')
except SyntaxError as e:
    print(f'SyntaxError at line {e.lineno}: {e.msg}')
