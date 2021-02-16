.PHONY: test clean develop-server
export JUPYTER_CONFIG_DIR := $(PWD)/.jupyter

virtualenv_run:
	tox -e virtualenv_run

test:
	tox

server: virtualenv_run
	 virtualenv_run/bin/jupyter lab -y \
	 	 --no-browser \
	 	 --ip 0.0.0.0 \
	 	 --debug \
	 	 --NotebookApp.token='' \
	 	 --NotebookApp.password='' \
	 	 --config example/jupyter_notebook_config.py

build:
	tox -e build

clean:
	rm -rf virtualenv_run/
	rm -rf .tox
	rm -rf dist/

