.PHONY: setup sample test dev backend

setup:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

sample:
	cd backend && . .venv/bin/activate && python ../scripts/generate_sample_data.py

test:
	cd backend && . .venv/bin/activate && pytest -v

backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

dev:
	./scripts/dev.sh
