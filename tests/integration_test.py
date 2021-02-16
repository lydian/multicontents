import subprocess
import socket

import pytest
import requests


pid = None


@pytest.fixture(params=["lab", "notebook"])
def jupyter_process(request):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port = s.getsockname()[1]
    p = subprocess.Popen(
        [
            "jupyter",
            request.param,
            "-y",
            "--no-browser",
            "--ip=0.0.0.0",
            f"--port={port}",
            "--NotebookApp.token=''",
            "--NotebookApp.password=''",
            "--config=example/jupyter_notebook_config.py",
            "--debug",
        ]
    )

    def clean_up():
        p.kill()

    request.addfinalizer(clean_up)
    yield (p, port)


def test_integration(jupyter_process):
    popen, port = jupyter_process
    if popen.poll() is not None:
        r = requests.get(f"http://127.0.0.1:{port}/api/contents").json()
        assert sorted([folder["name"] for folder in r["content"]]) == sorted(
            ["home", "tmp"]
        )
