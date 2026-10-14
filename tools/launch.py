"""Source launch with explicit installation root; no ambient AppData dependency."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

from hugin.__main__ import main

if __name__ == '__main__':
    raise SystemExit(main())
