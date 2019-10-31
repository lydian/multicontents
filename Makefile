.PHONY: test clean develop-server
export JUPYTER_CONFIG_DIR := $(PWD)/example

virtualenv_run:
	tox -e virtualenv_run

test:
	tox

server: virtualenv_run
	 virtualenv_run/bin/jupyter lab -y \
	 	 --no-browser \
	 	 --ip 0.0.0.0 \
	 	 --NotebookApp.token='' \
	 	 --NotebookApp.password=''

build:
	tox -e build

clean:
	rm -rf virtualenv_run/
	rm -rf .tox
	rm -rf dist/

