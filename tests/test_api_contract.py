import subprocess
import time
import requests
import json
from jsonschema import validate

CONTRACT_FILE = "tests/api_contract.json"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

def start_uvicorn():
    """Khởi động uvicorn background và đợi server sẵn sàng"""
    process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", SERVER_HOST, "--port", str(SERVER_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Polling loop đợi server ready
    timeout = 15
    start = time.time()
    while True:
        if process.poll() is not None:
            raise RuntimeError("Uvicorn exited prematurely")
        try:
            requests.get(f"{SERVER_URL}/docs")  # kiểm tra server bằng endpoint bất kỳ
            break
        except requests.exceptions.ConnectionError:
            if time.time() - start > timeout:
                process.terminate()
                raise RuntimeError("Uvicorn did not start in time")
            time.sleep(0.5)
    return process

def stop_uvicorn(process):
    """Dừng uvicorn an toàn"""
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

def test_api_contract():
    """Test tất cả endpoint dựa trên contract JSON"""
    process = start_uvicorn()
    try:
        with open(CONTRACT_FILE, "r") as f:
            contract = json.load(f)

        for ep in contract["endpoints"]:
            path = ep["path"]
            method = ep.get("method", "GET").upper()
            params = ep.get("params", {})
            schema = ep["schema"]

            url = f"http://{SERVER_HOST}:{SERVER_PORT}{path}"

            if method == "GET":
                response = requests.get(url, params=params)
            elif method == "POST":
                response = requests.post(url, json=params)
            else:
                raise ValueError(f"Unsupported method: {method}")

            assert response.status_code == 200, f"{path} returned {response.status_code}"

            data = response.json()
            validate(instance=data, schema=schema)
    finally:
        stop_uvicorn(process)
