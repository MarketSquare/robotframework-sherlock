from pathlib import Path

from tests.atest import AcceptanceTest, Keyword, Tree


class TestPythonPath(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"

    def test(self):
        cwd = Path(__file__).parent / "test_data" / "nested"
        data = self.run_sherlock(pythonpath=str(cwd))
        expected = Tree(
            name="test_data",
            children=[
                Tree(
                    name="nested",
                    res_type="Directory",
                    children=[Tree(name="Library", keywords=[Keyword(name="Keyword 1", used=1)])],
                ),
                Tree(name="test.robot", keywords=[]),
            ],
        )
        self.should_match_tree(expected, data)
