from pathlib import Path

from jinja2 import Template

from sherlock.model import DIRECTORY_TYPE, RESOURCE_TYPE, LIBRARY_TYPE, KeywordTimings


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
        self.type = model.type.upper()
        self.name = model.name
        self.path = model.path
        self.show = "BuiltIn" not in self.name
        self.children = []
        self.keywords = []
        self.timings = None
        self.status = "pass"
        self.fill_keywords(model)
        self.fill_children(model)

    def fill_keywords(self, model):
        if model.type not in (RESOURCE_TYPE, LIBRARY_TYPE):
            return
        self.timings = KeywordTimings()
        for index, kw in enumerate(model.keywords):
            self.timings += kw.timings
            new_id = f"{self.element_id}-k{index}"
            self.keywords.append(
                KeywordResult(
                    element_id=new_id,
                    name=kw.name,
                    used=kw.used,
                    complexity=kw.complexity,
                    status="pass",
                    timings=kw.timings,
                )
            )

    def fill_children(self, model):
        if model.type != DIRECTORY_TYPE:
            return
        for index, child in enumerate(model.children):
            new_id = f"{self.element_id}-r{index}"
            self.children.append(HtmlResultModel(new_id, child))


def html_report(directory, name, output_dir):
    result = HtmlResultModel("d0", directory)
    with open(Path(__file__).parent / "html.template") as f:
        template = Template(f.read()).render(tree=[result])
    with open(output_dir / f"sherlock_{name}.html", "w") as f:
        f.write(template)
