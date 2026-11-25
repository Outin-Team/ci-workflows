#!/usr/bin/env python3
"""Synchronize or verify scripts/ci_hub_client.py embedded inside reusable workflows."""

from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB_PATH = ROOT / "scripts" / "ci_hub_client.py"
WORKFLOWS = [
    ROOT / ".github" / "workflows" / "reusable-build-and-gate.yml",
    ROOT / ".github" / "workflows" / "reusable-deploy-approved.yml",
]

START_MARKER = "# <<< BEGIN EMBEDDED ci_hub_client.py >>>"
END_MARKER = "# <<< END EMBEDDED ci_hub_client.py >>>"


def render_embedded_block(source: str, indent: str) -> str:
    indented = "\n".join((indent + line) if line else "" for line in source.rstrip("\n").splitlines())
    return f"{indent}{START_MARKER}\n{indented}\n{indent}{END_MARKER}"


def sync_file(wf_path: pathlib.Path, source: str, check_only: bool) -> bool:
    text = wf_path.read_text(encoding="utf-8")
    start_idx = text.find(START_MARKER)
    end_idx = text.find(END_MARKER)
    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        raise RuntimeError(f"Markers not found in {wf_path}")

    line_start = text.rfind("\n", 0, start_idx) + 1
    indent = text[line_start:start_idx]
    end_line_end = text.find("\n", end_idx)
    if end_line_end == -1:
        end_line_end = len(text)

    expected_block = render_embedded_block(source, indent)
    new_text = text[:line_start] + expected_block + text[end_line_end:]
    if new_text == text:
        return True
    if check_only:
        print(f"[ERROR] Embedded script drift detected in {wf_path.relative_to(ROOT)}", file=sys.stderr)
        return False
    wf_path.write_text(new_text, encoding="utf-8")
    print(f"[SYNCED] {wf_path.relative_to(ROOT)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = LIB_PATH.read_text(encoding="utf-8")
    ok = True
    for wf in WORKFLOWS:
        if not sync_file(wf, source, check_only=args.check):
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
