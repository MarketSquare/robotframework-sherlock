import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import sherlock.config
from sherlock.config import Config
from sherlock.core import Sherlock
from sherlock.exceptions import SherlockFatalError


class TestCli:
    def test_invalid_output(self, tmp_path):
        with patch.object(
            sys,
            "argv",
            f"sherlock --output idontexist.xml --report html {tmp_path}".split(),
        ), pytest.raises(
            SherlockFatalError, match="Reading Robot Framework output file failed. No such file: 'idontexist.xml'"
        ):
            Config()

    def test_no_output(self, tmp_path):
        with patch.object(
            sys,
            "argv",
            f"sherlock --report html {tmp_path}".split(),
        ):
            Config()

    def test_output(self):
        with tempfile.NamedTemporaryFile() as fp, patch.object(
            sys,
            "argv",
            f"sherlock --output {fp.name} .".split(),
        ):
            config = Config()
            assert config.output == Path(fp.name)

    def test_default_output(self):
        with tempfile.NamedTemporaryFile() as fp, patch.object(
            sherlock.config, "ROBOT_DEFAULT_OUTPUT", fp.name
        ), patch.object(
            sys,
            "argv",
            f"sherlock {Path(fp.name).parent}".split(),
        ):
            config = Config()
            assert config.output == config.path / fp.name

    def test_default_source(self):
        with patch.object(sys, "argv", ["sherlock"]):
            config = Config()
            assert config.path == Path.cwd()

    def test_invalid_source(self):
        full_invalid_path = Path("idontexist").resolve()
        with patch.object(sys, "argv", ["sherlock", "idontexist"]), pytest.raises(SherlockFatalError) as err:
            Config()
        assert f"Path to source code does not exist: '{full_invalid_path}'" in str(err.value)

    def test_invalid_report(self):
        with patch.object(sys, "argv", "sherlock --report print,invalid".split(),), pytest.raises(
            SherlockFatalError,
            match="Provided report 'invalid' does not exist. Use comma separated list of values from: html,json,print",
        ):
            Sherlock()

    def test_invalid_report_similar(self):
        with patch.object(sys, "argv", "sherlock --report printt".split(),), pytest.raises(
            SherlockFatalError,
            match="Provided report 'printt' does not exist. Use comma separated list of values from: html,json,print. "
            "Did you mean:\n    print",
        ):
            Sherlock()

    def test_default_report(self):
        with patch.object(sys, "argv", "sherlock".split()):
            config = Config()
            assert config.report == ["print"]
