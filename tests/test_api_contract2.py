import subprocess
import time
import requests
import json
from jsonschema import validate
import bz2

CONTRACT_FILE = "tests/api_contract2.json"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

def start_uvicorn():
    process = subprocess.Popen(
        ["uvicorn", "app.main2:app", "--host", SERVER_HOST, "--port", str(SERVER_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    timeout = 15
    start = time.time()
    while True:
        if process.poll() is not None:
            raise RuntimeError("Uvicorn exited prematurely")
        try:
            requests.get(f"{SERVER_URL}/docs")
            break
        except requests.exceptions.ConnectionError:
            if time.time() - start > timeout:
                process.terminate()
                raise RuntimeError("Uvicorn did not start in time")
            time.sleep(0.5)
    return process

def stop_uvicorn(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

def test_weather_api_contract():
    process = start_uvicorn()
    try:
        with open(CONTRACT_FILE, "r") as f:
            contract = json.load(f)

        for ep in contract["endpoints"]:
            url = f"{SERVER_URL}{ep['path']}"
            method = ep["method"].upper()
            query = ep.get("query", {})
            files = {k: open(v, "rb") for k, v in ep.get("files", {}).items()}
            schema = ep["schema"]

            if method == "POST":
                response = requests.post(url, params=query, files=files)
            else:
                raise ValueError(f"Unsupported method: {method}")

            for f in files.values():
                f.close()

            assert response.status_code == 200, f"{url} returned {response.status_code}"

            # Nếu output_format = bz2 thì giải nén trước khi validate
            if query.get("output_format") == "bz2":
                data = json.loads(bz2.decompress(response.content).decode("utf-8"))
            else:
                data = response.json()

            validate(instance=data, schema=schema)

    finally:
        stop_uvicorn(process)
