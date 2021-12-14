import ast
import os
import textwrap
from pathlib import Path

from robot.api import get_resource_model
from robot.running.arguments import EmbeddedArguments
from robot.running.testlibraries import TestLibrary
from robot.utils import NormalizedDict

from sherlock.complexity import ComplexityChecker
from sherlock.file_utils import get_gitignore, INCLUDE_EXT


class KeywordStats:
    def __init__(self, name, node=None):
        self.name = name
        self.used = 0
        self.node = node
        self.complexity = self.get_complexity()

    def __str__(self):
        s = f"{self.name} | Used: {self.used}"
        if self.complexity:
            s += f" | Complexity: {self.complexity}"
        return s + "\n"

    def get_complexity(self):
        if not self.node:
            return None
        checker = ComplexityChecker()
        checker.visit(self.node)
        return checker.complexity()


class ResourceVisitor(ast.NodeVisitor):
    def __init__(self):
        self.normal_keywords = NormalizedDict(ignore="_")
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
        normal = NormalizedDict(ignore="_")
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
        self.type = "Library"
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

    def get_resources(self):
        return str(self.path), self

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
        self.type = "Resource"
        self.path = path
        self.directory = str(path.parent)
        self.resources = dict()
        self.imports = set()
        self.libraries = dict()

        model = get_resource_model(str(path), data_only=True, curdir=str(path.cwd()))
        visitor = ResourceVisitor()
        visitor.visit(model)
        self.keywords = KeywordResourceStore(visitor.normal_keywords, visitor.embedded_keywords)
        # set them from --variables and such
        variables = {"${/}": os.path.sep}
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

    def get_resources(self):
        return str(self.path), self

    def __str__(self):
        s = f"File: {self.path}\n"
        if self.keywords:
            s += f"  Keywords:\n"
            for kw in self.keywords:
                s += "    " + str(kw)
        return s


class Directory:
    def __init__(self, path, gitignore=None):
        self.type = "Directory"
        self.path = path
        self.children = []
        self.get_childs(gitignore)
        # TODO handle __init__.robot here

    @classmethod
    def root(cls, path):
        path = Path(path).resolve()
        gitignore = get_gitignore(path)
        directory = cls(path, gitignore)

        # TODO make separate tree for BuiltIn stuff
        built_in = Library("BuiltIn")
        built_in.load_library()
        built_in.filter_not_used = True
        directory.children.insert(0, built_in)
        return directory

    def get_childs(self, gitignore):
        for child in self.path.iterdir():
            gitignore_pattern = f"{child}/" if child.is_dir() else str(child)
            # FIXME __pycache__ is still matched
            if gitignore is not None and gitignore.match_file(gitignore_pattern):
                continue
            if child.is_dir():
                self.children.append(Directory(child, gitignore))
            elif child.is_file():
                if child.suffix not in INCLUDE_EXT:
                    continue
                if child.suffix == ".py":  # TODO better mapping
                    self.children.append(Library(child))
                else:
                    self.children.append(Resource(child))

    def get_resources(self):
        for resource in self.children:
            if resource.type == "Directory":
                yield from resource.get_resources()
            else:
                yield resource.get_resources()

    def __str__(self):
        return str(self.path.name)
