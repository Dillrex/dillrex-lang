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
11. `dillrexc.drx` provides a Dillrex-written front-end with `run`, `tokens`, `ast`, `check`, `build`, `read`, `decode`, and `run-artifact` commands.
12. `dillrexc.drx build` writes a first `.drxc` artifact containing source metadata and the encoded AST.
13. `dillrexc.drx read` validates `.drxc` artifacts and reports their stored metadata.
14. `dillrexc.drx decode` decodes artifact AST text back into Dillrex lists and re-emits it.
15. `dillrexc.drx run-artifact` runs `.drxc` artifacts through the Dillrex-built runner.
16. `dillrexc.drx build-project` builds a simple folder with `dillrex.json`.
17. `.drxc` artifacts now bundle imported functions and import-time body statements.
18. `dillrexc.drxc` can build another `.drxc` program artifact.
19. The Python seed runtime now handles very long Dillrex logic chains without stack overflow.
20. `dillrexc.drx rebuild-self` and `smoke-self` provide explicit self-build smoke commands.
21. `dillrexc.drxc` can rebuild `dillrexc.drx` into a second-generation compiler artifact.

Planned stages:

1. Optimize the second-generation compiler rebuild so it is fast enough for normal verification.
2. Compare first-generation and second-generation compiler artifacts.
3. Add simple compile targets after the AST shape settles.

Run the bootstrap checks:

```powershell
VERIFY_BOOTSTRAP.cmd
```

On Linux/macOS:

```bash
sh VERIFY_BOOTSTRAP.sh
```

Run the deeper self-host proof:

```powershell
VERIFY_SELFHOST2.cmd
```

On Linux/macOS:

```bash
sh VERIFY_SELFHOST2.sh
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
python -m dillrex bootstrap\dillrexc.drx decode build\no_input.drxc
python -m dillrex bootstrap\dillrexc.drx run-artifact build\no_input.drxc
python -m dillrex bootstrap\dillrexc.drx build-project examples\project-example
python -m dillrex bootstrap\dillrexc.drx rebuild-self build\dillrexc.drxc
python -m dillrex bootstrap\dillrexc.drx smoke-self
```

That process is called bootstrapping.
