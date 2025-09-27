PYTHON ?= python
STUDENT ?= anonymous
OUT ?= examples/adaptive.yaml

.PHONY: venv install dev lint test run clean
venv: ; python -m venv .venv
install: ; . .venv/bin/activate && pip install -U pip && pip install -e .
dev: ; . .venv/bin/activate && pip install -U pip && pip install -e .[dev] && pre-commit install || true
lint:
	ruff check src tests
	black --check src tests
test: ; pytest -q
run: ; socratic-tutor --problems examples/equations.yaml
clean:
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache __pycache__ **/__pycache__

# --- Dashboard (Streamlit) ---
dash:
	streamlit run app/dashboard.py

# --- API (FastAPI via uvicorn) ---
api:
	uvicorn socratic_tutor.api.main:app --reload --port 8000

# --- Adaptive generator ---
generate:
	$(PYTHON) -m socratic_tutor.tools.generate --student "$(STUDENT)" --out "$(OUT)"
	@echo "Example: make generate STUDENT=Paeta OUT=examples/adaptive_Paeta.yaml"

.PHONY: run-fac run-sys run-frac
run-fac:
	socratic-tutor --problems examples/factorization.yaml --student "$(USER)"

run-sys:
	socratic-tutor --problems examples/systems.yaml --student "$(USER)"

run-frac:
	socratic-tutor --problems examples/fractions.yaml --student "$(USER)"
