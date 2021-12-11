start-local:
	cd digster_api && uvicorn main:app --reload

test-local:
	pytest

test-cov-local:
	pytest --cov=digster_api tests -vv --cov-report html

migrate-db:
	alembic revision --autogenerate -m $(msg)
	alembic upgrade head
