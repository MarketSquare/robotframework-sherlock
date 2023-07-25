from pathlib import Path

from tests.atest import AcceptanceTest, Keyword, Tree, get_output


class TestExternalImport(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data" / "tests"

    def test(self):
        ext_libs_path = str(Path(__file__).parent / "test_data" / "ext_libs")
        data = self.run_sherlock(resource=[ext_libs_path])
        expected = Tree(
            name="tests",
            children=[Tree(name="test.robot", keywords=[])],
        )
        self.should_match_tree(expected, data)
        external_data = get_output("sherlock_ext_libs.json")
        external_expected = Tree(
            name="ext_libs", children=[Tree(name="Library", keywords=[Keyword(name="Keyword 1", used=1)])]
        )
        self.should_match_tree(external_expected, external_data)
