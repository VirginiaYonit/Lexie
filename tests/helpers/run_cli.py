# util per eseguire: python main.py <mode> <arg>  e catturare il path PDF
import re, subprocess, sys
from pathlib import Path

PDF_LINE = re.compile(r"^PDF:\s*(.+)$", re.IGNORECASE | re.MULTILINE)

def run_main_and_get_pdf(mode: str, arg: str, cwd: Path) -> Path:
    cmd = [sys.executable, "main.py", mode, arg]
    cp = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    if cp.returncode != 0:
        raise RuntimeError(f"CLI failed ({cp.returncode}):\nSTDOUT:\n{cp.stdout}\nSTDERR:\n{cp.stderr}")
    m = PDF_LINE.search(cp.stdout)
    if not m:
        raise RuntimeError(f"PDF path not found in STDOUT.\nSTDOUT:\n{cp.stdout}\nSTDERR:\n{cp.stderr}")
    return (Path(cwd) / Path(m.group(1))).resolve()
