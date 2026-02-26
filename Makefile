.PHONY: dev backend frontend backfill sync-stocks install

# 동시 실행
dev:
	@echo "Starting backend and frontend..."
	@make backend & make frontend

backend:
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

# 설치
install:
	cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

# 데이터 작업
backfill:
	cd backend && source venv/bin/activate && python -m app.jobs.backfill

sync-stocks:
	cd backend && source venv/bin/activate && python -m app.jobs.sync_stocks
