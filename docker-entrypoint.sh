#!/bin/sh

set -e

. /venv/bin/activate


exec uvicorn digster_api.main:app --host 0.0.0.0 --port 8000
