from __future__ import annotations

import contextlib
import glob
import io
import json
from pathlib import Path
import shlex
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from .runtime import DillrexError, run_file, run_source


ROOT = Path(__file__).resolve().parent.parent
ICON_PATH = ROOT / "assets" / "dillrex-icon.png"
DILLREX_TEMPLATE = """# My Dillrex program

fn main then
    print("hello from Dillrex")
end

main()
"""

FILE_TEMPLATES = {
    ".drx": DILLREX_TEMPLATE,
    ".bat": "@echo off\nREM New batch file\n",
    ".cmd": "@echo off\nREM New command file\n",
    ".ps1": "# New PowerShell script\n",
    ".py": "print(\"hello\")\n",
    ".html": "<!doctype html>\n<html>\n<head>\n    <title>New Page</title>\n</head>\n<body>\n</body>\n</html>\n",
    ".css": "/* New stylesheet */\n",
    ".js": "console.log(\"hello\");\n",
    ".json": "{}\n",
    ".md": "# New File\n",
    ".txt": "",
}

COMMANDS = sorted(
    {
        "cat",
        "cd",
        "clear",
        "cls",
        "dillrex",
        "dir",
        "echo",
        "exit",
        "help",
        "ls",
        "mkdir",
        "new",
        "open",
        "project",
        "pwd",
        "run",
        "start",
        "touch",
        "type",
    }
)
PATH_COMMANDS = {"cat", "cd", "dir", "ls", "mkdir", "new", "open", "run", "start", "touch", "type"}
PROJECT_FOLDERS = ("src", "assets", "build")


