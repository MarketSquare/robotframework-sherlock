from robot.libraries.BuiltIn import BuiltIn


class LibraryAccessRunning:
    def __init__(self):
        self.lib_instance = BuiltIn().get_library_instance("Selenium")
