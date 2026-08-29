import os
from pathlib import Path


TEXT_EXTENSIONS = {
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

SKIP_PARTS = {
    ".git",
    "__pycache__",
    "node_modules",
    "S-111",
    "tiles",
    "geollm_results",
    "logs",
    "dist",
}

SKIP_TEXT_FILE_PREFIXES = (
    "backend_log",
    "docker_log",
    "dis_",
    "response",
)


def should_check(path: Path, relative_path: Path) -> bool:
    if path.suffix.lower() == ".txt" and "scratch" in relative_path.parts:
        return False
    if path.suffix.lower() == ".txt" and path.name.startswith(SKIP_TEXT_FILE_PREFIXES):
        return False
    return (
        path.is_file()
        and path.suffix.lower() in TEXT_EXTENSIONS
        and not SKIP_PARTS.intersection(relative_path.parts)
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures: list[tuple[Path, str]] = []

    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [dirname for dirname in dirnames if dirname not in SKIP_PARTS]
        current_path = Path(current_root)

        for filename in filenames:
            path = current_path / filename
            relative_path = path.relative_to(root)
            if not should_check(path, relative_path):
                continue
            try:
                path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                failures.append((relative_path, str(exc)))

    if failures:
        print("Non-UTF-8 text files found:")
        for path, error in failures:
            print(f"- {path}: {error}")
        return 1

    print("All checked text files are valid UTF-8.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
