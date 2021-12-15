from pathlib import Path

from jinja2 import Template


class KeywordResult:
    def __init__(self, element_id, name, used, complexity, status):
        self.element_id = element_id
        self.name = name
        self.used = used
        self.complexity = complexity
        self.status = status


class HtmlResultModel:
    def __init__(self, element_id, model):
        self.element_id = element_id
        self.type = model.type.upper()
        self.name = model.path.name if isinstance(model.path, Path) else str(model.path)
        self.path = str(model.path)
        self.show = "BuiltIn" not in self.name
        self.children = []
        self.keywords = []
        self.status = "pass"
        self.fill_keywords(model)
        self.fill_children(model)

    def fill_keywords(self, model):
        if model.type not in ("Resource", "Library"):  # TODO make constant
            return
        for index, kw in enumerate(model.keywords):
            new_id = f"{self.element_id}-k{index}"
            self.keywords.append(
                KeywordResult(element_id=new_id, name=kw.name, used=kw.used, complexity=kw.complexity, status="pass")
            )

    def fill_children(self, model):
        if model.type != "Directory":
            return
        for index, child in enumerate(model.children):
            new_id = f"{self.element_id}-r{index}"
            self.children.append(HtmlResultModel(new_id, child))


def html_report(directory, output_dir):
    result = HtmlResultModel("d0", directory)
    with open(Path(__file__).parent / "html.template") as f:
        template = Template(f.read()).render(tree=[result])
    with open(output_dir / "sherlock.html", "w") as f:
        f.write(template)
