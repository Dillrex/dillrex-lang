#!/usr/bin/env sh
set -eu

PYTHON_BIN="${PYTHON:-}"

if [ -z "$PYTHON_BIN" ]; then
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_BIN="python"
    else
        echo "Could not find Python. Install Python 3.10+ or set PYTHON=/path/to/python." >&2
        exit 1
    fi
fi

echo "Building first Dillrex compiler artifact..."
"$PYTHON_BIN" -m dillrex bootstrap/dillrexc.drx build bootstrap/dillrexc.drx bootstrap/_selfhost_compiler1.drxc

echo
echo "Using the self-built compiler artifact to rebuild Dillrex..."
"$PYTHON_BIN" -m dillrex bootstrap/dillrexc.drx run-artifact bootstrap/_selfhost_compiler1.drxc build bootstrap/dillrexc.drx bootstrap/_selfhost_compiler2.drxc

echo
echo "Verifying second-generation compiler artifact..."
"$PYTHON_BIN" -m dillrex bootstrap/dillrexc.drx verify bootstrap/_selfhost_compiler2.drxc

rm -f bootstrap/_selfhost_compiler1.drxc bootstrap/_selfhost_compiler2.drxc

echo
echo "Deep self-host verification OK."
