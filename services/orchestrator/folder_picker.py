import subprocess
import json
import os

LAST_DIR_FILE = os.path.join(os.path.dirname(__file__), ".last_dir.txt")

start_dir = "d:\\"
if os.path.isfile(LAST_DIR_FILE):
    try:
        with open(LAST_DIR_FILE, "r", encoding="utf-8") as f:
            saved_dir = f.read().strip()
            if os.path.isdir(saved_dir):
                start_dir = saved_dir
    except:
        pass

ps_script = f"""
Add-Type -AssemblyName System.windows.forms
$form = New-Object System.Windows.Forms.Form
$form.TopMost = $true
$form.ShowInTaskbar = $false
$form.WindowState = [System.Windows.Forms.FormWindowState]::Minimized

$f = New-Object System.Windows.Forms.FolderBrowserDialog
$f.SelectedPath = "{start_dir}"
$f.Description = "GeoLLM - 폴더 선택"
$f.ShowNewFolderButton = $false
[System.Windows.Forms.Application]::EnableVisualStyles()
$form.Show()
$form.BringToFront()
if ($f.ShowDialog($form) -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output $f.SelectedPath
}}
$form.Dispose()
"""

result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
folder = result.stdout.strip()

final_paths = []
if folder and os.path.isdir(folder):
    parent_dir = os.path.dirname(folder)
    try:
        with open(LAST_DIR_FILE, "w", encoding="utf-8") as f:
            f.write(parent_dir)
    except:
        pass
    
    final_paths.append(folder.replace("\\", "/"))

print(json.dumps(final_paths))
