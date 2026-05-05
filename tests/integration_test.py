import os
import socket
import subprocess
import time
from pathlib import Path

import boto3
import pytest
import requests
from moto.server import ThreadedMotoServer

CONFIG_PATH = Path(__file__).parent / "jupyter_test_config.py"


def _free_port():
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _wait_http(url, timeout=30):
    deadline = time.time() + timeout
    last_exc = None
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code < 500:
                return
        except requests.RequestException as e:
            last_exc = e
        time.sleep(0.2)
    raise TimeoutError(f"{url} not ready in {timeout}s (last: {last_exc})")


@pytest.fixture
def moto_s3():
    port = _free_port()
    server = ThreadedMotoServer(port=port)
    server.start()
    endpoint = f"http://127.0.0.1:{port}"
    bucket = "multicontents-test"
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )
    s3.create_bucket(Bucket=bucket)
    try:
        yield endpoint, bucket
    finally:
        server.stop()


@pytest.fixture
def jupyter_server(tmp_path, moto_s3):
    endpoint, bucket = moto_s3
    local_root = tmp_path / "local"
    local_root.mkdir()

    env = os.environ.copy()
    env["MOTO_ENDPOINT"] = endpoint
    env["S3_BUCKET"] = bucket
    env["LOCAL_ROOT"] = str(local_root)

    port = _free_port()
    proc = subprocess.Popen(
        [
            "jupyter",
            "server",
            "--no-browser",
            "--ip=127.0.0.1",
            f"--port={port}",
            f"--config={CONFIG_PATH}",
        ],
        env=env,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_http(f"{base_url}/api/contents", timeout=30)
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def _put_file(base_url, path, content):
    r = requests.put(
        f"{base_url}/api/contents/{path}",
        json={"type": "file", "format": "text", "content": content},
    )
    r.raise_for_status()
    return r.json()


def _get_file(base_url, path):
    return requests.get(f"{base_url}/api/contents/{path}")


def test_root_listing_shows_both_managers(jupyter_server):
    r = requests.get(f"{jupyter_server}/api/contents").json()
    names = sorted(item["name"] for item in r["content"])
    assert names == ["local", "s3"]


def test_create_and_read_file_in_local(jupyter_server):
    _put_file(jupyter_server, "local/hello.txt", "hi from local")
    r = _get_file(jupyter_server, "local/hello.txt").json()
    assert r["content"] == "hi from local"


def test_create_and_read_file_in_s3(jupyter_server):
    _put_file(jupyter_server, "s3/foo.txt", "hi from s3")
    r = _get_file(jupyter_server, "s3/foo.txt").json()
    assert r["content"] == "hi from s3"


def test_move_file_across_managers(jupyter_server):
    _put_file(jupyter_server, "local/move-me.txt", "before")

    r = requests.patch(
        f"{jupyter_server}/api/contents/local/move-me.txt",
        json={"path": "s3/move-me.txt"},
    )
    r.raise_for_status()

    assert _get_file(jupyter_server, "local/move-me.txt").status_code == 404
    moved = _get_file(jupyter_server, "s3/move-me.txt").json()
    assert moved["content"] == "before"
