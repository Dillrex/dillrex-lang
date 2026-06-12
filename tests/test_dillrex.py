import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from dillrex.runtime import run_file, run_source


class DillrexRuntimeTests(unittest.TestCase):
    def test_full_dillrex_program(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            run_source(
                """
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

                    loop count <= 3 then
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
                """,
                input_func=self.fake_inputs("Dylan", "18"),
            )

        self.assertEqual(
            output.getvalue().splitlines(),
            [
                "Welcome to Dillrex",
                "Hello Dylan",
                "You are an adult",
                "Count: 1",
                "Count: 2",
                "Count: 3",
                "10 + 5 = 15",
            ],
        )

    def test_logic_words(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            run_source(
                """
                set age = 21
                set name = "Dylan"
                set active = true

                if age >= 18 and name == "Dylan" then
                    print("Allowed")
                end

                if not false or active then
                    print("Logic works")
                end
                """
            )

        self.assertEqual(output.getvalue().splitlines(), ["Allowed", "Logic works"])

    def test_math_operators_and_helpers(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            run_source(
                """
                print(2 + 3 * 4)
                print((2 + 3) * 4)
                print(10 % 3)
                print(2 ** 3)
                print(round(2.6))
                print(floor(2.9))
                print(ceil(2.1))
                print(abs(-5))
                print(min(4, 2, 9))
                print(max(4, 2, 9))
                """
            )

        self.assertEqual(
            output.getvalue().splitlines(),
            ["14", "20", "1", "8", "3", "2", "3", "5", "2", "9"],
        )

    def test_print_ask_and_null(self):
        output = io.StringIO()
        prompts = []

        def fake_input(prompt):
            prompts.append(prompt)
            return "Dylan"

        with contextlib.redirect_stdout(output):
            run_source(
                """
                set name = ask("Name: ")
                set nothinghere = null

                print()
                print("Name:", name, true, false, nothinghere)
                print("Score: " + 10)
                """,
                input_func=fake_input,
            )

        self.assertEqual(prompts, ["Name: "])
        self.assertEqual(
            output.getvalue().splitlines(),
            ["", "Name: Dylan true false null", "Score: 10"],
        )

    def test_lists_strings_and_indexing(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            run_source(
                """
                set tools = ["scanner", "radio"]
                push(tools, "laptop")
                set tools[1] = upper("antenna")

                print(len(tools))
                print(tools[0])
                print(tools[1])
                print(contains("hello", "ell"))
                print(split("a,b,c", ",")[2])
                print(replace("hi bob", "bob", "Dylan"))
                """
            )

        self.assertEqual(
            output.getvalue().splitlines(),
            ["3", "scanner", "ANTENNA", "true", "c", "hi Dylan"],
        )

    def test_files_imports_args_and_try_catch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tools.drx").write_text(
                """
                fn double(x) then
                    return x * 2
                end
                """,
                encoding="utf-8",
            )
            main = root / "main.drx"
            main.write_text(
                """
                import "tools.drx"

                write(args[1], upper(read(args[0])))
                append(args[1], "\\nDONE")
                print(double(6))
                print(listfiles(".")[0])

                try then
                    throw "custom problem"
                catch err then
                    print("caught " + err)
                end
                """,
                encoding="utf-8",
            )
            (root / "input.txt").write_text("hello", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                run_file(main, args=["input.txt", "output.txt"], work_dir=root)

            self.assertEqual((root / "output.txt").read_text(encoding="utf-8"), "HELLO\nDONE")
            self.assertEqual(output.getvalue().splitlines(), ["12", "input.txt", "caught custom problem"])

    def fake_inputs(self, *values):
        answers = list(values)

        def fake_input(_prompt):
            return answers.pop(0)

        return fake_input


if __name__ == "__main__":
    unittest.main()
