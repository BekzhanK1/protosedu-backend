FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1

# RUN apk add --no-cache gcc musl-dev postgresql-dev

WORKDIR /django

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .
RUN mkdir -p /django/logs

EXPOSE 8000

COPY entrypoint.sh /entrypoint.sh

RUN rm -f /django/celerybeat-schedule

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["gunicorn", "vunderkids.wsgi", "--bind", "0.0.0.0:8000", "--workers", "4"]
