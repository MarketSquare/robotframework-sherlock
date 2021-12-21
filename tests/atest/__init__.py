from sherlock.config import Config
from sherlock.core import Sherlock


def run_sherlock(robot_output, source, report=None):
    config = Config(from_cli=False)
    config.output_path = robot_output
    config.path = source
    if report is not None:
        config.report = report

    sherlock = Sherlock(config=config)
    sherlock.run()  # TODO create special report readable by tests?
