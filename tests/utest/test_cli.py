import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import sherlock.config
from sherlock.config import Config
from sherlock.exceptions import SherlockFatalError


class TestCli:
    def test_invalid_output_path(self):
        with patch.object(
            sys,
            "argv",
            "sherlock --output-path idontexist.xml --report html path/to/directory".split(),
        ), pytest.raises(
            SherlockFatalError, match="Reading Robot Framework output file failed. No such file: 'idontexist.xml'"
        ):
            Config()

    def test_no_output_path(self):
        with patch.object(
            sys,
            "argv",
            "sherlock --report html path/to/directory".split(),
        ):
            Config()

    def test_output_path(self):
        with tempfile.NamedTemporaryFile() as fp, patch.object(
            sys,
            "argv",
            f"sherlock --output-path {fp.name} .".split(),
        ):
            config = Config()
            assert config.output_path == Path(fp.name)

    def test_default_output_path(self):
        with tempfile.NamedTemporaryFile() as fp, patch.object(
            sherlock.config, "ROBOT_DEFAULT_OUTPUT", fp.name
        ), patch.object(
            sys,
            "argv",
            f"sherlock {Path(fp.name).parent}".split(),
        ):
            config = Config()
            assert config.output_path == config.path / fp.name

    def test_default_source(self):
        with patch.object(
            sys,
            "argv",
            ["sherlock"],
        ):
            config = Config()
            assert config.path == Path.cwd()

    def test_invalid_report(self):
        with patch.object(
            sys,
            "argv",
            "sherlock --report print,invalid".split(),
        ), pytest.raises(
            SherlockFatalError, match="Report 'invalid' not recognized. Use comma separated list of values from: print, html, json"
        ):
            Config()

    def test_default_report(self):
        with patch.object(
            sys,
            "argv",
            "sherlock".split(),
        ):
            config = Config()
            assert config.report == ["print"]
