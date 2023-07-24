from pathlib import Path

from tests.atest import run_sherlock, AcceptanceTest


class TestComplicatedStructure(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"
    TEST_PATH = "tests"

    def test(self):
        self.run_robot()
        run_sherlock(robot_output=self.ROOT / "output.xml", source=self.ROOT, report=["html"])
