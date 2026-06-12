# Dillrex

![Dillrex icon](assets/dillrex-icon.png)

Dillrex is a custom programming language that runs `.drx` files. The current package version is **0.2.0**.

Right now, Python is still the starter runtime. On top of that, Dillrex now has the beginning of a self-hosted toolchain written in Dillrex itself:

```text
Python Dillrex runtime
  -> Dillrex bootstrap driver
    -> Dillrex lexer
    -> Dillrex parser
    -> Dillrex runner
      -> runs Dillrex programs
```

There is also a Dillrex-written compiler front-end, `bootstrap/dillrexc.drx`, that can inspect source, run programs, build `.drxc` artifacts, read them, decode their stored AST, and run those artifacts.

## Quick Start

Run a Dillrex file:

```powershell
python -m dillrex run examples\hello.drx
```

You can also launch a `.drx` file directly:

```powershell
python -m dillrex examples\no_input.drx
```

Pass command-line args:

```powershell
python -m dillrex run examples\upperfile.drx input.txt output.txt
```

Run all tests:

```powershell
python -m unittest discover -s tests
```

Run the self-host bootstrap checks:

```powershell
VERIFY_BOOTSTRAP.cmd
```

On Linux/macOS:

```bash
python3 -m dillrex run examples/hello.drx
sh VERIFY_BOOTSTRAP.sh
```

## Simple Dillrex Program

```drx
# examples/no_input.drx style

fn main then
    print("Hello from Dillrex")

    set x = 0
    loop x < 3 then
        print("x = " + x)
        set x = x + 1
    end
end

main()
```

Run it:

```powershell
python -m dillrex run examples\no_input.drx
```

Expected output:

```text
Hello from Dillrex
x = 0
x = 1
x = 2
```

## Language Features

Dillrex currently supports:

- comments with `#`
- variables with `set`
- numbers, strings, booleans, and `null`
- `if / else / end`
- `loop / end`
- functions with `fn`
- `return`, including blank `return`
- `import "file.drx"`
- `try / catch`
- `throw`
- command-line `args`
- lists like `[1, 2, 3]`
- indexing like `items[0]`
- index assignment like `set items[1] = "new"`

Useful built-ins include:

- text: `len`, `upper`, `lower`, `trim`, `contains`, `split`, `replace`
- conversion: `text`, `str`, `num`, `int`, `bool`, `kind`, `type`
- lists: `push`, `pop`, `remove`
- files: `read`, `write`, `append`, `exists`, `delete`, `listfiles`
- math: `round`, `floor`, `ceil`, `abs`, `min`, `max`
- terminal: `print`, `ask`, `exit`

## More Examples

Lists and indexing:

```drx
set names = ["Dylan", "Max"]
push(names, "Sam")
set names[1] = upper("rex")

print(names[0])
print(names[1])
print(names[2])
```

Files and args:

```drx
set inputPath = args[0]
set outputPath = args[1]

set text = read(inputPath)
write(outputPath, upper(text))
print("Wrote uppercase text to " + outputPath)
```

Imports:

```drx
import "tools.drx"

set result = double(10)
print(result)
```

Try/catch:

```drx
try then
    throw "custom problem"
catch err then
    print("caught " + err)
end
```

## Self-Hosting Bootstrap

The `bootstrap/` folder is where Dillrex starts learning to build itself.

Important files:

- `bootstrap/lexer.drx`: tokenizes Dillrex source
- `bootstrap/parser.drx`: turns tokens into a list-based program tree
- `bootstrap/runner.drx`: executes that program tree
- `bootstrap/compiler-tools.drx`: shared formatting, artifact, and decode helpers
- `bootstrap/dillrex-self.drx`: bootstrap driver
- `bootstrap/dillrexc.drx`: compiler front-end
- `bootstrap/README.md`: detailed bootstrap status

Run a program through the Dillrex-written lexer, parser, and runner:

```powershell
python -m dillrex bootstrap\dillrex-self.drx --quiet examples\no_input.drx
```

Inspect tokens:

```powershell
python -m dillrex bootstrap\dillrex-self.drx --tokens examples\no_input.drx
```

Inspect the AST/program tree:

```powershell
python -m dillrex bootstrap\dillrex-self.drx --ast examples\no_input.drx
```

The big idea:

```text
.drx source
  -> lexer.drx makes tokens
  -> parser.drx makes an AST/list tree
  -> runner.drx executes that tree
  -> dillrexc.drx can build/read/decode/run .drxc artifacts
```

## Compiler Front-End

`bootstrap/dillrexc.drx` is the first Dillrex-written compiler front-end.

Check a source file:

```powershell
python -m dillrex bootstrap\dillrexc.drx check examples\no_input.drx
```

Run through the Dillrex-written runner:

```powershell
python -m dillrex bootstrap\dillrexc.drx run examples\no_input.drx
```

Print tokens:

```powershell
python -m dillrex bootstrap\dillrexc.drx tokens examples\no_input.drx
```

Print AST:

```powershell
python -m dillrex bootstrap\dillrexc.drx ast examples\no_input.drx
```

Build a `.drxc` artifact:

```powershell
python -m dillrex bootstrap\dillrexc.drx build examples\no_input.drx build\no_input.drxc
```

Read artifact metadata:

```powershell
python -m dillrex bootstrap\dillrexc.drx read build\no_input.drxc
```

Decode the stored AST:

```powershell
python -m dillrex bootstrap\dillrexc.drx decode build\no_input.drxc
```

Run a `.drxc` artifact:

```powershell
python -m dillrex bootstrap\dillrexc.drx run-artifact build\no_input.drxc
```

Current `.drxc` files are simple text artifacts:

```text
DILLREX-COMPILED    0.1
SOURCE              "examples/no_input.drx"
TOKENS              34
IMPORTS             0
FUNCTIONS           1
BODY                1
AST                 [...]
```

They are not native executables yet, but Dillrex can now run them by decoding their AST and feeding it into the Dillrex-built runner.

## Terminal App

### Windows

Double-click:

```text
START_DILLREX_TERMINAL.vbs
```

Or run:

```powershell
py -m dillrex.terminal_app
```

### Linux/macOS

```bash
chmod +x START_DILLREX_TERMINAL.sh
./START_DILLREX_TERMINAL.sh
```

Inside the terminal:

```text
new main.drx
run main.drx
```

## Tests And Verification

Run all tests:

```powershell
python -m unittest discover -s tests
```

Run only bootstrap tests:

```powershell
python -m unittest tests.test_bootstrap
```

Run the one-command bootstrap verifier:

```powershell
VERIFY_BOOTSTRAP.cmd
```

The verifier checks:

- bootstrap tests
- token output
- AST output
- compiler front-end checks
- `.drxc` build/read/decode/run-artifact
- nested self-host execution

## Current Status

Dillrex is at the **0.2.0 bootstrap foundation** stage.

What works now:

- Python runtime runs `.drx`
- Dillrex-written lexer works
- Dillrex-written parser works
- Dillrex-written runner works for core programs
- imports work in the Dillrex-written runner
- `.drxc` artifacts can be built, read, decoded, and run
- focused bootstrap tests pass

What is next:

- grow `dillrexc.drx` from front-end into a fuller build tool
- add simple compile targets after the AST shape settles
- eventually let the Dillrex-built Dillrex build itself
