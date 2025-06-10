import subprocess
import sys
import os

def run_python_in_terminal(title, command):
    if sys.platform.startswith("win"):
        # Windows: use 'start' in a new cmd window
        subprocess.Popen(f'start "{title}" cmd /K {"python " + command}', shell=True)
    elif sys.platform == "darwin":
        # macOS: use AppleScript to open new Terminal tabs or windows
        apple_script = f'''
        tell application "Terminal"
            activate
            do script python3 "{command}"
        end tell
        '''
        subprocess.Popen(["osascript", "-e", apple_script])
    else:
        # Linux: try gnome-terminal or xterm
        command = f'python3 {command}'
        try:
            subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f'{command}; exec bash'])
        except FileNotFoundError:
            subprocess.Popen(["xterm", "-e", f'{command}; bash'])

# Set working directory to script location
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Launch the processes
run_python_in_terminal("NetBot-Server", "src/netbots_server.py -p 20000 -stepsec 0.05 -games 10 -stepmax 3000")
run_python_in_terminal("NetBot-Viewer", "src/netbots_viewer.py -p 20001 -sp 20000")
# run_python_in_terminal("hideincorner", "robots/hideincorner.py -p 20002 -sp 20000")
run_python_in_terminal("circler1", "robots/circler.py -p 20002 -sp 20000")
run_python_in_terminal("lighthouse", "robots/lighthouse.py -p 20003 -sp 20000")
run_python_in_terminal("scaredycat", "robots/scaredycat.py -p 20004 -sp 20000")
run_python_in_terminal("circler2", "robots/circler.py -p 20005 -sp 20000")
# run_python_in_terminal("wallbanger", "robots/wallbanger.py -p 20005 -sp 20000")
