#!/bin/sh
cd "$(dirname "$0")" || exit 1
if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
    printf '%s\n' 'Install Python 3.10 or later, then open this file again.'
    exit 1
fi
exec python3 app.py
