from pathlib import Path

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

    @pytest.mark.parametrize("report_type", ["json", "html"])
    def test_with_report(self, path_to_test_data, report_type):
        robot_output = path_to_test_data / "output.xml"
        source = path_to_test_data / "tests"
        runner = run_sherlock(robot_output=robot_output, source=source, report=[report_type])
        output = runner.config.root / f"sherlock_tests.{report_type}"
        assert output.is_file()
        output.unlink()
