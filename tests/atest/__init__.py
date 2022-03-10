import json
from pathlib import Path

from sherlock.config import Config
from sherlock.core import Sherlock


def run_sherlock(robot_output, source, report=None, resource=None):
    config = Config(from_cli=False)
    config.output = robot_output
    config.path = source
    if report is not None:
        config.report = report
    if resource is not None:
        config.resource = resource

    sherlock = Sherlock(config=config)
    sherlock.run()  # TODO create special report readable by tests?
    return sherlock


def get_output(output):
    with open(output) as f:
        data = json.load(f)
    Path(output).unlink()
    return data


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
        if not all(
            match_tree(exp_child, act_child) for exp_child, act_child in zip(expected["children"], actual["children"])
        ):
            return False
    return True


class Tree:
    def __init__(self, name, keywords=None, children=None):
        self.name = name
        self.keywords = keywords
        self.children = children

    def to_json(self):
        ret = {"name": self.name}
        if self.keywords is not None:
            ret["keywords"] = [kw.to_json() for kw in self.keywords]
        if self.children is not None:
            ret["children"] = [child.to_json() for child in self.children]
        return ret


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
