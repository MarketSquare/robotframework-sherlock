from pathlib import Path

from tests.atest import AcceptanceTest, Keyword, Tree


class TestDuplicatedNamesDotted(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"

    def test(self):
        data = self.run_sherlock()
        expected = Tree(
            name="test_data",
            children=[
                Tree(name="Library1", keywords=[Keyword(name="Keyword 1", used=2)]),
                Tree(name="Library2", keywords=[Keyword(name="Keyword 1", used=1)]),
                Tree(name="test.resource", keywords=[Keyword(name="Keyword 1", used=21, complexity=1)]),
                Tree(name="test.robot", keywords=[]),
            ],
        )
        self.should_match_tree(expected, data)
