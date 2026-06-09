from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


class DillrexError(Exception):
    """Base error for readable Dillrex failures."""


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


KEYWORDS = {"fn", "if", "else", "loop"}
SYMBOLS = {"(", ")", "{", "}", ",", "+", "-", "*", "/", "=", "<", ">", "!"}
DOUBLE_SYMBOLS = {"==", "!=", "<=", ">="}


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
            while i < len(source) and (source[i].isdigit() or source[i] == "."):
                i += 1
                column += 1
            tokens.append(Token("NUMBER", source[start:i], line, start_column))
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
        while self.current().kind != "EOF":
            name, params, body = self.parse_function()
            functions[name] = {"params": params, "body": body}
        return functions

    def parse_function(self) -> tuple[str, list[str], list[Any]]:
        self.expect("FN", "Expected fn")
        name = self.expect("NAME", "Expected function name").value
        self.expect("(", "Expected ( after function name")
        params: list[str] = []
        if not self.match(")"):
            while True:
                params.append(self.expect("NAME", "Expected parameter name").value)
                if self.match(")"):
                    break
                self.expect(",", "Expected comma between parameters")
        body = self.parse_block()
        return name, params, body

    def parse_block(self) -> list[Any]:
        self.expect("{", "Expected {")
        statements = []
        while not self.match("}"):
            if self.current().kind == "EOF":
                raise DillrexError("Expected } before the end of the file.")
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self) -> Any:
        if self.match("IF"):
            condition = self.parse_expression()
            then_body = self.parse_block()
            else_body = []
            if self.match("ELSE"):
                else_body = self.parse_block()
            return ("if", condition, then_body, else_body)
        if self.match("LOOP"):
            condition = self.parse_expression()
            body = self.parse_block()
            return ("loop", condition, body)

        if self.current().kind == "NAME" and self.tokens[self.index + 1].kind == "=":
            name = self.expect("NAME", "Expected variable name").value
            self.expect("=", "Expected =")
            return ("assign", name, self.parse_expression())

        expression = self.parse_expression()
        return ("expr", expression)

    def parse_expression(self) -> Any:
        return self.parse_comparison()

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
        expr = self.parse_unary()
        while self.match("*", "/"):
            operator = self.tokens[self.index - 1].kind
            right = self.parse_unary()
            expr = ("binary", operator, expr, right)
        return expr

    def parse_unary(self) -> Any:
        if self.match("-"):
            return ("unary", "-", self.parse_unary())
        return self.parse_primary()

    def parse_primary(self) -> Any:
        if token := self.match("NUMBER"):
            return ("number", float(token.value) if "." in token.value else int(token.value))
        if token := self.match("STRING"):
            return ("string", token.value)
        if token := self.match("NAME"):
            if self.match("("):
                args = []
                if not self.match(")"):
                    while True:
                        args.append(self.parse_expression())
                        if self.match(")"):
                            break
                        self.expect(",", "Expected comma between arguments")
                return ("call", token.value, args)
            return ("var", token.value)
        if self.match("("):
            expr = self.parse_expression()
            self.expect(")", "Expected )")
            return expr
        current = self.current()
        raise DillrexError(f"Expected expression at line {current.line}, column {current.column}.")


class Interpreter:
    def __init__(
        self,
        functions: dict[str, Any],
        output: Callable[..., Any] = print,
        input_func: Callable[[str], str] = input,
    ):
        self.functions = functions
        self.builtins: dict[str, Callable[..., Any]] = {
            "print": output,
            "in": input_func,
        }

    def run(self) -> None:
        if "main" not in self.functions:
            raise DillrexError("No main() function found.")
        self.call_function("main", [])

    def call_function(self, name: str, args: list[Any]) -> Any:
        if name in self.builtins:
            return self.builtins[name](*args)
        if name not in self.functions:
            raise DillrexError(f"Unknown function {name}().")
        function = self.functions[name]
        params = function["params"]
        if len(args) != len(params):
            raise DillrexError(f"{name}() expected {len(params)} argument(s), got {len(args)}.")
        variables = dict(zip(params, args))
        self.execute_block(function["body"], variables)
        return None

    def execute_block(self, statements: list[Any], variables: dict[str, Any]) -> None:
        for statement in statements:
            kind = statement[0]
            if kind == "assign":
                variables[statement[1]] = self.evaluate(statement[2], variables)
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
            else:
                raise DillrexError(f"Unknown statement {kind}.")

    def evaluate(self, expr: Any, variables: dict[str, Any]) -> Any:
        kind = expr[0]
        if kind in {"number", "string"}:
            return expr[1]
        if kind == "var":
            name = expr[1]
            if name not in variables:
                raise DillrexError(f"Unknown variable {name}.")
            return variables[name]
        if kind == "call":
            _, name, arg_exprs = expr
            return self.call_function(name, [self.evaluate(arg, variables) for arg in arg_exprs])
        if kind == "unary":
            return -self.evaluate(expr[2], variables)
        if kind == "binary":
            _, operator, left_expr, right_expr = expr
            left = self.evaluate(left_expr, variables)
            right = self.evaluate(right_expr, variables)
            return self.apply_operator(operator, left, right)
        raise DillrexError(f"Unknown expression {kind}.")

    def apply_operator(self, operator: str, left: Any, right: Any) -> Any:
        if operator == "+":
            if isinstance(left, str) or isinstance(right, str):
                return f"{left}{right}"
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            return left / right
        if operator == "==":
            return left == right
        if operator == "!=":
            return left != right
        if operator == "<":
            return left < right
        if operator == ">":
            return left > right
        if operator == "<=":
            return left <= right
        if operator == ">=":
            return left >= right
        raise DillrexError(f"Unknown operator {operator}.")


def parse(source: str) -> dict[str, Any]:
    return Parser(tokenize(source)).parse_program()


def run_source(
    source: str,
    output: Callable[..., Any] = print,
    input_func: Callable[[str], str] = input,
) -> None:
    Interpreter(parse(source), output=output, input_func=input_func).run()


def run_file(
    path: Path,
    output: Callable[..., Any] = print,
    input_func: Callable[[str], str] = input,
) -> None:
    if not path.exists():
        raise DillrexError(f"File not found: {path}")
    run_source(path.read_text(encoding="utf-8"), output=output, input_func=input_func)


def run_repl() -> None:
    print("Dillrex Terminal 0.1")
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
        source = "fn main() {\n" + "\n".join(lines) + "\n}"
        try:
            run_source(source)
        except DillrexError as exc:
            print(f"Dillrex error: {exc}")
