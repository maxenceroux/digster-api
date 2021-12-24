#!/bin/sh

set -e

. /venv/bin/activate

pip install pytest
make test-local
