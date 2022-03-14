from pathlib import Path

from .. import Tree, Keyword, AcceptanceTest


class TestDictVariables(AcceptanceTest):
    ROOT = Path(Path(__file__).parent, "test_data")

    def test(self):
        data = self.run_sherlock()
        expected = Tree(
            name="test_data",
            res_type="Directory",
            children=[
                Tree(
                    name="test.robot", res_type="Resource", keywords=[Keyword(name="Keyword 1", used=1, complexity=1)]
                ),
            ],
        )
        self.should_match_tree(expected, data)
