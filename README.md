# vunderkids
## Celery worker
celery -A vunderkids worker -l info

## Beat
celery -A vunderkids beat --loglevel=info


## Redis 
docker run -d --name my-redis-stack -p 6379:6379  redis/redis-stack-server:latest
