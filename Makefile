run:
	python3 manage.py runserver 0.0.0.0:9000

makemigrations:
	python3 manage.py makemigrations

migrate:
	python3 manage.py migrate

celery:
	celery -A vunderkids worker -l info