class DillrexTerminalApp:
    def __init__(self) -> None:
        self.cwd = ROOT
        self.history: list[str] = []
        self.history_index: int | None = None
        self.last_tab_input = ""

        self.root = tk.Tk()
        self.root.title("Dillrex Terminal")
        self.root.geometry("980x620")
        self.root.minsize(720, 420)
        self.root.configure(bg="#050b0a")

        if ICON_PATH.exists():
            self.icon = tk.PhotoImage(file=str(ICON_PATH))
            self.root.iconphoto(True, self.icon)
        else:
            self.icon = None

        self.input_start = "1.0"
        self._build_ui()
        self._banner()
        self._prompt()

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg="#071511", height=74)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        if self.icon:
            logo = tk.Label(header, image=self.icon, bg="#071511")
            logo.pack(side=tk.LEFT, padx=(18, 12), pady=8)

        tk.Label(
            header,
            text="Dillrex Terminal",
            bg="#071511",
            fg="#b7ff35",
            font=("Consolas", 21, "bold"),
        ).pack(side=tk.LEFT, pady=(2, 0))

        frame = tk.Frame(self.root, bg="#010504")
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.screen = tk.Text(
            frame,
            bg="#010504",
            fg="#d9fff1",
            insertbackground="#b7ff35",
            selectbackground="#1d5b4a",
            relief=tk.FLAT,
            padx=14,
            pady=12,
            font=("Consolas", 12),
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            undo=False,
        )
        self.screen.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.screen.yview)

        self.screen.tag_configure("accent", foreground="#b7ff35")
        self.screen.tag_configure("cyan", foreground="#7fffd4")
        self.screen.tag_configure("warn", foreground="#ffcc66")
        self.screen.tag_configure("error", foreground="#ff7777")

        self.screen.bind("<Return>", self._on_enter)
        self.screen.bind("<BackSpace>", self._on_backspace)
        self.screen.bind("<Left>", self._guard_navigation)
        self.screen.bind("<Home>", self._on_home)
        self.screen.bind("<Tab>", self._on_tab)
        self.screen.bind("<Up>", self._history_up)
        self.screen.bind("<Down>", self._history_down)
        self.screen.bind("<KeyPress>", self._on_keypress)
        self.screen.focus_set()

    def _banner(self) -> None:
        self.write("Dillrex Terminal 0.2\n", "accent")

    def _prompt(self) -> None:
        self.write("dillrex> ", "accent")
        self.input_start = self.screen.index(tk.INSERT)
        self.screen.mark_set("insert", tk.END)

    def write(self, text: str, tag: str | None = None) -> None:
        if tag:
            self.screen.insert(tk.END, text, tag)
        else:
            self.screen.insert(tk.END, text)
        self.screen.see(tk.END)

    def current_input(self) -> str:
        return self.screen.get(self.input_start, "end-1c")

    def replace_current_input(self, value: str) -> None:
        self.screen.delete(self.input_start, "end-1c")
        self.screen.insert(tk.END, value)
        self.screen.see(tk.END)

    def _on_keypress(self, event: tk.Event) -> str | None:
        if event.keysym in {
            "Return",
            "BackSpace",
            "Left",
            "Right",
            "Home",
            "End",
            "Tab",
            "Up",
            "Down",
            "Control_L",
            "Control_R",
            "Shift_L",
            "Shift_R",
        }:
            return None
        self.last_tab_input = ""
        if self.screen.compare(tk.INSERT, "<", self.input_start):
            self.screen.mark_set("insert", tk.END)
        return None

    def _guard_navigation(self, _event: tk.Event) -> str | None:
        if self.screen.compare(tk.INSERT, "<=", self.input_start):
            return "break"
        return None

    def _on_home(self, _event: tk.Event) -> str:
        self.screen.mark_set("insert", self.input_start)
        return "break"

    def _on_backspace(self, _event: tk.Event) -> str | None:
        if self.screen.compare(tk.INSERT, "<=", self.input_start):
            return "break"
        return None

    def _history_up(self, _event: tk.Event) -> str:
        if not self.history:
            return "break"
        if self.history_index is None:
            self.history_index = len(self.history) - 1
        else:
            self.history_index = max(0, self.history_index - 1)
        self.replace_current_input(self.history[self.history_index])
        return "break"

    def _history_down(self, _event: tk.Event) -> str:
        if self.history_index is None:
            return "break"
        self.history_index += 1
        if self.history_index >= len(self.history):
            self.history_index = None
            self.replace_current_input("")
        else:
            self.replace_current_input(self.history[self.history_index])
        return "break"

    def _on_enter(self, _event: tk.Event) -> str:
        command = self.current_input().strip()
        self.write("\n")
        if command:
            self.last_tab_input = ""
            self.history.append(command)
            self.history_index = None
            self.run_command(command)
            if command.lower() == "exit":
                return "break"
        self._prompt()
        return "break"

    def _on_tab(self, _event: tk.Event) -> str:
        command = self.current_input()
        completion = self.get_completion(command)
        if not completion.matches:
            return "break"

        if len(completion.matches) == 1:
            self.replace_current_input(completion.replacement_for(completion.matches[0]))
            self.last_tab_input = ""
            return "break"

        common = shared_prefix(completion.matches)
        if common and len(common) > len(completion.partial):
            self.replace_current_input(completion.replacement_for(common))
            self.last_tab_input = self.current_input()
            return "break"

        if self.last_tab_input == command:
            self.write("\n")
            self.write_columns(completion.matches)
            self._prompt()
            self.replace_current_input(command)
            self.last_tab_input = ""
        else:
            self.last_tab_input = command
        return "break"

    def get_completion(self, command: str) -> "Completion":
        tokens, ends_with_space = split_command(command)
        if not tokens:
            return Completion(command, "", COMMANDS, lambda match: match + " ")

        if len(tokens) == 1 and not ends_with_space:
            partial = tokens[0].lower()
            matches = [name for name in COMMANDS if name.startswith(partial)]
            return Completion(command, tokens[0], matches, lambda match: match + " ")

        root_command = tokens[0].lower()
        if root_command == "dillrex" and len(tokens) == 2 and not ends_with_space:
            subcommands = ["code", "new", "run"]
            partial = tokens[1].lower()
            matches = [name for name in subcommands if name.startswith(partial)]
            return Completion(command, tokens[1], matches, lambda match: replace_last_token(command, match + " "))

        if root_command == "project" and len(tokens) == 2 and not ends_with_space:
            subcommands = ["new", "run"]
            partial = tokens[1].lower()
            matches = [name for name in subcommands if name.startswith(partial)]
            return Completion(command, tokens[1], matches, lambda match: replace_last_token(command, match + " "))

        if root_command == "project" and len(tokens) >= 3 and tokens[1].lower() == "new":
            return Completion(command, "", [], lambda match: command)

        if root_command not in PATH_COMMANDS and root_command != "dillrex":
            return Completion(command, "", [], lambda match: command)

        partial = "" if ends_with_space else tokens[-1]
        matches = self.path_matches(partial, dirs_only=root_command == "cd")
        return Completion(command, partial, matches, lambda match: replace_last_token(command, match))

    def path_matches(self, partial: str, dirs_only: bool = False) -> list[str]:
        raw = partial.strip('"')
        path = Path(raw)
        if path.is_absolute():
            search_dir = path.parent
            prefix = path.name.lower()
            display_prefix = str(path.parent) + "\\"
        else:
            parent_text = str(path.parent)
            search_dir = self.cwd if parent_text in {"", "."} else self.cwd / path.parent
            prefix = path.name.lower()
            display_prefix = "" if parent_text in {"", "."} else parent_text + "\\"

        if not search_dir.exists() or not search_dir.is_dir():
            return []

        matches = []
        for item in sorted(search_dir.iterdir(), key=lambda candidate: (candidate.is_file(), candidate.name.lower())):
            if dirs_only and not item.is_dir():
                continue
            if not item.name.lower().startswith(prefix):
                continue
            value = display_prefix + item.name
            if item.is_dir():
                value += "\\"
            if " " in value:
                value = f'"{value}"'
            matches.append(value)
        return matches

    def write_columns(self, values: list[str]) -> None:
        if not values:
            return
        width = max(len(value) for value in values) + 3
        columns = max(1, 80 // width)
        for index, value in enumerate(values, start=1):
            self.write(value.ljust(width), "cyan")
            if index % columns == 0:
                self.write("\n")
        if len(values) % columns != 0:
            self.write("\n")

    def run_command(self, command: str) -> None:
        try:
            parts = shlex.split(command, posix=False)
        except ValueError as exc:
            self.write(f"Command error: {exc}\n", "error")
            return
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]

        handlers = {
            "clear": self.clear,
            "cls": self.clear,
            "exit": self.exit,
            "pwd": self.pwd,
            "cd": self.cd,
            "ls": self.ls,
            "dir": self.ls,
            "mkdir": self.mkdir,
            "touch": self.touch,
            "new": self.new_file,
            "run": self.run_file_command,
            "cat": self.cat,
            "type": self.cat,
            "echo": self.echo,
            "open": self.open_path,
            "project": self.project,
            "start": self.open_path,
            "help": self.help,
            "dillrex": self.dillrex,
        }

        handler = handlers.get(cmd)
        if handler:
            handler(args)
            return

        self.run_system_command(command)

    def clear(self, _args: list[str]) -> None:
        self.screen.delete("1.0", tk.END)
        self._banner()

    def exit(self, _args: list[str]) -> None:
        self.root.destroy()

    def pwd(self, _args: list[str]) -> None:
        self.write(f"{self.cwd}\n")

    def cd(self, args: list[str]) -> None:
        if not args:
            self.write(f"{self.cwd}\n")
            return
        target = self.resolve_path(args[0])
        if not target.exists() or not target.is_dir():
            self.write(f"Folder not found: {target}\n", "error")
            return
        self.cwd = target.resolve()

    def ls(self, args: list[str]) -> None:
        target = self.resolve_path(args[0]) if args else self.cwd
        if not target.exists():
            self.write(f"Path not found: {target}\n", "error")
            return
        if target.is_file():
            self.write(f"{target.name}\n")
            return
        for path in sorted(target.iterdir(), key=lambda item: (item.is_file(), item.name.lower())):
            suffix = "/" if path.is_dir() else ""
            self.write(f"{path.name}{suffix}\n")

    def mkdir(self, args: list[str]) -> None:
        if not args:
            self.write("Usage: mkdir folder-name\n", "warn")
            return
        path = self.resolve_path(args[0])
        path.mkdir(parents=True, exist_ok=True)

    def touch(self, args: list[str]) -> None:
        if not args:
            self.write("Usage: touch file-name\n", "warn")
            return
        path = self.resolve_path(args[0])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    def new_file(self, args: list[str]) -> None:
        if not args:
            name = simpledialog.askstring("New file", "File name:", parent=self.root)
            if not name:
                return
        else:
            name = args[0]
        path = self.resolve_path(name)
        if path.exists():
            self.write(f"File already exists: {path}\n", "warn")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        content = FILE_TEMPLATES.get(path.suffix.lower(), "")
        path.write_text(content, encoding="utf-8")
        self.write(f"Created {path.name}\n", "accent")

    def run_file_command(self, args: list[str]) -> None:
        if not args:
            self.write("Usage: run file.drx\n", "warn")
            return
        path = self.resolve_path(args[0])
        if path.suffix.lower() == ".drx":
            self.dillrex_run([str(path)])
            return
        self.run_system_command(" ".join(["\"" + str(path) + "\"", *args[1:]]))

    def cat(self, args: list[str]) -> None:
        if not args:
            self.write("Usage: cat file-name\n", "warn")
            return
        path = self.resolve_path(args[0])
        if not path.exists() or not path.is_file():
            self.write(f"File not found: {path}\n", "error")
            return
        try:
            self.write(path.read_text(encoding="utf-8"))
            self.write("\n")
        except UnicodeDecodeError:
            self.write("Cannot print binary file.\n", "error")

    def echo(self, args: list[str]) -> None:
        self.write(" ".join(args) + "\n")

    def open_path(self, args: list[str]) -> None:
        if not args:
            selected = filedialog.askdirectory(title="Choose folder", initialdir=str(self.cwd))
            if selected:
                self.cwd = Path(selected)
            return
        path = self.resolve_path(args[0])
        if not path.exists():
            self.write(f"Path not found: {path}\n", "error")
            return
        subprocess.Popen(["explorer", str(path)])

    def help(self, _args: list[str]) -> None:
        self.write("Commands: new, run, project, ls, dir, cd, pwd, mkdir, touch, cat, type, echo, open, clear, cls, exit\n")
        self.write("Examples: new notes.txt, new app.drx, run app.drx, dillrex code print(\"hello\")\n")
        self.write("Projects: project new my-app, project run\n")
        self.write("Autocomplete: press Tab to complete, press Tab twice to show options.\n")

    def project(self, args: list[str]) -> None:
        if not args:
            self.write("Usage: project new my-app OR project run\n", "warn")
            return
        action = args[0].lower()
        if action == "new":
            self.project_new(args[1:])
            return
        if action == "run":
            self.project_run()
            return
        self.write(f"Unknown project command: {action}\n", "error")

    def project_new(self, args: list[str]) -> None:
        if not args:
            name = simpledialog.askstring("New Dillrex project", "Project name:", parent=self.root)
            if not name:
                return
        else:
            name = args[0]

        project_path = self.resolve_path(name)
        if project_path.exists():
            self.write(f"Project already exists: {project_path}\n", "warn")
            return

        project_path.mkdir(parents=True)
        for folder in PROJECT_FOLDERS:
            (project_path / folder).mkdir()

        config = {
            "name": project_path.name,
            "version": "0.1.0",
            "main": "main.drx",
            "source": "src",
            "assets": "assets",
            "build": "build",
        }
        (project_path / "dillrex.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        (project_path / "main.drx").write_text(DILLREX_TEMPLATE, encoding="utf-8")

        self.cwd = project_path.resolve()
        self.write(f"Created project {project_path.name}\n", "accent")
        self.write(f"Folder: {self.cwd}\n")

    def project_run(self) -> None:
        project_path = self.find_project_root()
        if project_path is None:
            self.write("No dillrex.json found in this folder or its parents.\n", "error")
            return

        config_path = project_path / "dillrex.json"
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.write(f"Invalid dillrex.json: {exc}\n", "error")
            return

        main_name = config.get("main", "main.drx")
        main_path = project_path / main_name
        self.dillrex_run([str(main_path)])

    def find_project_root(self) -> Path | None:
        current = self.cwd.resolve()
        while True:
            if (current / "dillrex.json").exists():
                return current
            if current.parent == current:
                return None
            current = current.parent

    def dillrex(self, args: list[str]) -> None:
        if not args:
            self.write("Usage: run file.drx\n", "warn")
            return
        action = args[0].lower()
        rest = args[1:]
        if action == "new":
            self.new_file(rest)
        elif action == "run":
            self.dillrex_run(rest)
        elif action == "code":
            self.dillrex_code(rest)
        else:
            self.write(f"Unknown Dillrex command: {action}\n", "error")

    def dillrex_run(self, args: list[str]) -> None:
        if not args:
            selected = filedialog.askopenfilename(
                title="Run Dillrex file",
                initialdir=str(self.cwd),
                filetypes=[("Dillrex files", "*.drx"), ("All files", "*.*")],
            )
            if not selected:
                return
            path = Path(selected)
        else:
            path = self.resolve_dillrex_path(args[0])

        captured = io.StringIO()

        def output(*values: object) -> None:
            print(*values, file=captured)

        def input_func(prompt: str) -> str:
            return simpledialog.askstring("Dillrex input", prompt, parent=self.root) or ""

        try:
            with contextlib.redirect_stdout(captured):
                run_file(path, output=output, input_func=input_func, work_dir=self.cwd)
        except DillrexError as exc:
            self.write(f"Dillrex error: {exc}\n", "error")
            return
        except Exception as exc:
            self.write(f"Terminal error: {exc}\n", "error")
            return

        self.write(captured.getvalue() or "(no output)\n")

    def dillrex_code(self, args: list[str]) -> None:
        code = " ".join(args)
        if not code:
            self.write("Usage: dillrex code print(\"hello\")\n", "warn")
            return
        source = code if code.lstrip().startswith("fn ") else f"fn main then\n{code}\nend\nmain()"
        captured = io.StringIO()

        def output(*values: object) -> None:
            print(*values, file=captured)

        try:
            with contextlib.redirect_stdout(captured):
                run_source(source, output=output)
        except DillrexError as exc:
            self.write(f"Dillrex error: {exc}\n", "error")
            return
        self.write(captured.getvalue() or "(no output)\n")

    def run_system_command(self, command: str) -> None:
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except Exception as exc:
            self.write(f"Command failed: {exc}\n", "error")
            return
        if result.stdout:
            self.write(result.stdout)
        if result.stderr:
            self.write(result.stderr, "error")

    def resolve_path(self, raw: str) -> Path:
        value = raw.strip('"')
        matches = glob.glob(str(self.cwd / value))
        if matches:
            return Path(matches[0])
        path = Path(value)
        if not path.is_absolute():
            path = self.cwd / path
        return path

    def resolve_dillrex_path(self, raw: str) -> Path:
        path = self.resolve_path(raw)
        if path.suffix == "":
            path = path.with_suffix(".drx")
        return path

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    DillrexTerminalApp().run()
    return 0


class Completion:
    def __init__(self, command: str, partial: str, matches: list[str], replacer):
        self.command = command
        self.partial = partial
        self.matches = matches
        self.replacer = replacer

    def replacement_for(self, value: str) -> str:
        return self.replacer(value)


def split_command(command: str) -> tuple[list[str], bool]:
    ends_with_space = command.endswith((" ", "\t"))
    try:
        return shlex.split(command, posix=False), ends_with_space
    except ValueError:
        return command.split(), ends_with_space


def replace_last_token(command: str, replacement: str) -> str:
    if command.endswith((" ", "\t")):
        return command + replacement
    stripped = command.rstrip()
    split_at = max(stripped.rfind(" "), stripped.rfind("\t"))
    if split_at == -1:
        return replacement
    return stripped[: split_at + 1] + replacement


def shared_prefix(values: list[str]) -> str:
    if not values:
        return ""
    prefix = values[0]
    for value in values[1:]:
        while not value.startswith(prefix) and prefix:
            prefix = prefix[:-1]
    return prefix


if __name__ == "__main__":
    raise SystemExit(main())
