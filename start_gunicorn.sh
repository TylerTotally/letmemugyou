#!/bin/bash
set -a
source /home/ubuntu/letmemugyou/.env
set +a

exec /home/ubuntu/letmemugyou/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/home/ubuntu/letmemugyou/letmemugyou.sock \
    app:app
