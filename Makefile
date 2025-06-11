run:
	uvicorn vunderkids.asgi:application --host 0.0.0.0 --port 9000 --reload

makemigrations:
	python3 manage.py makemigrations

migrate:
	python3 manage.py migrate

celery:
	celery -A vunderkids worker -l info --concurrency=2