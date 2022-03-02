import sys
from sherlock.core import Sherlock
from sherlock.exceptions import SherlockFatalError


def run_cli():
    try:
        runner = Sherlock()
        runner.run()
    except SherlockFatalError as err:
        print(f"Error: {err}")
        sys.exit(1)
    except Exception as err:
        message = (
            "\nFatal exception occurred. You can create an issue at "
            "https://github.com/bhirsz/robotframework-sherlock/issues . Thanks!"  # TODO change url when migrate
        )
        err.args = (str(err.args[0]) + message,) + err.args[1:]
        raise err
