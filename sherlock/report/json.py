import json

import sherlock.report
from sherlock.model import DIRECTORY_TYPE


def directory_to_json(directory):
    ret = {"name": str(directory.name), "type": directory.type}
    if directory.type == DIRECTORY_TYPE:  # TODO Directory can have keywords (__init__.py)
        ret["children"] = [directory_to_json(resource) for resource in directory.children]
    else:
        if directory.keywords is None:
            ret["keywords"] = []
        else:
            ret["keywords"] = [
                {"name": kw.name, "used": kw.used, "complexity": kw.complexity, "status": "pass"}  # TODO
                for kw in directory.keywords
            ]
    return ret


class JsonReport(sherlock.report.Report):
    name: str = "json"
    description: str = "JSON report"

    def get_report(self, tree, tree_name, path_root):
        ret = directory_to_json(tree)
        with open(path_root / f"sherlock_{tree_name}.json", "w") as f:
            json.dump(ret, f, indent=4)
