from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

sys.setrecursionlimit(max(sys.getrecursionlimit(), 20_000))


class DillrexError(Exception):
    """Base error for readable Dillrex failures."""


class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


KEYWORDS = {
    "fn",
    "if",
    "then",
    "else",
    "end",
    "loop",
    "set",
    "return",
    "import",
    "try",
    "catch",
    "throw",
    "true",
    "false",
    "null",
    "and",
    "or",
    "not",
}
SYMBOLS = {"(", ")", "[", "]", ",", "+", "-", "*", "/", "%", "=", "<", ">", "!"}
DOUBLE_SYMBOLS = {"==", "!=", "<=", ">=", "**"}


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    line = 1
    column = 1

    while i < len(source):
        ch = source[i]

        if ch in " \t\r":
            i += 1
            column += 1
            continue
        if ch == "\n":
            i += 1
            line += 1
            column = 1
            continue
        if ch == "#":
            while i < len(source) and source[i] != "\n":
                i += 1
                column += 1
            continue
        if ch == '"':
            start_line = line
            start_column = column
            i += 1
            column += 1
            value = []
            while i < len(source) and source[i] != '"':
                if source[i] == "\\":
                    i += 1
                    column += 1
                    if i >= len(source):
                        raise DillrexError(f"Unfinished string at line {start_line}.")
                    escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                    value.append(escapes.get(source[i], source[i]))
                else:
                    value.append(source[i])
                i += 1
                column += 1
            if i >= len(source):
                raise DillrexError(f"Unfinished string at line {start_line}.")
            i += 1
            column += 1
            tokens.append(Token("STRING", "".join(value), start_line, start_column))
            continue
        if ch.isdigit():
            start = i
            start_column = column
            dot_count = 0
            while i < len(source) and (source[i].isdigit() or source[i] == "."):
                if source[i] == ".":
                    dot_count += 1
                    if dot_count > 1:
                        raise DillrexError(f"Invalid number at line {line}, column {start_column}.")
                i += 1
                column += 1
            value = source[start:i]
            if value.endswith("."):
                raise DillrexError(f"Invalid number at line {line}, column {start_column}.")
            tokens.append(Token("NUMBER", value, line, start_column))
            continue
        if ch.isalpha() or ch == "_":
            start = i
            start_column = column
            while i < len(source) and (source[i].isalnum() or source[i] == "_"):
                i += 1
                column += 1
            value = source[start:i]
            kind = value.upper() if value in KEYWORDS else "NAME"
            tokens.append(Token(kind, value, line, start_column))
            continue
        pair = source[i : i + 2]
        if pair in DOUBLE_SYMBOLS:
            tokens.append(Token(pair, pair, line, column))
            i += 2
            column += 2
            continue
        if ch in SYMBOLS:
            tokens.append(Token(ch, ch, line, column))
            i += 1
            column += 1
            continue
        raise DillrexError(f"Unexpected character {ch!r} at line {line}, column {column}.")

    tokens.append(Token("EOF", "", line, column))
    return tokens


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.index = 0

    def current(self) -> Token:
        return self.tokens[self.index]

    def match(self, *kinds: str) -> Token | None:
        if self.current().kind in kinds:
            token = self.current()
            self.index += 1
            return token
        return None

    def expect(self, kind: str, message: str) -> Token:
        token = self.match(kind)
        if token is None:
            current = self.current()
            raise DillrexError(f"{message} at line {current.line}, column {current.column}.")
        return token

    def parse_program(self) -> dict[str, Any]:
        functions = {}
        imports = []
        body = []
        while self.current().kind != "EOF":
            if self.current().kind == "IMPORT":
                self.match("IMPORT")
                imports.append(self.expect("STRING", "Expected import path").value)
            elif self.current().kind == "FN":
                name, params, function_body = self.parse_function()
                functions[name] = {"params": params, "body": function_body}
            else:
                body.append(self.parse_statement())
        return {"imports": imports, "functions": functions, "body": body}

    def parse_function(self) -> tuple[str, list[str], list[Any]]:
        self.expect("FN", "Expected fn")
        name = self.expect("NAME", "Expected function name").value
        params: list[str] = []
        if self.match("("):
            while True:
                if self.match(")"):
                    break
                params.append(self.expect("NAME", "Expected parameter name").value)
                if self.match(")"):
                    break
                self.expect(",", "Expected comma between parameters")
        self.expect("THEN", "Expected then after function name")
        body = self.parse_block_until({"END"})
        self.expect("END", "Expected end after function")
        return name, params, body

    def parse_block_until(self, endings: set[str]) -> list[Any]:
        statements = []
        while self.current().kind not in endings:
            if self.current().kind == "EOF":
                raise DillrexError("Expected end before the end of the file.")
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self) -> Any:
        if self.match("IF"):
            condition = self.parse_expression()
            self.expect("THEN", "Expected then after if condition")
            then_body = self.parse_block_until({"ELSE", "END"})
            else_body = []
            if self.match("ELSE"):
                else_body = self.parse_block_until({"END"})
            self.expect("END", "Expected end after if")
            return ("if", condition, then_body, else_body)
        if self.match("LOOP"):
            condition = self.parse_expression()
            self.expect("THEN", "Expected then after loop condition")
            body = self.parse_block_until({"END"})
            self.expect("END", "Expected end after loop")
            return ("loop", condition, body)
        if self.match("SET"):
            target = self.parse_assignment_target()
            self.expect("=", "Expected =")
            return ("assign", target, self.parse_expression())
        if self.match("RETURN"):
            if self.current().kind in {"END", "ELSE", "CATCH", "EOF"}:
                return ("return", ("none", None))
            return ("return", self.parse_expression())
        if self.match("TRY"):
            self.expect("THEN", "Expected then after try")
            try_body = self.parse_block_until({"CATCH"})
            self.expect("CATCH", "Expected catch after try block")
            error_name = self.expect("NAME", "Expected error variable name").value
            self.expect("THEN", "Expected then after catch")
            catch_body = self.parse_block_until({"END"})
            self.expect("END", "Expected end after try/catch")
            return ("try", try_body, error_name, catch_body)
        if self.match("THROW"):
            return ("throw", self.parse_expression())

        expression = self.parse_expression()
        return ("expr", expression)

    def parse_assignment_target(self) -> Any:
        target: Any = ("var_target", self.expect("NAME", "Expected variable name").value)
        while self.match("["):
            index = self.parse_expression()
            self.expect("]", "Expected ] after index")
            target = ("index_target", target, index)
        return target

    def parse_expression(self) -> Any:
        return self.parse_or()

    def parse_or(self) -> Any:
        expr = self.parse_and()
        while self.match("OR"):
            right = self.parse_and()
            expr = ("logic", "or", expr, right)
        return expr

    def parse_and(self) -> Any:
        expr = self.parse_comparison()
        while self.match("AND"):
            right = self.parse_comparison()
            expr = ("logic", "and", expr, right)
        return expr

    def parse_comparison(self) -> Any:
        expr = self.parse_addition()
        while self.match("==", "!=", "<", ">", "<=", ">="):
            operator = self.tokens[self.index - 1].kind
            right = self.parse_addition()
            expr = ("binary", operator, expr, right)
        return expr

    def parse_addition(self) -> Any:
        expr = self.parse_multiplication()
        while self.match("+", "-"):
            operator = self.tokens[self.index - 1].kind
            right = self.parse_multiplication()
            expr = ("binary", operator, expr, right)
        return expr

    def parse_multiplication(self) -> Any:
        expr = self.parse_power()
        while self.match("*", "/", "%"):
            operator = self.tokens[self.index - 1].kind
            right = self.parse_power()
            expr = ("binary", operator, expr, right)
        return expr

    def parse_power(self) -> Any:
        expr = self.parse_unary()
        if self.match("**"):
            right = self.parse_power()
            expr = ("binary", "**", expr, right)
        return expr

    def parse_unary(self) -> Any:
        if self.match("NOT"):
            return ("unary", "not", self.parse_unary())
        if self.match("-"):
            return ("unary", "-", self.parse_unary())
        return self.parse_primary()

    def parse_primary(self) -> Any:
        expr: Any
        if token := self.match("NUMBER"):
            expr = ("number", float(token.value) if "." in token.value else int(token.value))
        elif token := self.match("STRING"):
            expr = ("string", token.value)
        elif self.match("TRUE"):
            expr = ("bool", True)
        elif self.match("FALSE"):
            expr = ("bool", False)
        elif self.match("NULL"):
            expr = ("none", None)
        elif token := self.match("NAME"):
            if self.match("("):
                args = []
                if not self.match(")"):
                    while True:
                        args.append(self.parse_expression())
                        if self.match(")"):
                            break
                        self.expect(",", "Expected comma between arguments")
                expr = ("call", token.value, args)
            else:
                expr = ("var", token.value)
        elif self.match("["):
            items = []
            if not self.match("]"):
                while True:
                    items.append(self.parse_expression())
                    if self.match("]"):
                        break
                    self.expect(",", "Expected comma between list items")
            expr = ("list", items)
        elif self.match("("):
            expr = self.parse_expression()
            self.expect(")", "Expected )")
        else:
            current = self.current()
            raise DillrexError(f"Expected expression at line {current.line}, column {current.column}.")

        while self.match("["):
            index = self.parse_expression()
            self.expect("]", "Expected ] after index")
            expr = ("index", expr, index)
        return expr


