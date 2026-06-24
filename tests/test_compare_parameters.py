import tempfile
import unittest
from pathlib import Path

from compare_parameters import compare_blocks, parse_block_lines, parse_flat_lines, parse_file


class CompareParametersTests(unittest.TestCase):
    def test_parse_block_lines(self):
        blocks = parse_block_lines(
            [
                "NAME   = A:BLOCK1",
                "  TYPE   = AIN",
                "  P1     = 10",
                "END",
            ]
        )
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].name, "A:BLOCK1")
        self.assertEqual(blocks[0].block_type, "AIN")
        self.assertEqual(blocks[0].params["P1"], "10")

    def test_parse_flat_lines(self):
        blocks = parse_flat_lines(
            [
                "A:BLOCK1.NAME = A:BLOCK1",
                "A:BLOCK1.TYPE = AIN",
                "A:BLOCK1.P1 = 10",
            ]
        )
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].name, "A:BLOCK1")
        self.assertEqual(blocks[0].block_type, "AIN")
        self.assertEqual(blocks[0].params["P1"], "10")

    def test_compare_detects_parameter_difference(self):
        first = parse_block_lines(["NAME=A", "TYPE=AIN", "P1=10", "END"])
        second = parse_block_lines(["NAME=A", "TYPE=AIN", "P1=11", "END"])
        report = compare_blocks(first, second)
        self.assertTrue(any("P1" in line for line in report))

    def test_parse_file_autodetects_utf16_flat_format(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.txt"
            path.write_text(
                "A:BLOCK1.NAME = A:BLOCK1\nA:BLOCK1.TYPE = AIN\nA:BLOCK1.P1 = 10\n",
                encoding="utf-16",
            )
            blocks = parse_file(path)
            self.assertEqual(blocks[0].name, "A:BLOCK1")
            self.assertEqual(blocks[0].block_type, "AIN")


if __name__ == "__main__":
    unittest.main()
