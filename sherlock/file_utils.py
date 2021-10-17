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


def get_paths(src: Tuple[str, ...]):
    sources = set()
    for s in src:
        path = Path(s).resolve()
        gitignore = get_gitignore(path)
        sources.update(iterate_dir((path,), gitignore))
    return sources


def iterate_dir(paths: Iterable[Path], gitignore: Optional[PathSpec]) -> Iterator[Path]:
    for path in paths:
        if gitignore is not None and gitignore.match_file(path):
            continue
        if path.is_dir():
            yield from iterate_dir(path.iterdir(), gitignore)
        elif path.is_file():
            if path.suffix not in INCLUDE_EXT:
                continue
            yield path


class ResultTree:
    def __init__(self, path, gitignore=None):
        if gitignore is None:
            gitignore = get_gitignore(path)
        self.path = path
        self.children = []
        for child in path.iterdir():
            if gitignore is not None and gitignore.match_file(f"{child}/" if child.is_dir() else str(child)):
                continue
            if child.is_dir():
                self.children.append(ResultTree(child, gitignore))
            elif child.is_file():
                if child.suffix not in INCLUDE_EXT:
                    continue
                self.children.append(child)

    def __str__(self):
        return str(self.path)
