"""Start the real Streamlit server, check health, and stop only that process."""

import subprocess, sys, time, urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
log = (root / "outputs/server_smoke.log").open("w")
process = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "dashboard/app.py",
        "--server.headless=true",
        "--server.address=127.0.0.1",
        "--server.port=8511",
        "--browser.gatherUsageStats=false",
    ],
    cwd=root,
    stdout=log,
    stderr=subprocess.STDOUT,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
)
try:
    for _ in range(40):
        if process.poll() is not None:
            raise RuntimeError("Server exited; inspect outputs/server_smoke.log")
        try:
            with urllib.request.urlopen(
                "http://127.0.0.1:8511/_stcore/health", timeout=1
            ) as response:
                assert response.status == 200
                print("Streamlit server health: HTTP 200")
                break
        except OSError:
            time.sleep(0.25)
    else:
        raise RuntimeError("Server did not become healthy")
finally:
    process.terminate()
    process.wait(timeout=10)
    log.close()
