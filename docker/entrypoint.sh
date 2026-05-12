#!/bin/sh
set -eu

cd /app/ujn

python manage.py collectstatic --noinput

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    python manage.py migrate --noinput
fi

gunicorn scoring_system.wsgi:application \
    --bind 127.0.0.1:8000 \
    --worker-class gthread \
    --workers "${GUNICORN_WORKERS:-2}" \
    --threads "${GUNICORN_THREADS:-8}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" &
gunicorn_pid="$!"

nginx -g 'daemon off;' &
nginx_pid="$!"

shutdown() {
    kill -TERM "$gunicorn_pid" "$nginx_pid" 2>/dev/null || true
    wait "$gunicorn_pid" 2>/dev/null || true
    wait "$nginx_pid" 2>/dev/null || true
}

term_handler() {
    shutdown
    exit 0
}

trap term_handler INT TERM

while kill -0 "$gunicorn_pid" 2>/dev/null && kill -0 "$nginx_pid" 2>/dev/null; do
    sleep 1
done

shutdown
exit 1
