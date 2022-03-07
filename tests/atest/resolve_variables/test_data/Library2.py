from robot.api import logger


class Library2:
    def __init__(self, arg):
        self.arg = arg

    def keyword1(self):
        logger.info(f"Variable value: {self.arg}")
