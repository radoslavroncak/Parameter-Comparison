#!/usr/bin/env python3
import argparse
from pathlib import Path


def parse_parameters(file_path: Path) -> dict[str, str]:
    parameters: dict[str, str] = {}
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key, value = line.split("=", 1)
        elif ":" in line:
            key, value = line.split(":", 1)
        elif " " in line:
            key, value = line.split(None, 1)
        else:
            key, value = line, ""

        parameters[key.strip()] = value.strip()
    return parameters


def compare_parameters(first: dict[str, str], second: dict[str, str]) -> str:
    first_keys = set(first)
    second_keys = set(second)

    only_first = sorted(first_keys - second_keys)
    only_second = sorted(second_keys - first_keys)
    common = sorted(first_keys & second_keys)
    changed = [key for key in common if first[key] != second[key]]

    lines: list[str] = []
    lines.append("Iba v prvom subore:")
    lines.extend(f"  - {key}={first[key]}" for key in only_first)
    if not only_first:
        lines.append("  (ziadne)")

    lines.append("")
    lines.append("Iba v druhom subore:")
    lines.extend(f"  - {key}={second[key]}" for key in only_second)
    if not only_second:
        lines.append("  (ziadne)")

    lines.append("")
    lines.append("Rozdielne hodnoty:")
    lines.extend(
        f"  - {key}: '{first[key]}' vs '{second[key]}'" for key in changed
    )
    if not changed:
        lines.append("  (ziadne)")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Porovna parametre z dvoch TXT suborov."
    )
    parser.add_argument("first_file", type=Path, help="Cesta k prvemu TXT suboru")
    parser.add_argument("second_file", type=Path, help="Cesta k druhemu TXT suboru")
    args = parser.parse_args()

    first_params = parse_parameters(args.first_file)
    second_params = parse_parameters(args.second_file)
    print(compare_parameters(first_params, second_params))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
