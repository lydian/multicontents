.PHONY: test clean develop-server
export JUPYTER_CONFIG_DIR := $(PWD)/.jupyter

virtualenv_run:
	tox -e virtualenv_run

test:
	tox

develop-server: virtualenv_run
	JUPYTER_CONFIG_DIR=example/ virtualenv_run/bin/jupyter lab --ip $(shell hostname -f)  -y --no-browser

clean:
	rm -rf virtualenv_run/
	rm -rf .tox

