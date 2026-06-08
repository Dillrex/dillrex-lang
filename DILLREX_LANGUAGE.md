# Dillrex Language

Dillrex is a small Python-powered programming language experiment.

Current syntax:

| Idea | Dillrex |
| --- | --- |
| Print text | `print("hello")` |
| Ask for input | `name = in("Name: ")` |
| If | `if name == "Dylan" { ... }` |
| Else | `else { ... }` |
| Loop | `loop x < 5 { ... }` |
| Function | `fn main() { ... }` |
| Comment | `# comment` |

## Run A Program

From this folder:

```powershell
.\.venv\Scripts\python.exe -m dillrex run examples\hello.drx
```

If that virtual environment is not available, use your normal Python install:

```powershell
python -m dillrex run examples\hello.drx
```

On Windows, you can also double-click:

```text
RUN_DILLREX_EXAMPLE.cmd
```

## Open The Dillrex Terminal

```powershell
.\.venv\Scripts\python.exe -m dillrex shell
```

On Windows, you can also double-click:

```text
DILLREX_TERMINAL.cmd
```

Then type one-line Dillrex commands:

```dillrex
print("hello world")
```

Press Enter on a blank line to run them.

## Run Tests

```powershell
python -m unittest tests.test_dillrex
```

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

## GitHub Notes

This folder is ready to be added to a GitHub repository. For the first public Dillrex language repo,
keep these files:

- `dillrex/`
- `examples/`
- `tests/`
- `DILLREX_LANGUAGE.md`

The rest of this workspace contains the existing Dillrex Scanner CAD app.
