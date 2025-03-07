#!/bin/sh
set -e
# Use the PORT environment variable if set, default to 8000
PORT_NUM=${PORT:-8000}
echo "Starting server on port ${PORT_NUM}"
exec uvicorn main:app --host 0.0.0.0 --port ${PORT_NUM}
