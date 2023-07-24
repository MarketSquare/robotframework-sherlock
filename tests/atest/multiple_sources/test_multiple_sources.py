from pathlib import Path

from tests.atest import AcceptanceTest, Keyword, Tree


class TestMultipleSources(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"

    # def test_two_sources(self, path_to_test_data):
    #     robot_output = path_to_test_data / "output.xml"
    #     source1 = path_to_test_data / "resource1"
    #     source2 = path_to_test_data / "resource2"  # TODO
    #     run_sherlock(robot_output=robot_output, source=[source1, source2], report=["json"])

    def test_single_source(self):
        source = self.ROOT / "resource1"
        data = self.run_sherlock(source=source)
        # TODO used 0 since it doesn't know it was used by test.robot
        expected = Tree(
            name="resource1",
            children=[Tree(name="file.resource", keywords=[Keyword(name="Keyword 1", used=0, complexity=1)])],
        )
        self.should_match_tree(expected, data)
