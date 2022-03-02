from pathlib import Path

from robot.api import SuiteVisitor
from robot.variables.scopes import VariableScopes


class StructureVisitor(SuiteVisitor):
    def __init__(self, resources, from_output, robot_settings):
        self.resources = resources
        self.from_output = from_output
        self.variables = VariableScopes(robot_settings)

        self.search_scope = []
        self.suite_errors = set()
        self.errors = []

    def visit_suite(self, suite):
        if suite.source in self.resources:
            self.search_scope.append(self.resources[suite.source])
        elif Path(suite.source).is_dir() and str(Path(suite.source) / "__init__.robot") in self.resources:
            self.search_scope.append(self.resources[str(Path(suite.source) / "__init__.robot")])
        else:
            pass
            # raise SherlockFatalError(f"Could not find definition of '{suite.source}' suite")  # TODO
        # TODO read variables from suite and add it to self.variables
        if self.search_scope:
            self.search_scope[-1].init_imports(self.variables)
        suite.setup.visit(self)
        suite.tests.visit(self)

        # TODO improve error handling
        # if self.suite_errors:
        #     self.errors.append(f"\nErrors in {suite.source}:")
        # self.errors.extend(list(self.suite_errors))

        suite.suites.visit(self)
        suite.teardown.visit(self)
        if self.search_scope:
            self.search_scope.pop()

    def visit_keyword(self, kw):
        if not self.search_scope:
            return
        name = kw.kwname if self.from_output else kw.name
        libname = kw.libname if self.from_output else None
        found = self.search_scope[-1].search(name, self.resources, libname)
        if not found:
            self.suite_errors.add(f"Keyword '{name}' definition not found")
        elif len(found) > 1:
            s = f"Keyword '{name}' matches following resources/libraries:\n"
            self.suite_errors.add(s)
        else:
            found[0].used += 1
            if self.from_output:
                found[0].timings.add_timing(kw.elapsedtime)
            scope = self.resources[found[0].parent]
            self.search_scope.append(scope)
            if hasattr(kw, "body"):
                kw.body.visit(self)
            self.search_scope.pop()
        kw.teardown.visit(self)
