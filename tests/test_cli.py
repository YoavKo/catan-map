import contextlib
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from catan_map import cli, generate, parse, serialize

ROOT = Path(__file__).resolve().parents[1]
BASE = "WSGOCWSGDOWCSGOCWSG563a4b892c563b9a48"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run(*argv):
    """(exit code, stdout, stderr) of the command line, without starting a process."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = cli.main(list(argv))
        except SystemExit as exit_:       # argparse exits on a usage error
            code = exit_.code
    return code, out.getvalue(), err.getvalue()


def lines_of(stdout):
    return dict(line.split(": ", 1) if ": " in line else (line, "") for line in stdout.split("\n") if ":" in line)


class MakingABoard(unittest.TestCase):
    def test_without_arguments_a_random_three_letter_seed(self):
        code, out, err = run()
        self.assertEqual((code, err), (0, ""))
        seed = re.match(r"seed:   ([A-Z]{3})\n", out)
        self.assertTrue(seed, out)
        string = out.split("string: ")[1].strip()
        self.assertEqual(parse(string).board, generate(seed.group(1)))

    def test_two_runs_give_different_seeds(self):
        seeds = {re.match(r"seed:   (\w+)", run()[1]).group(1) for _ in range(20)}
        self.assertGreater(len(seeds), 15)

    def test_a_seed_always_gives_the_same_output(self):
        first = run("--seed", "KMQXRT", "--format", "s", "--no-pipes")
        self.assertEqual(first, run("--seed", "kmqxrt", "--format", "s", "--no-pipes"))
        self.assertEqual(first[1], "seed:   KMQXRT\nstring: CGGWSWWCODGCGOSSOSW58ab94ca33645298b6\n")

    def test_the_default_layout_is_paired(self):
        out = run("--seed", "KMQXRT", "--no-pipes")[1]
        self.assertEqual(out.split("string: ")[1].strip(), serialize(generate("KMQXRT"), "p"))

    def test_pipes_are_written_by_default(self):
        out = run("--seed", "KMQXRT-P")[1]
        self.assertEqual(out.split("string: ")[1].strip(), serialize(generate("KMQXRT", ports=True), "p", True, True))
        self.assertIn("|", out)
        self.assertEqual(run("--seed", "KMQXRT", "--pipes")[0], 2)      # the old flag is gone

    def test_the_new_rule_options(self):
        code, out, _ = run("--seed", "KMQXRT", "--no-same-neighbours", "--allow-adjacent-2-12", "--no-pipes")
        self.assertEqual(code, 0)
        self.assertIn("seed:   KMQXRT-LU\n", out)
        self.assertEqual(out.split("string: ")[1].strip(), serialize(generate("KMQXRT", no_same_neighbours=True, allow_adjacent_low_high=True), "p"))
        self.assertIn("seed:   KMQXRT-LU\n", run("--seed", "KMQXRT-L", "--no-same-neighbours")[1])
        self.assertEqual(run("--string", BASE, "--no-same-neighbours")[0], 2)

    def test_formats_and_pipes(self):
        board = generate("KMQXRT")
        for flag, fmt in (("s", "s"), ("sections", "s"), ("p", "p"), ("paired", "p")):
            for pipes in (False, True):
                args = ["--seed", "KMQXRT", "--format", flag] + ([] if pipes else ["--no-pipes"])
                code, out, _ = run(*args)
                self.assertEqual(code, 0)
                self.assertEqual(out.split("string: ")[1].strip(), serialize(board, fmt, pipes))

    def test_ports_are_added_with_the_flag_and_not_otherwise(self):
        self.assertEqual(len(run("--seed", "KMQXRT", "--no-pipes")[1].split("string: ")[1].strip()), 37)
        with_ports = run("--seed", "KMQXRT", "--ports", "--no-pipes")[1]
        self.assertTrue(with_ports.split("string: ")[1].strip().endswith("XO3Gws3#c3"))
        self.assertIn("seed:   KMQXRT-P\n", with_ports)

    def test_the_printed_seed_is_the_full_seed_code(self):
        self.assertIn("seed:   KMQXRT-EP\n", run("--seed", "KMQXRT", "--desert", "edge", "--ports")[1])
        self.assertIn("seed:   KMQXRT-RAP\n", run("--seed", "KMQXRT", "--desert", "ring", "--allow-adjacent-red", "--ports")[1])

    def test_the_flags_in_the_seed_code_do_what_the_options_do(self):
        a = run("--seed", "KMQXRT-EP")
        b = run("--seed", "KMQXRT", "--desert", "edge", "--ports")
        self.assertEqual(a, b)
        self.assertEqual(run("--seed", "kmqxrt-pe"), a)       # the order and the case of the flags do not matter

    def test_the_desert_options(self):
        for zone in ("edge", "inner", "center", "ring"):
            board = parse(run("--seed", "KMQXRT", "--desert", zone)[1].split("string: ")[1].strip()).board
            self.assertEqual(board, generate("KMQXRT", desert=zone))

    def test_an_option_may_add_but_not_change(self):
        code, out, err = run("--seed", "KMQXRT-E", "--desert", "inner")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("error:", err)
        self.assertIn("seed code says the desert is on the edge (E)", err)
        self.assertIn("inner", err)
        self.assertEqual(run("--seed", "KMQXRT-E", "--desert", "edge")[0], 0)
        self.assertEqual(run("--seed", "KMQXRT-E", "--desert", "free")[0], 2)
        self.assertEqual(run("--seed", "KMQXRT", "--desert", "free")[0], 0)

    def test_bad_seeds(self):
        for seed in ("KM2XRT", "", "KMQXRT-EI", "KMQXRT-Z", "a" * 33):
            code, out, err = run("--seed", seed)
            self.assertEqual((code, out), (2, ""), seed)
            self.assertTrue(err.startswith("error:"), seed)


class ReadingAString(unittest.TestCase):
    def test_either_layout_to_either_layout(self):
        paired = serialize(parse(BASE).board, "p")
        for given in (BASE, paired, serialize(parse(BASE).board, "s", True)):
            self.assertEqual(run("--string", given, "--format", "p", "--no-pipes")[1], f"string: {paired}\n")
            self.assertEqual(run("--string", given, "--format", "s", "--no-pipes")[1], f"string: {BASE}\n")
            self.assertEqual(run("--string", given, "--no-pipes")[1], f"string: {paired}\n")      # paired is the default

    def test_a_string_with_ports_keeps_them(self):
        text = BASE + "X3gO3s#3cW"
        self.assertEqual(run("--string", text, "--format", "s", "--no-pipes")[1], f"string: {text}\n")
        self.assertEqual(run("--string", text, "--format", "s")[1], f"string: {serialize(parse(text).board, 's', True, True)}\n")

    def test_the_ports_flag_adds_the_default_ports(self):
        self.assertEqual(run("--string", BASE, "--ports", "--format", "s", "--no-pipes")[1], f"string: {BASE}3gO3s#3cW\n")

    def test_no_seed_line_when_reading(self):
        self.assertNotIn("seed:", run("--string", BASE)[1])

    def test_a_bad_string_is_an_error_naming_the_character(self):
        code, out, err = run("--string", BASE[:19] + "Z" + BASE[20:])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("character 20", err)

    def test_touching_reds_warn_on_stderr_and_still_succeed(self):
        tokens = list(parse(BASE).board.tokens)
        tokens[2], tokens[6] = tokens[6], tokens[2]
        from catan_map.codec import Board
        text = serialize(Board(parse(BASE).board.tiles, tuple(tokens)), "s")
        code, out, err = run("--string", text, "--format", "s", "--no-pipes")
        self.assertEqual(code, 0)
        self.assertIn("string: " + text, out)
        self.assertIn("warning: the 6 at row 1, column 2 touches the 8 at row 1, column 3\n", err)

    def test_seed_options_do_not_apply_to_a_string(self):
        for option in (["--desert", "edge"], ["--allow-adjacent-red"]):
            code, out, err = run("--string", BASE, *option)
            self.assertEqual((code, out), (2, ""))
            self.assertIn("only apply when a board is made from a seed", err)

    def test_a_seed_and_a_string_together_is_a_usage_error(self):
        code, _, err = run("--seed", "KMQXRT", "--string", BASE)
        self.assertEqual(code, 2)
        self.assertIn("not allowed with", err)


class Drawing(unittest.TestCase):
    def test_the_board_is_drawn_under_the_string(self):
        code, out, _ = run("--seed", "KMQXRT", "--board", "--format", "s", "--no-pipes")
        self.assertEqual(code, 0)
        self.assertIn("string: CGGWSWWCODGCGOSSOSW58ab94ca33645298b6\n\n", out)
        self.assertIn("↘", out)
        # only the drawing: no heading and no list of ports under it
        self.assertNotIn("ports", out)
        self.assertNotIn("-> tile", out)
        self.assertEqual(len(out.rstrip("\n").split("\n")), 2 + 1 + 7)    # seed, string, a blank line, 7 rows

    def test_ascii(self):
        out = run("--seed", "KMQXRT", "--board", "--ascii")[1]
        self.assertTrue(out.isascii())
        self.assertIn("3\\", out)

    def test_colour(self):
        plain = run("--seed", "KMQXRT", "--board")[1]
        coloured = run("--seed", "KMQXRT", "--board", "--color")[1]
        self.assertIn("\x1b[", coloured)
        self.assertEqual(ANSI.sub("", coloured), plain)

    def test_a_string_can_be_drawn_too(self):
        out = run("--string", BASE + "3gO3s#3cW", "--board")[1]
        self.assertIn("W5", out)
        self.assertNotIn("ports", out)
        self.assertEqual(len(out.rstrip("\n").split("\n")), 1 + 1 + 7)    # string, a blank line, 7 rows


class AsAProgram(unittest.TestCase):
    def call(self, *args, env=None):
        full = dict(os.environ, **(env or {}))
        full["PYTHONPATH"] = str(ROOT)
        return subprocess.run([sys.executable, "-m", "catan_map", *args], capture_output=True, text=True, cwd=ROOT, env=full)

    def test_python_dash_m_works(self):
        done = self.call("--seed", "KMQXRT", "--format", "s", "--no-pipes")
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout, "seed:   KMQXRT\nstring: CGGWSWWCODGCGOSSOSW58ab94ca33645298b6\n")

    def test_a_bad_input_exits_with_code_two(self):
        done = self.call("--seed", "KM2XRT")
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stdout, "")
        self.assertIn("error:", done.stderr)

    def test_a_console_that_cannot_show_arrows_gets_the_ascii_drawing(self):
        done = self.call("--seed", "KMQXRT", "--board", env={"PYTHONIOENCODING": "ascii"})
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(done.stdout.isascii())
        self.assertIn("3\\", done.stdout)

    def run_file(self, *args, cwd):
        """Python started on a file or folder, with the package NOT on the path (so only the
        file's own location can make the imports work)."""
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        return subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=cwd, env=env)

    def test_it_runs_when_started_as_a_file_or_a_folder(self):
        expected = "seed:   KMQXRT\nstring: CGGWSWWCODGCGOSSOSW58ab94ca33645298b6\n"
        elsewhere = tempfile.gettempdir()
        starts = [
            (["catan_map/cli.py"], ROOT),                                    # python catan_map/cli.py
            ([str(ROOT / "catan_map" / "cli.py")], elsewhere),               # the same, from another folder
            ([str(ROOT / "catan_map" / "__main__.py")], elsewhere),
            ([str(ROOT / "catan_map")], elsewhere),                          # python path/to/catan_map
        ]
        for command, cwd in starts:
            done = self.run_file(*command, "--seed", "KMQXRT", "--format", "s", "--no-pipes", cwd=cwd)
            self.assertEqual((done.returncode, done.stdout, done.stderr), (0, expected, ""), command)

    def test_started_as_a_file_help_and_errors_still_work(self):
        done = self.run_file("catan_map/cli.py", "-h", cwd=ROOT)
        self.assertEqual(done.returncode, 0)
        self.assertIn("--seed", done.stdout)
        done = self.run_file("catan_map/cli.py", "--seed", "KM2XRT", cwd=ROOT)
        self.assertEqual((done.returncode, done.stdout), (2, ""))
        self.assertIn("error:", done.stderr)
        done = self.run_file("catan_map/cli.py", "--string", "WSG", cwd=ROOT)
        self.assertEqual(done.returncode, 2)

    def test_help_mentions_the_options(self):
        done = self.call("--help")
        self.assertEqual(done.returncode, 0)
        for word in ("--seed", "--string", "--format", "--no-pipes", "--ports", "--board", "--color", "--ascii", "--desert", "--allow-adjacent-red"):
            self.assertIn(word, done.stdout)


if __name__ == "__main__":
    unittest.main()
