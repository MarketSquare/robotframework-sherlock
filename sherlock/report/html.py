from itertools import chain
from pathlib import Path

from jinja2 import Template

from sherlock.model import DIRECTORY_TYPE, RESOURCE_TYPE, LIBRARY_TYPE, SUITE_TYPE, KeywordTimings
from sherlock.file_utils import INIT_EXT


class KeywordResult:
    def __init__(self, element_id, name, used, complexity, status, timings):
        self.element_id = element_id
        self.name = name
        self.used = used
        self.complexity = complexity
        self.status = status
        self.timings = timings


class HtmlResultModel:
    def __init__(self, element_id, model):
        self.element_id = element_id
        self.type = model.get_type().upper()
        self.name = model.name
        self.path = model.path
        self.show = "BuiltIn" not in self.name
        self.children = []
        self.keywords = []
        self.timings = KeywordTimings()
        self.errors = model.errors
        self.fill_keywords(model)
        self.fill_children(model)

    @property
    def status(self):
        status = "label"
        for child in chain(self.keywords, self.children):
            if child.status in ("skip", "fail"):
                return child.status
            if child.status == "pass":
                status = "pass"
        if self.type == SUITE_TYPE.upper() and not self.keywords:
            return "pass"
        return status

    def fill_keywords(self, model):
        if model.type not in (RESOURCE_TYPE, LIBRARY_TYPE, SUITE_TYPE) or not model.keywords:
            return
        for index, kw in enumerate(model.keywords):
            self.timings += kw.timings
            new_id = f"{self.element_id}-k{index}"
            self.keywords.append(
                KeywordResult(
                    element_id=new_id,
                    name=kw.name,
                    used=kw.used,
                    complexity=kw.complexity,
                    status=kw.status,
                    timings=kw.timings,
                )
            )

    @staticmethod
    def get_children_with_init_first(model):
        children = [child for child in model.children]
        for index, child in enumerate(children):
            if child.name in INIT_EXT:
                yield children.pop(index)
        for child in children:
            yield child

    def fill_children(self, model):
        if model.type != DIRECTORY_TYPE:
            return
        for index, child in enumerate(self.get_children_with_init_first(model)):
            new_id = f"{self.element_id}-r{index}"
            model = HtmlResultModel(new_id, child)
            self.timings += model.timings
            self.children.append(model)


def html_report(directory, name, output_dir):
    result = HtmlResultModel("d0", directory)
    with open(Path(__file__).parent / "html.template") as f:
        template = Template(f.read()).render(tree=[result])
    with open(output_dir / f"sherlock_{name}.html", "w") as f:
        f.write(template)
