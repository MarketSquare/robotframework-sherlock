from pathlib import Path
import subprocess

import pytest


@pytest.fixture(scope="class", autouse=True)
def generate_robot_output(path_to_test_data, run_with_tests):
    source = path_to_test_data / run_with_tests
    subprocess.run(
        f"robot --outputdir {path_to_test_data} {source}", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    yield
    for path in (path_to_test_data / "log.html", path_to_test_data / "output.xml", path_to_test_data / "report.html"):
        path.unlink(missing_ok=True)
