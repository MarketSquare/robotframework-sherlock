from pathlib import Path

from tests.atest import AcceptanceTest, Keyword, Tree


class TestImportWithVariable(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"
    TEST_PATH = "tests"

    def test(self):
        data = self.run_sherlock()
        expected = Tree(
            name="test_data",
            children=[
                Tree(
                    name="tests",
                    children=[
                        Tree(name="a.resource", keywords=[]),
                        Tree(
                            name="b.resource",
                            keywords=[Keyword(name="Internal Keyword", used=0), Keyword(name="Keyword 1", used=1)],
                        ),
                        Tree(
                            name="c.resource",
                            keywords=[Keyword(name="Internal Keyword", used=1), Keyword(name="Keyword 1", used=1)],
                        ),
                        Tree(name="test_a.robot", keywords=[Keyword(name="Internal Keyword", used=1)]),
                        Tree(name="test_b.robot", keywords=[]),
                    ],
                )
            ],
        )
        self.should_match_tree(expected, data)
