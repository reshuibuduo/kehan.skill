#!/usr/bin/env python3
"""Build a deterministic .skill ZIP from the self-contained skill directory."""
import argparse
import hashlib
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'dong-kehan'

def build(output):
    paths = sorted(p for p in SKILL.rglob('*') if p.is_file()
                   and '__pycache__' not in p.parts and p.name != '.DS_Store')
    if not (SKILL / 'SKILL.md').is_file():
        raise ValueError('SKILL.md missing')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w') as archive:
        for path in paths:
            if path.is_symlink():
                raise ValueError('Package files must not be symlinks')
            info = zipfile.ZipInfo('dong-kehan/' + path.relative_to(SKILL).as_posix(),
                                   date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes())
    return len(paths)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'dist/kehan.skill')
    args = parser.parse_args()
    count = build(args.output)
    print(f'PACKAGE PASS: {count} files; sha256={hashlib.sha256(args.output.read_bytes()).hexdigest()}')

if __name__ == '__main__':
    main()
