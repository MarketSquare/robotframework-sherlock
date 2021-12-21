from pathlib import Path
import subprocess

import pytest

from . import run_sherlock


@pytest.fixture(scope="class")
def path_to_test_data():
    return Path(Path(__file__).parent.parent, "test_data")


class TestExampleWorkflow:
    @pytest.fixture(scope="class", autouse=True)
    def generate_robot_output(self, path_to_test_data):
        source = path_to_test_data / "tests"
        subprocess.run(f"robot --outputdir {path_to_test_data} {source}", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        yield
        for path in (path_to_test_data / "log.html", path_to_test_data / "output.xml", path_to_test_data / "report.html"):
            path.unlink(missing_ok=True)

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
