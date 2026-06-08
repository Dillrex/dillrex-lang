import contextlib
import io
import unittest

from dillrex.runtime import run_source


class DillrexRuntimeTests(unittest.TestCase):
    def test_print_if_else_and_loop(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            run_source(
                """
                fn main() {
                    name = "Dylan"

                    if name == "Dylan" {
                        print("Welcome back Dylan")
                    } else {
                        print("Hello " + name)
                    }

                    x = 0
                    loop x < 3 {
                        print(x)
                        x = x + 1
                    }
                }
                """
            )

        self.assertEqual(
            output.getvalue().splitlines(),
            ["Welcome back Dylan", "0", "1", "2"],
        )


if __name__ == "__main__":
    unittest.main()
