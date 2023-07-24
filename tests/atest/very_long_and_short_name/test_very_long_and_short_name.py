from pathlib import Path

from tests.atest import AcceptanceTest, Keyword, Tree


class TestVeryLongAndShortName(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"

    def test(self):
        data = self.run_sherlock()
        # TODO assert
