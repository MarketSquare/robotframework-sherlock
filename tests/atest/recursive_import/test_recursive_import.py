from pathlib import Path

from tests.atest import AcceptanceTest, Keyword, Tree


class TestRecursiveImport(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"
    TEST_PATH = ""

    def test(self):
        data = self.run_sherlock()
        expected = Tree(
            name="test_data",
            children=[
                Tree(name="base.resource", res_type="Resource", keywords=[]),
                Tree(
                    name="Library",
                    res_type="Library",
                    keywords=[
                        Keyword(name="My Keyword", used=1),
                        Keyword(name="Not Used", used=0),
                        Keyword(name="Third Keyword", used=2),
                    ],
                ),
                Tree(
                    name="Library2",
                    res_type="Library",
                    keywords=[
                        Keyword(name="Keyword From Lib2", used=0),
                    ],
                ),
                Tree(
                    name="sub_resource.resource",
                    res_type="Resource",
                    keywords=[Keyword(name="Sub resource keyword", used=0)],
                ),
                Tree(name="suite.robot", keywords=[]),
            ],
        )
        self.should_match_tree(expected, data)
