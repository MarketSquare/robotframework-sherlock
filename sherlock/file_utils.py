from pathlib import Path
from functools import lru_cache
from typing import Iterable, Iterator, Optional, List, Tuple

from pathspec import PathSpec

INCLUDE_EXT = frozenset({".robot", ".resource", ".py"})
INIT_EXT = ("__init__.robot", "__init__.py")


@lru_cache()
def get_gitignore(root: Path) -> PathSpec:
    """Return a PathSpec matching gitignore content if present."""
    gitignore = root / ".gitignore"
    lines: List[str] = []
    if gitignore.is_file():
        with gitignore.open(encoding="utf-8") as gf:
            lines = gf.readlines()
    return PathSpec.from_lines("gitwildmatch", lines)


def find_project_root(paths) -> Path:
    """Return a directory containing .git or pyproject.toml.
    That directory will be a common parent of all files and directories
    passed in `paths`.
    If no directory in the tree contains a marker that would specify it's the
    project root, the root of the file system is returned.
    """
    if paths is None:
        return Path.cwd()

    path_srcs = [Path(Path.cwd(), path).resolve() for path in paths]

    # A list of lists of parents for each 'path'. 'path' is included as a
    # "parent" of itself if it is a directory
    src_parents = [list(path.parents) + ([path] if path.is_dir() else []) for path in path_srcs]

    common_base = max(
        set.intersection(*(set(parents) for parents in src_parents)),
        key=lambda path: path.parts,
    )

    for directory in (common_base, *common_base.parents):
        if (directory / ".git").exists() or (directory / "pyproject.toml").is_file():
            return directory
    return directory


def find_file_in_project_root(config_name, root):
    for parent in (root, *root.parents):
        if (parent / ".git").exists() or (parent / config_name).is_file():
            return parent / config_name
    return parent / config_name
