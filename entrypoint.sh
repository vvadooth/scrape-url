#!/bin/sh
set -e

# If PORT is not set, default to 8000
if [ -z "$PORT" ]; then
  echo "PORT not set; defaulting to 8000"
  PORT=8000
fi

echo "Starting server on port $PORT"
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
