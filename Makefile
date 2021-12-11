start-local:
	uvicorn main:app --reload

test-local:
	pytest

test-cov-local:
	pytest --cov=digster_api tests -vv --cov-report html

migrate-db:
	alembic revision --autogenerate -m $(commit_message)
	alembic upgrade head
