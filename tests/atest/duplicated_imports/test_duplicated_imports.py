from pathlib import Path

import pytest

from tests.atest import AcceptanceTest, Keyword, Tree


class TestDuplicatedImports(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"

    @pytest.mark.parametrize("run_robot", [True, False])
    def test(self, run_robot):
        data = self.run_sherlock(run_robot=run_robot)
        expected = Tree(
            name="test_data",
            children=[
                Tree(name="test.resource", keywords=[Keyword(name="Keyword 1", used=2, complexity=1)]),
                Tree(name="test.robot", keywords=[]),
            ],
        )
        self.should_match_tree(expected, data)
