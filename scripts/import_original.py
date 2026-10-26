#!/usr/bin/env python3
"""Import a user-owned archive into ignored local-original, without unpacking or uploading it."""
from pathlib import Path
import argparse
import hashlib
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Local game archive (.sit, .zip, .hqx, .bin)")
    args = parser.parse_args()
    src = args.source.expanduser().resolve()
    if not src.is_file() or src.suffix.lower() not in {".sit", ".zip", ".hqx", ".bin"}:
        parser.error("Provide a local .sit/.zip/.hqx/.bin file")
    dest_dir = ROOT / "local-original"
    dest_dir.mkdir(exist_ok=True)
    dest = dest_dir / src.name
    if src == dest:
        print("Archive already in", dest)
    else:
        if dest.exists():
            parser.error(f"Refusing to overwrite {dest}")
        shutil.copy2(src, dest)
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    print(f"Local archive: {dest}\nSize: {dest.stat().st_size} bytes\nSHA256: {digest}")
    print("No game files were uploaded, decoded or redistributed.")
if __name__ == "__main__":
    sys.exit(main())
