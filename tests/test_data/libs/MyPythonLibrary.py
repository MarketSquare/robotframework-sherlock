from robot.api.deco import not_keyword


class MyPythonLibrary:
    def __init__(self, arg):
        self.arg = arg

    def python_keyword(self, a):
        pass

    def im_not_used(self):
        pass

    @not_keyword
    def should_be_hidden(self):
        pass
