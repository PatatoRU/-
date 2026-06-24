from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SECRET_PATTERNS = {
    "openai_api_key": re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "telegram_bot_token": re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b"),
}
ALLOWED_FILES = {".env.example"}
LOCAL_SECRET_GLOBS = [".env", ".env.*", "docker-compose.override.yml"]


def tracked_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files"], text=True)
    return [Path(line) for line in output.splitlines() if line]


def local_secret_files() -> list[Path]:
    files: set[Path] = set()
    for pattern in LOCAL_SECRET_GLOBS:
        files.update(path for path in Path(".").glob(pattern) if path.is_file())
    return sorted(files)


def scan_paths(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        if path.name in ALLOWED_FILES or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                findings.append(f"{path}: possible {name}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan project files for leaked credentials.")
    parser.add_argument("--include-local", action="store_true", help="also scan local .env-style files")
    args = parser.parse_args()
    paths = tracked_files()
    if args.include_local:
        paths.extend(local_secret_files())
    findings = scan_paths(paths)
    if findings:
        print("Security check failed:")
        print("\n".join(findings))
        return 1
    scope = "tracked and local secret files" if args.include_local else "tracked files"
    print(f"Security check passed: no secrets found in {scope}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
