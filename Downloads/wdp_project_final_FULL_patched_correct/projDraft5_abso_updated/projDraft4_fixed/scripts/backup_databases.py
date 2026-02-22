from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup local SQLite databases.")
    parser.add_argument("--source", default="instance", help="Folder containing .db files")
    parser.add_argument("--dest", default="backups", help="Destination folder for backups")
    args = parser.parse_args()

    source_dir = Path(args.source).resolve()
    dest_root = Path(args.dest).resolve()
    if not source_dir.exists():
        raise SystemExit(f"Source folder not found: {source_dir}")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_dir = dest_root / f"backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    db_files = sorted(source_dir.glob("*.db"))
    if not db_files:
        raise SystemExit(f"No .db files found in {source_dir}")

    for db_file in db_files:
        shutil.copy2(db_file, backup_dir / db_file.name)

    print(f"Backed up {len(db_files)} database files to: {backup_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
