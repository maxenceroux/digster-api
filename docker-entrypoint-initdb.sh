#!/bin/sh

set -e

. /venv/bin/activate


make migrate-db msg="db-init"
