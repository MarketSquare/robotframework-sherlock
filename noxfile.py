import nox

DEFAULT_PYTHON_VERSION = "3.9"
UNIT_TEST_PYTHON_VERSIONS = ["3.7", "3.8", "3.9", "3.10"]
nox.options.sessions = [
    "unit",
]


@nox.session(python=UNIT_TEST_PYTHON_VERSIONS)
def unit(session):
    session.install(".[dev]")
    session.run("pytest", "tests")


@nox.session(python=DEFAULT_PYTHON_VERSION)
def coverage(session):
    session.install(".[dev]")
    session.install("coverage")
    session.run("coverage", "run", "-m", "pytest")
    session.run("coverage", "html")
