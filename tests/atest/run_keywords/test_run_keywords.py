from pathlib import Path

from tests.atest import AcceptanceTest, Keyword, Tree


class TestRunKeywords(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"

    def test(self):
        data = self.run_sherlock()
        expected = Tree(
            name="test_data",
            children=[
                Tree(
                    name="test.robot",
                    keywords=[
                        Keyword(name="Keyword 1", used=4),
                        Keyword(name="Keyword 2", used=1),
                        Keyword(name="Keyword 3", used=1),
                    ],
                ),
            ],
        )
        self.should_match_tree(expected, data)
