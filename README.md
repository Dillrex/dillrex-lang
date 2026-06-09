# Dillrex

![Dillrex icon](assets/dillrex-icon.png)

Dillrex is a small Python-powered programming language experiment.

The first version supports:

- `print("hello")`
- `name = in("Name: ")`
- `name = "Dylan"`
- `if condition { ... } else { ... }`
- `loop condition { ... }`
- `fn main() { ... }`
- `# comments`

## Example

```dillrex
# My first Dillrex program

fn main() {
    name = in("Name: ")

    if name == "Dylan" {
        print("Welcome back Dylan")
    } else {
        print("Hello " + name)
    }

    x = 0
    loop x < 5 {
        print(x)
        x = x + 1
    }
}
```

## Run

```powershell
python -m dillrex run examples\hello.drx
```

On Linux:

```bash
python3 -m dillrex run examples/hello.drx
```

## Open The Dillrex Terminal

### Windows

For the custom Windows terminal app, double-click:

```text
START_DILLREX_TERMINAL.vbs
```

This opens the Dillrex window without leaving command windows behind.

You can also run it from PowerShell:

```powershell
py -m dillrex.terminal_app
```

If `py` is not available:

```powershell
python -m dillrex.terminal_app
```

### Linux

From the cloned repo folder:

```bash
chmod +x START_DILLREX_TERMINAL.sh
./START_DILLREX_TERMINAL.sh
```

Or run it directly:

```bash
python3 -m dillrex.terminal_app
```

Linux needs Python with Tkinter installed. On many distros that package is called `python3-tk`.

Inside the Dillrex Terminal, type directly after the `dillrex>` prompt. Create and run `.dillrex`
files like this:

```text
new hello.dillrex
run hello.dillrex
```

`new` can create whatever extension you type:

```text
new notes.txt
new app.dillrex
new script.bat
new page.html
```

Create a full Dillrex project:

```text
project new my-app
project run
```

A project looks like:

```text
my-app/
  main.dillrex
  dillrex.json
  src/
  assets/
  build/
```

It also supports common terminal commands like:

```text
ls
dir
cd examples
pwd
mkdir projects
touch notes.txt
cat notes.txt
dillrex code print("hello")
clear
exit
```

Autocomplete works like a normal terminal:

```text
Tab       completes the current command or file name
Tab Tab   shows matching options when there are several
```

The older command-line shell still works too:

```powershell
python -m dillrex shell
```

On Linux:

```bash
python3 -m dillrex shell
```

The terminal icon lives at `assets/dillrex-icon.png`, with a Windows `.ico` version at
`assets/dillrex-icon.ico`.

## Variables

Dillrex variables use simple assignment:

```dillrex
name = "Dylan"
age = 21
print("Hello " + name)
```

Use `name = value`, not `set name = value`.

## Tests

```bash
python -m unittest tests.test_dillrex
```
