import contextlib
import os
from pathlib import Path

import pytest

from sherlock.file_utils import find_file_in_project_root, find_project_root, get_gitignore

TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"


@contextlib.contextmanager
def working_directory(path):
    """Changes working directory and returns to previous on exit"""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


class TestFileUtils:
    def test_find_project_root(self):
        source = TEST_DATA_DIR / "configs" / "pyproject"
        root = find_project_root((source,))
        assert root == source

    def test_find_project_root_without_sources(self):
        source = TEST_DATA_DIR / "configs" / "pyproject"
        with working_directory(source):
            root = find_project_root(None)
            assert root == source

    def test_find_project_root_multiple_sources(self):
        common = TEST_DATA_DIR / "configs" / "nested_pyproject"
        sources = (common / "1" / "2" / "test.robot", common / "2")
        root = find_project_root(sources)
        assert root == common

    def test_find_project_root_no_pyproject(self):
        source = Path.home()
        root = find_project_root((source,))
        assert root == Path(source.parts[0])

    def test_find_file_in_project_root(self):
        source = TEST_DATA_DIR / "configs" / "nested_pyproject" / "2"
        file = find_file_in_project_root("pyproject.toml", source)
        assert file == source / "pyproject.toml"

    def test_find_file_in_project_root_no_file(self):
        source = TEST_DATA_DIR / "configs" / "no_pyproject"
        file = find_file_in_project_root("pyproject.toml", source)
        # if file is not found it will find it in parents - in this case top of the repository
        assert file == TEST_DATA_DIR.parent.parent / "pyproject.toml"

    def test_find_file_in_project_root_outside_repo(self):
        source = Path.home()
        file = find_file_in_project_root("pyproject.toml", source)
        # if file is not found anywhere, it will return Path({root}:/{file})
        assert file == Path(source.parts[0]) / "pyproject.toml"

    def test_get_gitignore(self):
        gitignore = TEST_DATA_DIR / "gitignore"
        spec = get_gitignore(gitignore)
        assert spec.match_file("file.resource")
        assert not spec.match_file("file.robot")
