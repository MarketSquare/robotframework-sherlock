from pathlib import Path

from .. import Tree, Keyword, AcceptanceTest


class TestKeywordInResAndSuite(AcceptanceTest):
    ROOT = Path(Path(__file__).parent, "test_data")

    def test(self):
        data = self.run_sherlock()
        expected = Tree(
            name="test_data",
            children=[
                Tree(name="kw.resource", keywords=[Keyword(name="Ambiguous Name", used=1)]),
                Tree(name="test.robot", keywords=[Keyword(name="Ambiguous Name", used=1)]),
            ],
        )
        self.should_match_tree(expected, data)
