PY ?= python
REPO ?= https://github.com/psf/requests
MODE ?= advanced

.PHONY: setup baseline advanced eval report test index

setup:
	$(PY) -m pip install -r requirements.txt

index:
	$(PY) -m repowiki index $(REPO)

baseline:
	$(PY) -m repowiki generate $(REPO) --mode baseline

advanced:
	$(PY) -m repowiki generate $(REPO) --mode advanced

eval:
	$(PY) -m evals.runner

report:
	type evals\report.md 2>nul || cat evals/report.md

test:
	$(PY) -m pytest -q
