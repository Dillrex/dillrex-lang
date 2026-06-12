import json
import tempfile
import unittest
from pathlib import Path

from dillrex.runtime import run_file


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "bootstrap" / "dillrex-self.drx"
DILLREXC = ROOT / "bootstrap" / "dillrexc.drx"


class BootstrapTests(unittest.TestCase):
    def run_bootstrap(self, *args):
        return self.run_drx(BOOTSTRAP, *args)

    def run_dillrexc(self, *args):
        return self.run_drx(DILLREXC, *args)

    def run_drx(self, path, *args):
        lines = []

        def capture(*values):
            lines.append(" ".join(values))

        run_file(path, output=capture, args=list(args), work_dir=ROOT)
        return lines

    def after_runner_marker(self, lines):
        marker = "Running with Dillrex-built runner"
        self.assertIn(marker, lines)
        return lines[lines.index(marker) + 1 :]

    def test_bootstrap_runner_executes_loop_program(self):
        lines = self.run_bootstrap("examples/no_input.drx")

        self.assertIn("Tokens: 34", lines)
        self.assertIn("Functions: 1", lines)
        self.assertEqual(
            self.after_runner_marker(lines),
            ["Hello from Dillrex", "x = 0", "x = 1", "x = 2"],
        )

    def test_bootstrap_runner_executes_math_program(self):
        lines = self.run_bootstrap("--quiet", "examples/math.drx")

        self.assertEqual(
            lines,
            ["14", "20", "1", "8", "3", "2", "3", "5", "2", "9"],
        )

    def test_bootstrap_runner_loads_relative_imports_and_file_args(self):
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
                """,
                encoding="utf-8",
            )
            input_path = root / "input.txt"
            output_path = root / "output.txt"
            input_path.write_text("hello", encoding="utf-8")

            lines = self.run_bootstrap("--quiet", str(main), str(input_path), str(output_path))

            self.assertEqual(output_path.read_text(encoding="utf-8"), "HELLO\nDONE")
            self.assertEqual(lines, ["12"])

    def test_dillrex_built_runner_can_run_the_bootstrap_driver(self):
        lines = self.run_bootstrap(
            "--quiet",
            "bootstrap/dillrex-self.drx",
            "--quiet",
            "examples/no_input.drx",
        )

        self.assertEqual(lines, ["Hello from Dillrex", "x = 0", "x = 1", "x = 2"])

    def test_quiet_mode_passes_clean_program_args(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            main = root / "args.drx"
            main.write_text(
                """
                print(args[0])
                print(args[1])
                """,
                encoding="utf-8",
            )

            lines = self.run_bootstrap("--quiet", str(main), "first", "second")

            self.assertEqual(lines, ["first", "second"])

    def test_tokens_mode_outputs_machine_readable_tokens_only(self):
        lines = self.run_bootstrap("--tokens", "examples/no_input.drx")

        self.assertEqual(lines[0], 'TOK\tFN\t"fn"\t3\t1')
        self.assertEqual(lines[-1], 'TOK\tEOF\t""\t14\t1')
        self.assertNotIn("Running with Dillrex-built runner", lines)
        self.assertNotIn("Hello from Dillrex", lines)

    def test_ast_mode_outputs_machine_readable_program_tree_only(self):
        lines = self.run_bootstrap("--ast", "examples/no_input.drx")

        self.assertEqual(len(lines), 1)
        program = json.loads(lines[0])
        self.assertEqual(program[0], "program")
        self.assertEqual(program[2][0][1], "main")
        self.assertEqual(program[3][0], ["expr", ["call", "main", []]])

    def test_dillrexc_frontend_runs_programs(self):
        lines = self.run_dillrexc("run", "examples/no_input.drx")

        self.assertEqual(lines, ["Hello from Dillrex", "x = 0", "x = 1", "x = 2"])

    def test_dillrexc_frontend_reports_check_summary(self):
        lines = self.run_dillrexc("check", "examples/no_input.drx")

        self.assertEqual(lines, ["CHECK\texamples/no_input.drx\t34\t0\t1\t1"])

    def test_dillrexc_frontend_exposes_tokens_and_ast(self):
        token_lines = self.run_dillrexc("tokens", "examples/no_input.drx")
        ast_lines = self.run_dillrexc("ast", "examples/no_input.drx")

        self.assertEqual(token_lines[0], 'TOK\tFN\t"fn"\t3\t1')
        self.assertEqual(json.loads(ast_lines[0])[2][0][1], "main")

    def test_dillrexc_frontend_runs_through_self_host_chain(self):
        lines = self.run_bootstrap(
            "--quiet",
            "bootstrap/dillrexc.drx",
            "run",
            "examples/no_input.drx",
        )

        self.assertEqual(lines, ["Hello from Dillrex", "x = 0", "x = 1", "x = 2"])

    def test_dillrexc_build_writes_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "no_input.drxc"

            lines = self.run_dillrexc("build", "examples/no_input.drx", str(output_path))

            artifact = output_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines, [f"BUILT\t{output_path}"])
            self.assertEqual(artifact[0], "DILLREX-COMPILED\t0.1")
            self.assertEqual(artifact[1], 'SOURCE\t"examples/no_input.drx"')
            self.assertEqual(artifact[2], "TOKENS\t34")
            self.assertEqual(artifact[5], "BODY\t1")
            self.assertEqual(json.loads(artifact[6].removeprefix("AST\t"))[2][0][1], "main")

    def test_dillrexc_build_runs_through_self_host_chain(self):
        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "math.drxc"

            lines = self.run_bootstrap(
                "--quiet",
                "bootstrap/dillrexc.drx",
                "build",
                "examples/math.drx",
                str(output_path),
            )

            artifact = output_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines, [f"BUILT\t{output_path}"])
            self.assertEqual(artifact[0], "DILLREX-COMPILED\t0.1")
            self.assertEqual(artifact[2], "TOKENS\t82")

    def test_dillrexc_reads_artifact_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "no_input.drxc"

            self.run_dillrexc("build", "examples/no_input.drx", str(output_path))
            lines = self.run_dillrexc("read", str(output_path))

            self.assertEqual(lines[0], f"ARTIFACT\t{output_path}")
            self.assertEqual(lines[1], 'SOURCE\t"examples/no_input.drx"')
            self.assertEqual(lines[2], "TOKENS\t34")
            self.assertEqual(lines[4], "FUNCTIONS\t1")
            self.assertTrue(lines[6].startswith("AST_BYTES\t"))
            self.assertEqual(lines[7], "AST_ROOT\tprogram")
            self.assertEqual(lines[9], "AST_FUNCTIONS\t1")

    def test_dillrexc_reads_artifact_through_self_host_chain(self):
        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "math.drxc"

            self.run_bootstrap(
                "--quiet",
                "bootstrap/dillrexc.drx",
                "build",
                "examples/math.drx",
                str(output_path),
            )
            lines = self.run_bootstrap(
                "--quiet",
                "bootstrap/dillrexc.drx",
                "read",
                str(output_path),
            )

            self.assertEqual(lines[0], f"ARTIFACT\t{output_path}")
            self.assertEqual(lines[2], "TOKENS\t82")
            self.assertEqual(lines[5], "BODY\t10")
            self.assertEqual(lines[7], "AST_ROOT\tprogram")
            self.assertEqual(lines[10], "AST_BODY\t10")

    def test_dillrexc_decodes_artifact_ast(self):
        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "no_input.drxc"

            self.run_dillrexc("build", "examples/no_input.drx", str(output_path))
            lines = self.run_dillrexc("decode", str(output_path))

            self.assertEqual(len(lines), 1)
            program = json.loads(lines[0])
            self.assertEqual(program[0], "program")
            self.assertEqual(program[2][0][1], "main")

    def test_dillrexc_decodes_artifact_ast_through_self_host_chain(self):
        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "math.drxc"

            self.run_bootstrap(
                "--quiet",
                "bootstrap/dillrexc.drx",
                "build",
                "examples/math.drx",
                str(output_path),
            )
            lines = self.run_bootstrap(
                "--quiet",
                "bootstrap/dillrexc.drx",
                "decode",
                str(output_path),
            )

            self.assertEqual(len(lines), 1)
            program = json.loads(lines[0])
            self.assertEqual(program[0], "program")
            self.assertEqual(len(program[3]), 10)

    def test_dillrexc_runs_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "no_input.drxc"

            self.run_dillrexc("build", "examples/no_input.drx", str(output_path))
            lines = self.run_dillrexc("run-artifact", str(output_path))

            self.assertEqual(lines, ["Hello from Dillrex", "x = 0", "x = 1", "x = 2"])

    def test_dillrexc_runs_artifact_with_program_args(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            artifact_path = root / "upper.drxc"
            input_path = root / "input.txt"
            output_path = root / "output.txt"
            input_path.write_text("hello artifact args", encoding="utf-8")

            self.run_dillrexc("build", "examples/upperfile.drx", str(artifact_path))
            lines = self.run_dillrexc("run-artifact", str(artifact_path), str(input_path), str(output_path))

            self.assertEqual(output_path.read_text(encoding="utf-8"), "HELLO ARTIFACT ARGS")
            self.assertEqual(lines, [f"Wrote uppercase text to {output_path}"])

    def test_dillrexc_runs_artifact_through_self_host_chain(self):
        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "math.drxc"

            self.run_bootstrap(
                "--quiet",
                "bootstrap/dillrexc.drx",
                "build",
                "examples/math.drx",
                str(output_path),
            )
            lines = self.run_bootstrap(
                "--quiet",
                "bootstrap/dillrexc.drx",
                "run-artifact",
                str(output_path),
            )

            self.assertEqual(lines, ["14", "20", "1", "8", "3", "2", "3", "5", "2", "9"])


if __name__ == "__main__":
    unittest.main()
