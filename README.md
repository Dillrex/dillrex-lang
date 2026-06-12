# Dillrex

![Dillrex icon](assets/dillrex-icon.png)

Dillrex is a custom programming language with `.drx` files and its own terminal app.
Python currently powers the interpreter, but Dillrex code is parsed and run by the Dillrex runtime.

## Syntax

```drx
# comment

set x = 10
set name = ask("Name: ")

print("Hello")
print(x)

if x > 5 then
    print("big")
else
    print("small")
end

loop x < 20 then
    print(x)
    set x = x + 1
end

fn add(a, b) then
    return a + b
end

set total = add(2, 3)
print(total)
```

## Keywords

| Idea | Dillrex |
| --- | --- |
| Print | `print` |
| Input | `ask` |
| Variable | `set` |
| If | `if` |
| Start block | `then` |
| Else | `else` |
| End block | `end` |
| While loop | `loop` |
| Function | `fn` |
| Return | `return` |
| Import | `import` |
| Comment | `#` |
| Empty value | `null` |

## Run

```powershell
python -m dillrex run examples\hello.drx
```

Pass command-line args:

```powershell
python -m dillrex run examples\upperfile.drx input.txt output.txt
```

On Linux:

```bash
python3 -m dillrex run examples/hello.drx
```

## Open The Dillrex Terminal

### Windows

Double-click:

```text
START_DILLREX_TERMINAL.vbs
```

Or run:

```powershell
py -m dillrex.terminal_app
```

### Linux

```bash
chmod +x START_DILLREX_TERMINAL.sh
./START_DILLREX_TERMINAL.sh
```

Inside the Dillrex Terminal:

```text
new main.drx
run main.drx
```

## Full Example

```drx
# Dillrex first test program

fn main then
    print("Welcome to Dillrex")

    set name = ask("Name: ")
    set age = ask("Age: ")

    print("Hello " + name)

    if age >= 18 then
        print("You are an adult")
    else
        print("You are not an adult")
    end

    set count = 1

    loop count <= 5 then
        print("Count: " + count)
        set count = count + 1
    end

    set answer = add(10, 5)
    print("10 + 5 = " + answer)
end

fn add(a, b) then
    return a + b
end

main()
```

## Lists, Files, And Args

```drx
set names = ["Dylan", "Max"]
push(names, "Sam")
print(names[0])

print(args[0])

if exists("notes.txt") then
    set text = read("notes.txt")
    write("copy.txt", upper(text))
end
```

## Imports

```drx
import "tools.drx"

set result = double(10)
print(result)
```

## Bootstrap

The `bootstrap/` folder starts the path toward Dillrex building itself.

```powershell
python -m dillrex run bootstrap\dillrex-self.drx examples\no_input.drx
```

The bootstrap now includes Dillrex-written lexer, parser, and runner pieces. To run
the focused self-host checks:

```powershell
VERIFY_BOOTSTRAP.cmd
```

Inspect the compiler pipeline without running the program:

```powershell
python -m dillrex bootstrap\dillrex-self.drx --tokens examples\no_input.drx
python -m dillrex bootstrap\dillrex-self.drx --ast examples\no_input.drx
```

Use the Dillrex-written compiler front-end:

```powershell
python -m dillrex bootstrap\dillrexc.drx check examples\no_input.drx
python -m dillrex bootstrap\dillrexc.drx run examples\no_input.drx
python -m dillrex bootstrap\dillrexc.drx build examples\no_input.drx build\no_input.drxc
python -m dillrex bootstrap\dillrexc.drx read build\no_input.drxc
```

## Tests

```bash
python -m unittest discover -s tests
```
