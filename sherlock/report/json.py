import json


def directory_to_json(directory):
    ret = {
        "path": str(directory.path),
        "type": directory.type
    }
    if directory.type == "Directory":  # TODO Directory can have keywords (__init__.py)
        ret["children"] = [
            directory_to_json(resource) for resource in directory.children
        ]
    else:
        ret["keywords"] = [{
            "name": kw.name,
            "used": kw.used,
            "complexity": kw.complexity,
            "status": "pass"  # TODO
        } for kw in directory.keywords
        ]
    return ret


def json_report(directory, output_dir):
    ret = directory_to_json(directory)
    with open(output_dir / "sherlock.json", "w") as f:
        json.dump(ret, f, indent=4)
