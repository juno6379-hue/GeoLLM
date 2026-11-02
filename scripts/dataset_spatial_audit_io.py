"""Shared output policy for read-only Dataset spatial audits."""
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def output_argument(default=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=default or ROOT/'outputs/dataset_location_audit_20261102/spatial')
    return parser.parse_args().output

def refuse_existing(path):
    path=Path(path)
    if path.exists():
        raise FileExistsError(f'Audit evidence already exists: {path}. Use --output with a new directory; overwrite/resume is not implicit.')
    path.parent.mkdir(parents=True,exist_ok=True)
    return path
