# dillrex-lang

![Language](https://img.shields.io/badge/language-dillrex--lang-blue)
![Version](https://img.shields.io/badge/version-0.3.0-green)

![Dillrex icon](assets/dillrex-icon.png)

**dillrex-lang** is a custom programming language that runs `.drx` files. The current package version is **0.3.0**.

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

The current self-hosting milestone is working: Dillrex can build `dillrexc.drx` into `dillrexc.drxc`, then use that self-built compiler artifact to build `dillrexc.drx` again.

This repo is configured to hide the Python seed/runtime from GitHub's language bar. GitHub will only show a real **Dillrex** language label in the sidebar after Dillrex is added to GitHub Linguist, so the README marks the project as **dillrex-lang** directly.

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

Run the deeper self-host proof:

```powershell
VERIFY_SELFHOST2.cmd
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

- text: `len`, `upper`, `lower`, `trim`, `contains`, `split`, `join`, `replace`
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

Build the Dillrex compiler front-end itself:

```powershell
python -m dillrex bootstrap\dillrexc.drx rebuild-self build\dillrexc.drxc
```

Run the current self-host smoke test:

```powershell
python -m dillrex bootstrap\dillrexc.drx smoke-self
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
DILLREX-COMPILED    0.2
FORMAT              ast-text
SOURCE              "examples/no_input.drx"
SOURCE_DIR          "examples"
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

Run the deeper compiler-rebuild proof:

```powershell
VERIFY_SELFHOST2.cmd
```

The verifier checks:

- bootstrap tests
- token output
- AST output
- compiler front-end checks
- `.drxc` build/read/decode/run-artifact
- nested self-host execution

`VERIFY_SELFHOST2.cmd` is slower, but it checks the bigger milestone:

- build the Dillrex compiler artifact
- use that self-built artifact to rebuild the Dillrex compiler
- verify the second-generation compiler artifact

## Current Status

Dillrex is at the **0.3.0 self-hosting milestone** stage.

What works now:

- Python runtime runs `.drx`
- Dillrex-written lexer works
- Dillrex-written parser works
- Dillrex-written runner works for core programs
- imports work in the Dillrex-written runner
- `.drxc` artifacts can be built, read, decoded, and run
- `.drxc` artifacts bundle imported Dillrex code
- `dillrexc.drxc` can build another `.drxc` artifact
- `dillrexc.drx rebuild-self` builds the compiler front-end artifact
- `dillrexc.drx smoke-self` builds the compiler artifact, uses it to build a program artifact, then runs that program
- `dillrexc.drxc` can rebuild `dillrexc.drx` into a second-generation compiler artifact
- the Python seed runtime handles long logic chains without overflowing the Python stack
- the Dillrex-built runner uses the Python seed only for host runtime services while Dillrex code handles lexing, parsing, artifact building, and artifact running
- focused bootstrap tests pass

What is next:

- optimize the second-generation compiler rebuild so it is fast enough for normal verification
- compare first-generation and second-generation compiler artifacts
- add simple compile targets after the AST shape settles
