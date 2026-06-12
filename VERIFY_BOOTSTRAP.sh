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

echo "Running Dillrex bootstrap tests..."
"$PYTHON_BIN" -m unittest tests.test_bootstrap

echo
echo "Checking machine-readable bootstrap output modes..."
"$PYTHON_BIN" -m dillrex bootstrap/dillrex-self.drx --tokens examples/no_input.drx >/dev/null
"$PYTHON_BIN" -m dillrex bootstrap/dillrex-self.drx --ast examples/no_input.drx >/dev/null
"$PYTHON_BIN" -m dillrex bootstrap/dillrexc.drx check examples/no_input.drx >/dev/null
"$PYTHON_BIN" -m dillrex bootstrap/dillrexc.drx build examples/no_input.drx bootstrap/_verify_no_input.drxc >/dev/null
test -f bootstrap/_verify_no_input.drxc
"$PYTHON_BIN" -m dillrex bootstrap/dillrexc.drx read bootstrap/_verify_no_input.drxc >/dev/null
"$PYTHON_BIN" -m dillrex bootstrap/dillrexc.drx decode bootstrap/_verify_no_input.drxc >/dev/null
"$PYTHON_BIN" -m dillrex bootstrap/dillrexc.drx run-artifact bootstrap/_verify_no_input.drxc >/dev/null
rm -f bootstrap/_verify_no_input.drxc

echo
echo "Running nested quiet self-host smoke test..."
"$PYTHON_BIN" -m dillrex bootstrap/dillrex-self.drx --quiet bootstrap/dillrex-self.drx --quiet examples/math.drx

echo
echo "Running Dillrex compiler front-end through self-host chain..."
"$PYTHON_BIN" -m dillrex bootstrap/dillrex-self.drx --quiet bootstrap/dillrexc.drx run examples/no_input.drx
"$PYTHON_BIN" -m dillrex bootstrap/dillrex-self.drx --quiet bootstrap/dillrexc.drx build examples/math.drx bootstrap/_verify_math.drxc >/dev/null
test -f bootstrap/_verify_math.drxc
"$PYTHON_BIN" -m dillrex bootstrap/dillrex-self.drx --quiet bootstrap/dillrexc.drx read bootstrap/_verify_math.drxc >/dev/null
"$PYTHON_BIN" -m dillrex bootstrap/dillrex-self.drx --quiet bootstrap/dillrexc.drx decode bootstrap/_verify_math.drxc >/dev/null
"$PYTHON_BIN" -m dillrex bootstrap/dillrex-self.drx --quiet bootstrap/dillrexc.drx run-artifact bootstrap/_verify_math.drxc >/dev/null
rm -f bootstrap/_verify_math.drxc

echo
echo "Checking compiled compiler artifact..."
"$PYTHON_BIN" -m dillrex bootstrap/dillrexc.drx build bootstrap/dillrexc.drx bootstrap/_verify_dillrexc.drxc >/dev/null
"$PYTHON_BIN" -m dillrex bootstrap/dillrexc.drx run-artifact bootstrap/_verify_dillrexc.drxc build examples/no_input.drx bootstrap/_verify_compiled_output.drxc >/dev/null
"$PYTHON_BIN" -m dillrex bootstrap/dillrexc.drx run-artifact bootstrap/_verify_compiled_output.drxc >/dev/null
rm -f bootstrap/_verify_dillrexc.drxc bootstrap/_verify_compiled_output.drxc

echo
echo "Running self compiler smoke command..."
"$PYTHON_BIN" -m dillrex bootstrap/dillrexc.drx smoke-self >/dev/null
rm -f build/dillrexc.drxc build/self-smoke.drxc

echo
echo "Bootstrap verification OK."
