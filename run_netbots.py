import subprocess
import sys
import os
import shlex

def run_python_in_terminal(title, command):
    if sys.platform.startswith("win"):
        # Windows: use 'start' in a new cmd window
        subprocess.Popen(f'start "{title}" cmd /K {"python " + command}', shell=True)
    elif sys.platform == "darwin":
        # ---- macOS ---------------------------------------------------------
        cwd        = os.getcwd()                     # keep same working dir
        shell_cmd  = f'cd {shlex.quote(cwd)} && python3 {command}'

        # Escape double-quotes that might appear inside shell_cmd
        osa_cmd    = shell_cmd.replace('"', r'\"')

        subprocess.Popen([
            "osascript",            # one-liner AppleScript
            "-e", f'tell application "Terminal" to activate',
            "-e", f'tell application "Terminal" to do script "{osa_cmd}"'
        ], check=True)
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
