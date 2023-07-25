import contextlib
import io
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sherlock.config import Config, TomlConfigParser
from sherlock.exceptions import SherlockFatalError

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


class TestConfig:
    def test_load_args_from_cli(self, tmp_path):
        with tempfile.NamedTemporaryFile() as fp, patch.object(
            sys,
            "argv",
            f"sherlock --output {fp.name} --log-output sherlock.log --report html {tmp_path}".split(),
        ):
            config = Config()
            assert config.path == Path(tmp_path)
            assert config.output == Path(fp.name)
            assert isinstance(config.log_output, io.TextIOWrapper)
            assert config.report == ["html"]

    def test_load_args_from_cli_no_pyproject(self, tmp_path):
        with tempfile.NamedTemporaryFile() as fp, working_directory(Path.home()), patch.object(
            sys,
            "argv",
            f"sherlock --output {fp.name} --log-output sherlock.log --report html {tmp_path}".split(),
        ):
            config = Config()
            assert config.path == Path(tmp_path)
            assert config.output == Path(fp.name)
            assert isinstance(config.log_output, io.TextIOWrapper)
            assert config.report == ["html"]

    def test_load_args_from_cli_overwrite_config(self):
        config_dir = TEST_DATA_DIR / "configs" / "pyproject"
        with tempfile.NamedTemporaryFile() as fp, working_directory(config_dir), patch.object(
            sys, "argv", f"sherlock --output {fp.name} {config_dir}".split()
        ):
            config = Config()
            assert config.path == Path(config_dir)
            assert config.output == Path(fp.name)
            assert isinstance(config.log_output, io.TextIOWrapper)
            assert config.report == ["print", "html"]

    def test_load_args_from_cli_config_option(self, tmp_path):
        config_dir = TEST_DATA_DIR / "configs" / "pyproject"
        cmd = f"sherlock --config pyproject_other.toml {tmp_path}".split()
        with working_directory(config_dir), patch.object(sys, "argv", cmd):
            config = Config()
            assert config.path == Path(tmp_path)
            assert config.log_output is None
            assert config.report == ["print"]

    def test_load_args_from_config_missing_file(self, tmp_path):
        cmd = f"sherlock --config idontexist.toml {tmp_path}".split()
        with patch.object(sys, "argv", cmd), pytest.raises(SherlockFatalError) as err:
            Config()
        assert "Configuration file 'idontexist.toml' does not exist" in str(err)

    @pytest.mark.parametrize(
        "python_path, exp_python_path",
        [
            (".", [str(Path.cwd())]),
            (f".;{Path('test_libraries')}", [str(Path.cwd()), str(Path.cwd() / "test_libraries")]),
        ],
    )
    def test_pythonpath(self, tmp_path, python_path, exp_python_path):
        cmd = f"sherlock --pythonpath {python_path} {tmp_path}".split()
        with patch.object(sys, "argv", cmd):
            config = Config()
            assert sorted(exp_python_path) == sorted(config.pythonpath)


class TestTomlParser:
    def test_read_toml_data(self):
        config_path = TEST_DATA_DIR / "configs" / "pyproject" / "pyproject.toml"
        config = TomlConfigParser(config_path=config_path, look_up={}).read_from_file()
        assert config and isinstance(config, dict)

    def test_read_toml_data_empty_pyproject(self):
        config_path = TEST_DATA_DIR / "configs" / "empty_pyproject" / "pyproject.toml"
        config = TomlConfigParser(config_path=config_path, look_up={}).read_from_file()
        assert not config and isinstance(config, dict)

    def test_read_toml_data_no_sherlock_section(self):
        config_path = TEST_DATA_DIR / "configs" / "no_sherlock_section_pyproject" / "pyproject.toml"
        config = TomlConfigParser(config_path=config_path, look_up={}).read_from_file()
        assert not config and isinstance(config, dict)

    def test_get_config(self):
        config_path = TEST_DATA_DIR / "configs" / "pyproject" / "pyproject.toml"
        look_up = Config(from_cli=False).__dict__
        config = TomlConfigParser(config_path=config_path, look_up=look_up).get_config()
        assert isinstance(config["log_output"], io.TextIOWrapper)
        config["log_output"] = None
        assert config == {
            "output": Path("output.xml"),
            "log_output": None,
            "report": ["print", "html"],
            "path": ["file1.robot", "dir/"],
            "variable": ["first:value", "second:value"],
        }

    def test_get_config_empty(self):
        config_path = TEST_DATA_DIR / "configs" / "empty_pyproject" / "pyproject.toml"
        look_up = Config(from_cli=False).__dict__
        config = TomlConfigParser(config_path=config_path, look_up=look_up).get_config()
        assert not config and isinstance(config, dict)

    def test_get_config_missing_key(self):
        config_path = TEST_DATA_DIR / "configs" / "pyproject_missing_key" / "pyproject.toml"
        look_up = Config(from_cli=False).__dict__
        with pytest.raises(SherlockFatalError) as err:
            TomlConfigParser(config_path=config_path, look_up=look_up).get_config()
        assert "Option 'some_key' is not supported in configuration file" in str(err)

    def test_get_config_nested_configuration(self):
        config_path = TEST_DATA_DIR / "configs" / "pyproject_nested_config" / "pyproject.toml"
        look_up = Config(from_cli=False).__dict__
        with pytest.raises(SherlockFatalError) as err:
            TomlConfigParser(config_path=config_path, look_up=look_up).get_config()
        assert "Nesting configuration files is not allowed" in str(err)

    def test_get_config_invalid_toml(self):
        config_path = TEST_DATA_DIR / "configs" / "pyproject_invalid" / "pyproject.toml"
        look_up = Config(from_cli=False).__dict__
        with pytest.raises(SherlockFatalError) as err:
            TomlConfigParser(config_path=config_path, look_up=look_up).get_config()
        assert (
            rf"Failed to decode {config_path}: This float doesn't have a leading digit (line 3 column 1 char 38)"
            in err.value.args[0]
        )

    def test_get_config_python_path(self):
        config_path = TEST_DATA_DIR / "configs" / "pyproject_pythonpath" / "pyproject.toml"
        look_up = Config(from_cli=False).__dict__
        config = TomlConfigParser(config_path=config_path, look_up=look_up).get_config()
        assert config == {"pythonpath": [str(Path.cwd() / "test_libs")], "report": ["html"]}
