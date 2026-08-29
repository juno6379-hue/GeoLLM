import sys
with open('d:/An_GeoLLM/services/spatial_analysis_agent/agent.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if 185 <= i <= 209:
        # Increase indentation by 4 spaces
        new_lines.append('    ' + line if line.strip() else line)
    else:
        new_lines.append(line)

with open('d:/An_GeoLLM/services/spatial_analysis_agent/agent.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
