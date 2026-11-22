#!/bin/sh

# Author: abolfazlkameli0@gmail.com
# Version: v0.1.0
# Date: 20/11/26
# Description: entrypoint for PasteForge API.
# Usage: ./entrypoint.sh

set -e

alembic upgrade head

uvicorn pasteforge.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --proxy-headers \
    --forwarded-allow-ips="*" \
    --workers $(( 2 * $(grep -c processor /proc/cpuinfo) + 1 ))