# Dillrex Bootstrap

This folder is where Dillrex starts learning to build itself.

Current stage:

1. The Python starter runtime runs `.drx` programs.
2. Dillrex `.drx` tools can read files, split text, use lists, import files, and use command-line args.
3. `lexer.drx` now tokenizes Dillrex source into `[kind, value, line, column]` tokens.
4. `parser.drx` now turns those tokens into a simple list-based program tree.
5. `runner.drx` now executes that program tree for core Dillrex programs.
6. The Dillrex-built runner now loads relative imports, nested imports, and imported top-level code.
7. Focused bootstrap tests now cover the Dillrex-written runner, imports, file args, and nested self-host execution.
8. `dillrex-self.drx --quiet file.drx` runs without debug token output for tests and future build steps.
9. `VERIFY_BOOTSTRAP.cmd` and `VERIFY_BOOTSTRAP.sh` run the key bootstrap checks in one command.
10. `--tokens` and `--ast` expose machine-readable compiler pipeline output.
11. `dillrexc.drx` provides a Dillrex-written front-end with `run`, `tokens`, `ast`, `check`, `build`, and `read` commands.
12. `dillrexc.drx build` writes a first `.drxc` artifact containing source metadata and the encoded AST.
13. `dillrexc.drx read` validates `.drxc` artifacts and reports their stored metadata.

Planned stages:

1. Teach `dillrexc.drx` to decode artifact AST text back into Dillrex lists.
2. Add simple compile targets after the AST shape settles.
3. Later, the Dillrex-built compiler can build/run itself.

Run the bootstrap checks:

```powershell
VERIFY_BOOTSTRAP.cmd
```

On Linux/macOS:

```bash
sh VERIFY_BOOTSTRAP.sh
```

Inspect compiler pipeline output:

```powershell
python -m dillrex bootstrap\dillrex-self.drx --tokens examples\no_input.drx
python -m dillrex bootstrap\dillrex-self.drx --ast examples\no_input.drx
```

Use the Dillrex-written compiler front-end:

```powershell
python -m dillrex bootstrap\dillrexc.drx check examples\no_input.drx
python -m dillrex bootstrap\dillrexc.drx run examples\no_input.drx
python -m dillrex bootstrap\dillrexc.drx tokens examples\no_input.drx
python -m dillrex bootstrap\dillrexc.drx ast examples\no_input.drx
python -m dillrex bootstrap\dillrexc.drx build examples\no_input.drx build\no_input.drxc
python -m dillrex bootstrap\dillrexc.drx read build\no_input.drxc
```

That process is called bootstrapping.
