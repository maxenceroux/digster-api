
start-local:
	uvicorn digster_api.main:app --host 0.0.0.0 --port 8000 --reload

test-local:
	pytest

test-cov-local:
	pytest --cov=digster_api tests -vv --cov-report html

migrate-db:
	alembic revision --autogenerate -m $(msg)
	alembic upgrade head

start-dev-docker:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

start-test-docker:
	docker-compose -f docker-compose.yml -f docker-compose.test.yml up

start-worker:
	celery worker --app=digster_api.worker.celery --loglevel=info
