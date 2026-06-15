#!/bin/bash

# Start the Celery worker in the background with limited concurrency to save memory
celery -A celery_worker worker --loglevel=info --concurrency=1 &

# Start the FastAPI backend in the foreground
uvicorn app.main:app --host 0.0.0.0 --port $PORT
