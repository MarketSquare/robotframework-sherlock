from pathlib import Path

from .. import Tree, Keyword, AcceptanceTest


class TestDuplicatedImports(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"

    def test(self):
        data = self.run_sherlock()
        expected = Tree(
            name="test_data",
            children=[
                Tree(name="test.resource", keywords=[Keyword(name="Keyword 1", used=2, complexity=1)]),
                Tree(name="test.robot", keywords=[]),
            ],
        )
        self.should_match_tree(expected, data)
