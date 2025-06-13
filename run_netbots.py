import subprocess
import sys
import os
import shlex

PY = sys.executable                    # ← interpreter inside the current env
CWD = os.getcwd()

def run_python_in_terminal(title, command):

    if sys.platform.startswith("win"):
        # Windows: one-liner passed to the shell so `start` is understood
        cmdline = (
            f'start "{title}" cmd /K '           # open titled window, keep open
            f'cd /d "{CWD}" ^&^& '               # stay in the repo folder
            f'"{PY}" {command}'                  # run with current env’s Python
        )
        subprocess.Popen(cmdline, shell=True)    # <-- STRING, not list! ✔︎
    elif sys.platform == "darwin":
        # ---- macOS ---------------------------------------------------------
        cwd        = os.getcwd()                     # keep same working dir
        shell_cmd  = f'cd {shlex.quote(cwd)} && python3 {command}'

        # Escape double-quotes that might appear inside shell_cmd
        osa_cmd    = shell_cmd.replace('"', r'\"')

        # <-- the important change ------------------------------
        subprocess.run(
            [
                "osascript",
                "-e", 'tell application "Terminal" to activate',
                "-e", f'tell application "Terminal" to do script "{osa_cmd}"'
            ],
            check=True                                    # raises if exit≠0
        )
        # --------------------------------------------------------
    else:
        shell_cmd = f'cd {shlex.quote(CWD)} && "{PY}" {command}'
        try:
            subprocess.Popen([
                "gnome-terminal", "--", "bash", "-c", f'{shell_cmd}; exec bash'
            ])
        except FileNotFoundError:
            subprocess.Popen([
                "xterm", "-e", f'{shell_cmd}; bash'
            ])

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
