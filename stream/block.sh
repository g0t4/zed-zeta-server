#!/usr/bin/env bash

# check if in VENV and warn if not
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Not in a virtual environment. This may cause problems."
    echo "See README.md for more information."
    exit 1
fi

uvicorn --reload --port 7100 stream.block:app
