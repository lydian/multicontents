.PHONY: sync test build server clean
export JUPYTER_CONFIG_DIR := $(PWD)/.jupyter

sync:
	uv sync --extra dev

test: sync
	uv run pytest tests/

build:
	uv build

server: sync
	uv run jupyter lab -y \
		--no-browser \
		--ip 0.0.0.0 \
		--debug \
		--NotebookApp.token='' \
		--NotebookApp.password='' \
		--config example/jupyter_notebook_config.py

clean:
	rm -rf .venv/
	rm -rf .tox/
	rm -rf dist/
	rm -rf build/
	rm -rf virtualenv_run/
	rm -rf *.egg-info/
