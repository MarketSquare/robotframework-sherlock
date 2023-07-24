from pathlib import Path

from tests.atest import AcceptanceTest, Keyword, Tree


class TestSuiteSetups(AcceptanceTest):
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
                        Tree(
                            name="resource.robot",
                            keywords=[Keyword(name="Other Keyword", used=6), Keyword(name="Suite Keyword", used=2)],
                        ),
                        Tree(name="tests.robot", keywords=[Keyword(name="Internal Keyword", used=1)]),
                        Tree(name="__init__.robot", keywords=[Keyword(name="Suite Keyword", used=2)]),
                    ],
                )
            ],
        )
        self.should_match_tree(expected, data)
