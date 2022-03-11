from pathlib import Path

from .. import run_sherlock, AcceptanceTest


class TestComplicatedStructure(AcceptanceTest):
    ROOT = Path(Path(__file__).parent, "test_data")
    TEST_PATH = "tests"

    def test(self):
        run_sherlock(robot_output=self.ROOT / "output.xml", source=self.ROOT, report=["html"])
