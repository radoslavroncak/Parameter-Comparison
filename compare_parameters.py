#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass
class Block:
    name: str
    block_type: str = "UNKNOWN"
    params: Dict[str, str] = field(default_factory=dict)


def read_lines(path: Path) -> List[str]:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = data.decode("utf-16")
    else:
        for encoding in ("utf-8-sig", "cp1250", "latin1"):
            try:
                text = data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = data.decode("latin1", errors="replace")
    return text.splitlines()


def detect_format(lines: Iterable[str]) -> str:
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("NAME"):
            return "block"
        if "." in line.split("=", 1)[0]:
            return "flat"
    return "block"


def parse_block_lines(lines: Iterable[str]) -> List[Block]:
    blocks: List[Block] = []
    current: Block | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if line == "END":
            if current:
                blocks.append(current)
                current = None
            continue

        if "=" not in line:
            continue

        left, right = line.split("=", 1)
        key = left.strip()
        value = right.strip()

        if key == "NAME":
            if current:
                blocks.append(current)
            current = Block(name=value)
            continue

        if current is None:
            continue

        if key == "TYPE":
            current.block_type = value or "UNKNOWN"
        else:
            current.params[key] = value

    if current:
        blocks.append(current)

    return blocks


def parse_flat_lines(lines: Iterable[str]) -> List[Block]:
    by_prefix: Dict[str, Block] = {}

    for raw_line in lines:
        line = raw_line.strip().lstrip("\ufeff")
        if not line or "=" not in line:
            continue

        left, right = line.split("=", 1)
        key_path = left.strip()
        value = right.strip()

        if "." not in key_path:
            continue

        prefix, key = key_path.rsplit(".", 1)
        block = by_prefix.setdefault(prefix, Block(name=prefix))

        if key == "NAME":
            block.name = value or prefix
        elif key == "TYPE":
            block.block_type = value or "UNKNOWN"
        else:
            block.params[key] = value

    merged: Dict[str, Block] = {}
    for prefix, block in by_prefix.items():
        target = merged.setdefault(block.name, Block(name=block.name))
        if target.block_type == "UNKNOWN" and block.block_type != "UNKNOWN":
            target.block_type = block.block_type
        target.params.update(block.params)
        if target.name == prefix and block.name != prefix:
            target.name = block.name

    return list(merged.values())


def parse_file(path: Path) -> List[Block]:
    lines = read_lines(path)
    if detect_format(lines) == "flat":
        return parse_flat_lines(lines)
    return parse_block_lines(lines)


def index_by_name(blocks: Iterable[Block]) -> Dict[str, Block]:
    return {block.name: block for block in blocks}


def index_by_type(blocks: Iterable[Block]) -> Dict[str, List[Block]]:
    grouped: Dict[str, List[Block]] = defaultdict(list)
    for block in blocks:
        grouped[block.block_type].append(block)
    return grouped


def compare_blocks(first: List[Block], second: List[Block]) -> List[str]:
    report: List[str] = []
    by_name_1 = index_by_name(first)
    by_name_2 = index_by_name(second)

    only_1 = sorted(set(by_name_1) - set(by_name_2))
    only_2 = sorted(set(by_name_2) - set(by_name_1))

    if only_1:
        report.append("Bloky len v subore 1:")
        report.extend(f"  - {name}" for name in only_1)
    if only_2:
        report.append("Bloky len v subore 2:")
        report.extend(f"  - {name}" for name in only_2)

    common = sorted(set(by_name_1) & set(by_name_2))
    for name in common:
        b1 = by_name_1[name]
        b2 = by_name_2[name]

        if b1.block_type != b2.block_type:
            report.append(
                f"Typ sa lisi pre {name}: subor1={b1.block_type}, subor2={b2.block_type}"
            )

        keys = sorted(set(b1.params) | set(b2.params))
        block_diffs = []
        for key in keys:
            v1 = b1.params.get(key, "<CHYBA>")
            v2 = b2.params.get(key, "<CHYBA>")
            if v1 != v2:
                block_diffs.append(f"    {key}: '{v1}' != '{v2}'")

        if block_diffs:
            report.append(f"Rozdiely v bloku {name} (TYPE={b1.block_type}):")
            report.extend(block_diffs)

    if not report:
        report.append("Subory su z hladiska parametrov rovnake.")

    return report


def write_split_files(blocks: List[Block], output_dir: Path, source_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    grouped = index_by_type(blocks)

    for block_type in sorted(grouped):
        safe_type = re.sub(r"[^A-Za-z0-9_.-]+", "_", block_type)
        path = output_dir / f"{source_name}.{safe_type}.txt"
        lines: List[str] = []
        for block in sorted(grouped[block_type], key=lambda item: item.name):
            lines.append(f"NAME   = {block.name}")
            lines.append(f"  TYPE   = {block.block_type}")
            for key, value in sorted(block.params.items()):
                lines.append(f"  {key:<6} = {value}")
            lines.append("END")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Porovna dva textove subory s parametrami. "
            "Podporuje blokovy format (NAME/TYPE/.../END) aj plochy format NAME.PARAM=..."
        )
    )
    parser.add_argument("subor1", type=Path)
    parser.add_argument("subor2", type=Path)
    parser.add_argument(
        "--split-output-dir",
        type=Path,
        help="Volitelne: vytvori podsubory podla TYPE pre oba vstupy.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    blocks_1 = parse_file(args.subor1)
    blocks_2 = parse_file(args.subor2)

    if args.split_output_dir:
        write_split_files(blocks_1, args.split_output_dir, args.subor1.stem)
        write_split_files(blocks_2, args.split_output_dir, args.subor2.stem)

    for line in compare_blocks(blocks_1, blocks_2):
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
