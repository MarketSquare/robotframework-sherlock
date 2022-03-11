from pathlib import Path

from .. import Tree, Keyword, AcceptanceTest


class TestVeryLongAndShortName(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"

    def test(self):
        data = self.run_sherlock()
        # TODO assert
