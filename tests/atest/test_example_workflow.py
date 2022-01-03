from pathlib import Path
import subprocess

import pytest

from . import run_sherlock


@pytest.fixture(scope="class")
def path_to_test_data():
    return Path(Path(__file__).parent.parent, "test_data")


@pytest.fixture(scope="class")
def run_with_tests():
    return "tests"


class TestExampleWorkflow:
    def test_with_xml_output(self, path_to_test_data):
        robot_output = path_to_test_data / "output.xml"
        source = path_to_test_data / "tests"
        run_sherlock(robot_output=robot_output, source=source)

    def test_without_xml_output(self, path_to_test_data):
        source = path_to_test_data / "tests"
        run_sherlock(robot_output=None, source=source)

    def test_with_html_report(self, path_to_test_data):
        robot_output = path_to_test_data / "output.xml"
        source = path_to_test_data / "tests"
        run_sherlock(robot_output=robot_output, source=source, report=["html"])

    def test_with_json_report(self, path_to_test_data):
        robot_output = path_to_test_data / "output.xml"
        source = path_to_test_data / "tests"
        run_sherlock(robot_output=robot_output, source=source, report=["json"])
