import subprocess
import sys

try:
    result = subprocess.run(
        [sys.executable, "manage.py", "check"],
        capture_output=True,
        text=True,
        cwd="/home/ramin/kidsmap"
    )
    with open("check_output.txt", "w") as f:
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\nSTDERR:\n")
        f.write(result.stderr)
        f.write("\nEXIT CODE: ")
        f.write(str(result.returncode))
except Exception as e:
    with open("check_output.txt", "w") as f:
        f.write(str(e))
