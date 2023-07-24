from pathlib import Path
import io
import sys
import tempfile
import os
import contextlib
from unittest.mock import patch

import pytest

from sherlock.config import TomlConfigParser, Config
from sherlock.exceptions import SherlockFatalError


@pytest.fixture
def path_to_test_data():
    return Path(__file__).parent.parent / "test_data"


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

    def test_load_args_from_cli_overwrite_config(self, path_to_test_data):
        config_dir = path_to_test_data / "configs" / "pyproject"
        with tempfile.NamedTemporaryFile() as fp, working_directory(config_dir), patch.object(
            sys, "argv", f"sherlock --output {fp.name} {config_dir}".split()
        ):
            config = Config()
            assert config.path == Path(config_dir)
            assert config.output == Path(fp.name)
            assert isinstance(config.log_output, io.TextIOWrapper)
            assert config.report == ["print", "html"]

    def test_load_args_from_cli_config_option(self, path_to_test_data, tmp_path):
        config_dir = path_to_test_data / "configs" / "pyproject"
        with working_directory(config_dir), patch.object(
            sys, "argv", f"sherlock --config pyproject_other.toml {tmp_path}".split()
        ):
            config = Config()
            assert config.path == Path(tmp_path)
            assert config.log_output is None
            assert config.report == ["print"]

    def test_load_args_from_config_missing_file(self, tmp_path):
        with patch.object(sys, "argv", f"sherlock --config idontexist.toml {tmp_path}".split()), pytest.raises(
            SherlockFatalError
        ) as err:
            Config()
        assert "Configuration file 'idontexist.toml' does not exist" in str(err)


class TestTomlParser:
    def test_read_toml_data(self, path_to_test_data):
        config_path = path_to_test_data / "configs" / "pyproject" / "pyproject.toml"
        config = TomlConfigParser(config_path=config_path, look_up={}).read_from_file()
        assert config and isinstance(config, dict)

    def test_read_toml_data_empty_pyproject(self, path_to_test_data):
        config_path = path_to_test_data / "configs" / "empty_pyproject" / "pyproject.toml"
        config = TomlConfigParser(config_path=config_path, look_up={}).read_from_file()
        assert not config and isinstance(config, dict)

    def test_read_toml_data_no_sherlock_section(self, path_to_test_data):
        config_path = path_to_test_data / "configs" / "no_sherlock_section_pyproject" / "pyproject.toml"
        config = TomlConfigParser(config_path=config_path, look_up={}).read_from_file()
        assert not config and isinstance(config, dict)

    def test_get_config(self, path_to_test_data):
        config_path = path_to_test_data / "configs" / "pyproject" / "pyproject.toml"
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

    def test_get_config_empty(self, path_to_test_data):
        config_path = path_to_test_data / "configs" / "empty_pyproject" / "pyproject.toml"
        look_up = Config(from_cli=False).__dict__
        config = TomlConfigParser(config_path=config_path, look_up=look_up).get_config()
        assert not config and isinstance(config, dict)

    def test_get_config_missing_key(self, path_to_test_data):
        config_path = path_to_test_data / "configs" / "pyproject_missing_key" / "pyproject.toml"
        look_up = Config(from_cli=False).__dict__
        with pytest.raises(SherlockFatalError) as err:
            TomlConfigParser(config_path=config_path, look_up=look_up).get_config()
        assert "Option 'some_key' is not supported in configuration file" in str(err)

    def test_get_config_nested_configuration(self, path_to_test_data):
        config_path = path_to_test_data / "configs" / "pyproject_nested_config" / "pyproject.toml"
        look_up = Config(from_cli=False).__dict__
        with pytest.raises(SherlockFatalError) as err:
            TomlConfigParser(config_path=config_path, look_up=look_up).get_config()
        assert "Nesting configuration files is not allowed" in str(err)

    def test_get_config_invalid_toml(self, path_to_test_data):
        config_path = path_to_test_data / "configs" / "pyproject_invalid" / "pyproject.toml"
        look_up = Config(from_cli=False).__dict__
        with pytest.raises(SherlockFatalError) as err:
            TomlConfigParser(config_path=config_path, look_up=look_up).get_config()
        assert (
            rf"Failed to decode {config_path}: This float doesn't have a leading digit (line 3 column 1 char 38)"
            in err.value.args[0]
        )
