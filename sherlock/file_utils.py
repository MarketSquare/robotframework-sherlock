from pathlib import Path
from functools import lru_cache
from typing import Iterable, Iterator, Optional, List, Tuple

from pathspec import PathSpec

INCLUDE_EXT = frozenset({".robot", ".resource", ".py"})


@lru_cache()
def get_gitignore(root: Path) -> PathSpec:
    """Return a PathSpec matching gitignore content if present."""
    gitignore = root / ".gitignore"
    lines: List[str] = []
    if gitignore.is_file():
        with gitignore.open(encoding="utf-8") as gf:
            lines = gf.readlines()
    return PathSpec.from_lines("gitwildmatch", lines)
