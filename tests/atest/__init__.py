import json
import subprocess
from pathlib import Path

from sherlock.config import Config, _process_pythonpath
from sherlock.core import Sherlock


def run_sherlock(robot_output, source, report=None, resource=None, pythonpath=None):
    config = Config(from_cli=False)
    config.output = robot_output
    config.path = source
    if report is not None:
        config.report = report
    if resource is not None:
        config.resource = resource
    if pythonpath is not None:
        config.pythonpath = _process_pythonpath([pythonpath])
    config.validate_test_path()

    sherlock = Sherlock(config=config)
    sherlock.run()  # TODO create special report readable by tests?
    return sherlock


def get_output(output):
    with open(output) as f:
        data = json.load(f)
    Path(output).unlink()
    return data


def sort_by_name(collection):
    return sorted(collection, key=lambda x: x["name"])


def match_tree(expected, actual):
    if expected["name"] != actual["name"]:
        print(f"Expected name '{expected['name']}' does not match actual name '{actual['name']}'")
        return False

    if "keywords" in expected:
        if len(expected["keywords"]) != len(actual["keywords"]):
            print(
                f"Expected number of keywords in {expected['name']}: {len(expected['keywords'])} "
                f"does not match actual: {len(actual['keywords'])}"
            )
            return False
        expected["keywords"] = sort_by_name(expected["keywords"])
        actual["keywords"] = sort_by_name(actual["keywords"])
        for exp_keyword, act_keyword in zip(expected["keywords"], actual["keywords"]):
            if "used" not in exp_keyword:
                act_keyword.pop("used", None)
            if "complexity" not in exp_keyword:
                act_keyword.pop("complexity", None)
            if "status" not in exp_keyword:
                act_keyword.pop("status", None)
            if exp_keyword != act_keyword:
                return False

    if "children" in expected:
        if len(expected["children"]) != len(actual["children"]):
            print(
                f"Expected length of children tree: {len(expected['children'])} "
                f"does not match actual: {len(actual['children'])}"
            )
            return False
        expected["children"] = sort_by_name(expected["children"])
        actual["children"] = sort_by_name(actual["children"])
        if not all(
            match_tree(exp_child, act_child) for exp_child, act_child in zip(expected["children"], actual["children"])
        ):
            return False

    if "type" in expected:
        if expected["type"] != actual["type"]:
            print(f"Resource type does not match: {expected['type']} != {actual['type']}")
            return False
    return True


class Tree:
    def __init__(self, name, keywords=None, children=None, res_type=None):
        self.name = name
        self.keywords = keywords
        self.children = children
        self.res_type = res_type

    def to_json(self):
        ret = {"name": self.name}
        if self.keywords is not None:
            ret["keywords"] = [kw.to_json() for kw in self.keywords]
        if self.children is not None:
            ret["children"] = [child.to_json() for child in self.children]
        if self.res_type is not None:
            ret["type"] = self.res_type
        return ret

    def __str__(self):
        return str(self.to_json())


class Keyword:
    def __init__(self, name, used=None, complexity=None):
        self.name = name
        self.used = used
        self.complexity = complexity

    def to_json(self):
        ret = {"name": self.name}
        if self.used is not None:
            ret["used"] = self.used
        if self.complexity is not None:
            ret["complexity"] = self.complexity
        return ret


class AcceptanceTest:
    ROOT = Path()
    TEST_PATH = "test.robot"

    def run_robot(self, pythonpath=None):
        source = self.ROOT / self.TEST_PATH
        cmd = f"robot --outputdir {self.ROOT}"
        if pythonpath:
            cmd += f" --pythonpath {pythonpath}"
        cmd += f" {source}"
        subprocess.run(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def run_sherlock(self, source=None, resource=None, report=None, pythonpath=None, run_robot=True):
        if report is None:
            report = ["json"]
        if run_robot:
            self.run_robot(pythonpath)
            robot_output = self.ROOT / "output.xml"
        else:
            robot_output = None
        if source:
            source = source if source.is_dir() else source.parent
        else:
            source = self.ROOT
        run_sherlock(robot_output=robot_output, source=source, report=report, resource=resource, pythonpath=pythonpath)
        data = get_output(f"sherlock_{source.name}.json")
        return data

    @staticmethod
    def should_match_tree(expected_tree, actual):
        expected = expected_tree.to_json()
        assert match_tree(expected, actual)
