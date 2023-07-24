from pathlib import Path

import pytest

from . import AcceptanceTest, run_sherlock


class TestExampleWorkflow(AcceptanceTest):
    ROOT = Path(__file__).parent.parent / "test_data"
    TEST_PATH = "tests"

    def test_with_xml_output(self):
        robot_output = self.ROOT / "output.xml"
        source = self.ROOT / self.TEST_PATH
        self.run_robot()
        run_sherlock(robot_output=robot_output, source=source)

    def test_without_xml_output(self):
        source = self.ROOT / self.TEST_PATH
        run_sherlock(robot_output=None, source=source)

    @pytest.mark.parametrize("report_type", ["json", "html"])
    def test_with_report(self, report_type):
        robot_output = self.ROOT / "output.xml"
        source = self.ROOT / self.TEST_PATH
        self.run_robot()
        runner = run_sherlock(robot_output=robot_output, source=source, report=[report_type])
        output = runner.config.root / f"sherlock_tests.{report_type}"
        assert output.is_file()
        output.unlink()
