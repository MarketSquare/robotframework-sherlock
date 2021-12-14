import ast
import os
from pathlib import Path

from robot.api import get_resource_model
from robot.running.arguments import EmbeddedArguments
from robot.running.testlibraries import TestLibrary
from robot.utils import NormalizedDict


class KeywordStats:
    def __init__(self, name, node=None):
        self.name = name
        self.used = 0
        self.node = node

    def __str__(self):
        return f"{self.name} | Used: {self.used}\n"


class ResourceVisitor(ast.NodeVisitor):
    def __init__(self):
        self.normal_keywords = NormalizedDict(ignore='_')
        self.embedded_keywords = dict()
        self.resources = set()
        self.libraries = dict()

    def visit_Keyword(self, node):  # noqa
        embedded = EmbeddedArguments(node.name)
        if embedded:
            self.embedded_keywords[node.name] = (KeywordStats(node.name, node=node), embedded.name)
        else:
            self.normal_keywords[node.name] = KeywordStats(node.name, node=node)  # TODO: handle duplications

    def visit_ResourceImport(self, node):  # noqa
        if node.name:
            self.resources.add(node.name)

    def visit_LibraryImport(self, node):  # noqa
        # TODO aliases
        if node.name:
            self.libraries[node.name] = node.args


class KeywordStore:
    def __init__(self, normal, embedded):
        self._normal = normal
        self._embedded = embedded

    def __iter__(self):
        yield from self._normal.values()
        for kw_stat, pattern in self._embedded.values():
            yield kw_stat

    def find_kw(self, kw_name):
        found = []
        try:
            kw_stat = self._normal[kw_name]
            found.append(kw_stat)
        except KeyError:
            for name, (kw_stat, template) in self._embedded.items():
                if self.match_embedded(kw_name, template):
                    found.append(kw_stat)
        return found

    @staticmethod
    def match_embedded(name, pattern):
        raise NotImplemented


class KeywordLibraryStore(KeywordStore):
    def __init__(self, test_library):
        normal = NormalizedDict(ignore='_')
        for kw in test_library.handlers._normal:
            normal[kw] = KeywordStats(kw)
        embedded = {handler.name: (KeywordStats(handler.name, handler)) for handler in test_library.handlers._embedded}
        super().__init__(normal, embedded)

    @staticmethod
    def match_embedded(name, pattern):
        return pattern.matches(name)


class KeywordResourceStore(KeywordStore):
    def __init__(self, normal, embedded):
        keyword_stats = {name: KeywordStats(name) for name in normal.values()}
        for kw_stat, pattern in embedded.values():
            keyword_stats[kw_stat.name] = kw_stat
        super().__init__(normal, embedded)

    @staticmethod
    def match_embedded(name, pattern):
        return pattern.match(name)


class Library:
    def __init__(self, path):
        self.path = path
        self.keywords = None
        self.loaded = False
        self.filter_not_used = False

    def load_library(self, args=None):
        if self.keywords:
            return
        # TODO handle exceptions (not enough args etc)
        name = str(self.path)
        library = TestLibrary(name, args)
        self.keywords = KeywordLibraryStore(library)

    def search(self, name, *args):
        if not self.keywords:
            return  # TODO lib not init
        return self.keywords.find_kw(name)

    def __str__(self):
        s = f"Library: {self.path}\n"
        if self.keywords:
            s += f"  Keywords:\n"
            for kw in self.keywords:
                if self.filter_not_used and not kw.used:
                    continue
                s += "    " + str(kw)
        return s


class Resource:
    def __init__(self, path: Path):
        self.path = str(path)
        self.directory = str(path.parent)
        self.resources = dict()
        self.imports = set()
        self.libraries = dict()

        model = get_resource_model(str(path), data_only=True, curdir=str(path.cwd()))
        visitor = ResourceVisitor()
        visitor.visit(model)
        self.keywords = KeywordResourceStore(visitor.normal_keywords, visitor.embedded_keywords)
        # set them from --variables and such
        variables = {'${/}': os.path.sep}
        for resource in visitor.resources:
            for var, value in variables.items():
                resource = resource.replace(var, value)
            self.imports.add(str(Path(self.directory, resource).resolve()))
        for library, args in visitor.libraries.items():
            for var, value in variables.items():
                library = library.replace(var, value)
            self.libraries[str(Path(self.directory, library).resolve())] = args

    def search(self, name, resources):
        found = resources["BuiltIn"].search(name, resources)
        if found:
            return found
        found += self.keywords.find_kw(name)
        for imported in self.imports:
            if imported in resources:
                found += resources[imported].search(name, resources)
        for lib, args in self.libraries.items():
            if lib in resources:
                resources[lib].load_library(args)
                found += resources[lib].search(name, resources)
        return found

    def __str__(self):
        s = f"File: {self.path}\n"
        if self.keywords:
            s += f"  Keywords:\n"
            for kw in self.keywords:
                s += "    " + str(kw)
        return s