class Interpreter:
    def __init__(
        self,
        program: dict[str, Any],
        output: Callable[..., Any] = print,
        input_func: Callable[..., str] = input,
        args: list[str] | None = None,
        base_dir: Path | None = None,
        work_dir: Path | None = None,
        imported: set[Path] | None = None,
    ):
        self.program = program
        self.functions = program["functions"]
        self.body = program["body"]
        self.output = output
        self.input_func = input_func
        self.base_dir = base_dir or Path.cwd()
        self.work_dir = work_dir or Path.cwd()
        self.imported = imported if imported is not None else set()
        self.globals: dict[str, Any] = {"args": list(args or [])}
        self.builtins: dict[str, Callable[..., Any]] = {
            "print": self.dillrex_print,
            "ask": self.dillrex_input,
            "len": len,
            "type": self.kind,
            "str": self.to_text,
            "text": self.to_text,
            "num": self.to_number,
            "int": self.to_int,
            "bool": self.to_bool,
            "kind": self.kind,
            "upper": lambda value: self.to_text(value).upper(),
            "lower": lambda value: self.to_text(value).lower(),
            "trim": lambda value: self.to_text(value).strip(),
            "contains": lambda value, search: self.to_text(search) in self.to_text(value),
            "split": lambda value, separator: self.to_text(value).split(self.to_text(separator)),
            "join": lambda values, separator: self.to_text(separator).join(self.to_text(value) for value in values),
            "nativeJoin": lambda values, separator: self.to_text(separator).join(
                self.to_text(value) for value in values
            ),
            "replace": lambda value, old, new: self.to_text(value).replace(self.to_text(old), self.to_text(new)),
            "push": self.list_push,
            "pop": self.list_pop,
            "remove": self.list_remove,
            "read": self.file_read,
            "write": self.file_write,
            "append": self.file_append,
            "exists": self.file_exists,
            "delete": self.file_delete,
            "listfiles": self.file_list,
            "exit": self.exit_program,
            "round": round,
            "floor": math.floor,
            "ceil": math.ceil,
            "abs": abs,
            "min": min,
            "max": max,
        }

    def dillrex_print(self, *values: Any) -> None:
        self.output(*(self.to_text(value) for value in values))

    def dillrex_input(self, prompt: Any = "") -> str:
        return self.input_func(self.to_text(prompt))

    def run(self) -> None:
        self.run_imports()
        if self.body:
            self.execute_block(self.body, self.globals)
            return
        if "main" in self.functions:
            self.call_function("main", [])
            return
        raise DillrexError("No code to run.")

    def call_function(self, name: str, args: list[Any]) -> Any:
        if name in self.builtins:
            return self.builtins[name](*args)
        if name not in self.functions:
            raise DillrexError(f"Unknown function {name}().")
        function = self.functions[name]
        params = function["params"]
        if len(args) != len(params):
            raise DillrexError(f"{name}() expected {len(params)} argument(s), got {len(args)}.")
        variables = dict(self.globals)
        variables.update(zip(params, args))
        try:
            self.execute_block(function["body"], variables)
        except ReturnSignal as signal:
            return signal.value
        return None

    def run_imports(self) -> None:
        for import_name in self.program["imports"]:
            path = self.resolve_import(import_name)
            if path in self.imported:
                continue
            if not path.exists():
                raise DillrexError(f'Could not find imported file "{import_name}".')
            self.imported.add(path)
            imported_program = parse(path.read_text(encoding="utf-8"))
            imported_interpreter = Interpreter(
                imported_program,
                output=self.output,
                input_func=self.input_func,
                args=self.globals["args"],
                base_dir=path.parent,
                work_dir=self.work_dir,
                imported=self.imported,
            )
            imported_interpreter.globals = self.globals
            imported_interpreter.run_imports()
            if imported_interpreter.body:
                imported_interpreter.execute_block(imported_interpreter.body, self.globals)
            self.functions.update(imported_interpreter.functions)

    def execute_block(self, statements: list[Any], variables: dict[str, Any]) -> None:
        for statement in statements:
            kind = statement[0]
            if kind == "assign":
                self.assign(statement[1], self.evaluate(statement[2], variables), variables)
            elif kind == "if":
                _, condition, then_body, else_body = statement
                self.execute_block(then_body if self.evaluate(condition, variables) else else_body, variables)
            elif kind == "loop":
                _, condition, body = statement
                guard = 0
                while self.evaluate(condition, variables):
                    self.execute_block(body, variables)
                    guard += 1
                    if guard > 1_000_000:
                        raise DillrexError("Loop stopped after 1,000,000 turns.")
            elif kind == "expr":
                self.evaluate(statement[1], variables)
            elif kind == "return":
                raise ReturnSignal(self.evaluate(statement[1], variables))
            elif kind == "try":
                _, try_body, error_name, catch_body = statement
                try:
                    self.execute_block(try_body, variables)
                except DillrexError as exc:
                    variables[error_name] = str(exc)
                    self.execute_block(catch_body, variables)
            elif kind == "throw":
                raise DillrexError(self.to_text(self.evaluate(statement[1], variables)))
            else:
                raise DillrexError(f"Unknown statement {kind}.")

    def assign(self, target: Any, value: Any, variables: dict[str, Any]) -> None:
        kind = target[0]
        if kind == "var_target":
            variables[target[1]] = value
            if variables is self.globals:
                self.globals[target[1]] = value
            return
        if kind == "index_target":
            container = self.resolve_target_value(target[1], variables)
            index = self.evaluate(target[2], variables)
            container[int(index)] = value
            return
        raise DillrexError(f"Unknown assignment target {kind}.")

    def resolve_target_value(self, target: Any, variables: dict[str, Any]) -> Any:
        if target[0] == "var_target":
            name = target[1]
            if name not in variables:
                raise DillrexError(f"Unknown variable {name}.")
            return variables[name]
        if target[0] == "index_target":
            container = self.resolve_target_value(target[1], variables)
            index = self.evaluate(target[2], variables)
            return container[int(index)]
        raise DillrexError(f"Unknown assignment target {target[0]}.")

    def evaluate(self, expr: Any, variables: dict[str, Any]) -> Any:
        kind = expr[0]
        if kind in {"number", "string", "bool", "none"}:
            return expr[1]
        if kind == "var":
            name = expr[1]
            if name not in variables:
                raise DillrexError(f"Unknown variable {name}.")
            return variables[name]
        if kind == "list":
            return [self.evaluate(item, variables) for item in expr[1]]
        if kind == "index":
            container = self.evaluate(expr[1], variables)
            index = self.evaluate(expr[2], variables)
            try:
                return container[int(index)]
            except (IndexError, TypeError, ValueError) as exc:
                raise DillrexError(f"Index {index} is out of range.") from exc
        if kind == "call":
            _, name, arg_exprs = expr
            return self.call_function(name, [self.evaluate(arg, variables) for arg in arg_exprs])
        if kind == "unary":
            operator = expr[1]
            value = self.evaluate(expr[2], variables)
            if operator == "not":
                return not self.to_bool(value)
            return -value
        if kind == "logic":
            _, operator, left_expr, right_expr = expr
            return self.evaluate_logic(operator, left_expr, right_expr, variables)
        if kind == "binary":
            _, operator, left_expr, right_expr = expr
            left = self.evaluate(left_expr, variables)
            right = self.evaluate(right_expr, variables)
            return self.apply_operator(operator, left, right)
        raise DillrexError(f"Unknown expression {kind}.")

    def evaluate_logic(self, operator: str, left_expr: Any, right_expr: Any, variables: dict[str, Any]) -> bool:
        if operator not in {"and", "or"}:
            raise DillrexError(f"Unknown logic operator {operator}.")

        operands = [right_expr]
        current = left_expr
        while current[0] == "logic" and current[1] == operator:
            operands.append(current[3])
            current = current[2]
        operands.append(current)
        operands.reverse()

        if operator == "and":
            for operand in operands:
                if not self.to_bool(self.evaluate(operand, variables)):
                    return False
            return True

        for operand in operands:
            if self.to_bool(self.evaluate(operand, variables)):
                return True
        return False

    def list_push(self, values: Any, value: Any) -> None:
        values.append(value)

    def list_pop(self, values: Any) -> Any:
        return values.pop()

    def list_remove(self, values: Any, index: Any) -> Any:
        return values.pop(int(index))

    def resolve_import(self, path: Any) -> Path:
        file_path = Path(self.to_text(path))
        if not file_path.is_absolute():
            file_path = self.base_dir / file_path
        return file_path.resolve()

    def resolve_file(self, path: Any) -> Path:
        file_path = Path(self.to_text(path))
        if not file_path.is_absolute():
            file_path = self.work_dir / file_path
        return file_path.resolve()

    def file_read(self, path: Any) -> str:
        file_path = self.resolve_file(path)
        if not file_path.exists():
            raise DillrexError(f'File "{path}" does not exist.')
        return file_path.read_text(encoding="utf-8")

    def file_write(self, path: Any, text: Any) -> None:
        file_path = self.resolve_file(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.to_text(text), encoding="utf-8")

    def file_append(self, path: Any, text: Any) -> None:
        file_path = self.resolve_file(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(self.to_text(text))

    def file_exists(self, path: Any) -> bool:
        return self.resolve_file(path).exists()

    def file_delete(self, path: Any) -> None:
        file_path = self.resolve_file(path)
        if file_path.exists():
            file_path.unlink()

    def file_list(self, path: Any) -> list[str]:
        folder = self.resolve_file(path)
        return sorted(os.listdir(folder))

    def exit_program(self, code: Any = 0) -> None:
        raise SystemExit(int(code))

    def apply_operator(self, operator: str, left: Any, right: Any) -> Any:
        if operator == "+":
            if isinstance(left, str) or isinstance(right, str):
                return f"{self.to_text(left)}{self.to_text(right)}"
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            return left / right
        if operator == "%":
            return left % right
        if operator == "**":
            return left**right
        if operator == "==":
            left, right = self.comparison_values(left, right)
            return left == right
        if operator == "!=":
            left, right = self.comparison_values(left, right)
            return left != right
        if operator == "<":
            left, right = self.comparison_values(left, right)
            return left < right
        if operator == ">":
            left, right = self.comparison_values(left, right)
            return left > right
        if operator == "<=":
            left, right = self.comparison_values(left, right)
            return left <= right
        if operator == ">=":
            left, right = self.comparison_values(left, right)
            return left >= right
        raise DillrexError(f"Unknown operator {operator}.")

    def comparison_values(self, left: Any, right: Any) -> tuple[Any, Any]:
        if isinstance(left, str) and isinstance(right, (int, float)):
            return self.to_number(left), right
        if isinstance(right, str) and isinstance(left, (int, float)):
            return left, self.to_number(right)
        return left, right

    def to_text(self, value: Any) -> str:
        if value is True:
            return "true"
        if value is False:
            return "false"
        if value is None:
            return "null"
        if isinstance(value, list):
            return "[" + ", ".join(self.to_text(item) for item in value) + "]"
        return str(value)

    def to_number(self, value: Any) -> int | float:
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                return float(value) if "." in value else int(value)
            except ValueError as exc:
                raise DillrexError(f"Cannot convert {value!r} to a number.") from exc
        raise DillrexError(f"Cannot convert {self.kind(value)} to a number.")

    def to_int(self, value: Any) -> int:
        return int(self.to_number(value))

    def to_bool(self, value: Any) -> bool:
        if isinstance(value, str):
            return value.strip().lower() not in {"", "false", "null", "0"}
        return bool(value)

    def kind(self, value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "num"
        if isinstance(value, str):
            return "text"
        if isinstance(value, list):
            return "list"
        return type(value).__name__


def parse(source: str) -> dict[str, Any]:
    return Parser(tokenize(source)).parse_program()


def run_source(
    source: str,
    output: Callable[..., Any] = print,
    input_func: Callable[..., str] = input,
    args: list[str] | None = None,
    base_dir: Path | None = None,
    work_dir: Path | None = None,
) -> None:
    Interpreter(
        parse(source),
        output=output,
        input_func=input_func,
        args=args,
        base_dir=base_dir,
        work_dir=work_dir,
    ).run()


def run_file(
    path: Path,
    output: Callable[..., Any] = print,
    input_func: Callable[..., str] = input,
    args: list[str] | None = None,
    work_dir: Path | None = None,
) -> None:
    if not path.exists():
        raise DillrexError(f"File not found: {path}")
    run_source(
        path.read_text(encoding="utf-8"),
        output=output,
        input_func=input_func,
        args=args,
        base_dir=path.parent,
        work_dir=work_dir or Path.cwd(),
    )


def run_repl() -> None:
    print("Dillrex Shell 0.1")
    print('Type Dillrex code, then a blank line to run it. Try: print("hello")')
    print("Type exit to leave.")
    while True:
        lines = []
        while True:
            prompt = "drx> " if not lines else "...  "
            line = input(prompt)
            if line.strip() == "exit":
                return
            if line == "":
                break
            lines.append(line)
        if not lines:
            continue
        source = "fn main then\n" + "\n".join(lines) + "\nend\nmain()"
        try:
            run_source(source)
        except DillrexError as exc:
            print(f"Dillrex error: {exc}")
