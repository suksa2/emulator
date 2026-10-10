PYTHON ?= python3

.PHONY: run test

run:
	PYTHONPATH=src $(PYTHON) -m emulator

test:
	$(PYTHON) -m unittest discover -s tests -t . -v
