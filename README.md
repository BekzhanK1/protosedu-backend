# Protosedu Backend

Django REST API для системы электронного обучения.

## Структура проекта

- **account** ― пользователи, школы и роли.
- **tasks** ― курсы, разделы, главы и задания.
- **subscription** ― тарифы и управление подпиской.
- **documents** ― загрузка файлов и предметов.
- **leagues** ― игровые лиги и группы.
- **modo** ― тесты и вопросы.

Все маршруты подключаются в [`api/urls.py`](api/urls.py) и доступны по префиксу `/api/`.

## Быстрый старт

1. **Клонируйте репозиторий и создайте окружение**

```bash
git clone <repo-url>
cd protosedu-backend
```

2. **Создайте файл `.env`** с переменными окружения. Минимальный набор:

```env
SECRET_KEY=your-secret-key
STAGE=DEV
DATABASE_NAME=protosedu
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
CACHE_STAGE=docker
CELERY_STAGE=docker
```

Полный список переменных описан в [`vunderkids/settings_config/base.py`](vunderkids/settings_config/base.py).

3. **Запустите локально**

```bash
make makemigrations
make migrate
make run  # сервер доступен на http://localhost:9000/
```

Запуск Celery:

```bash
make celery       # celery worker -l info
celery -A vunderkids beat --loglevel=info
```

4. **Docker Compose**

```bash
docker compose up --build
```

Команда поднимет PostgreSQL, Redis, веб‑сервер (Gunicorn) и процессы Celery.
Скрипт [`entrypoint.sh`](entrypoint.sh) выполнит миграции и соберёт статику.

## Полезные ссылки

- Документация API — `/api/schema/`.
- Админка — `/admin/`.

Деплой в продакшен осуществляется через GitHub Actions ([`.github/workflows/cd.yml`](.github/workflows/cd.yml)).
