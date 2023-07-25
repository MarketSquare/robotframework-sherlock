class LibraryWithFailingInit:
    def __init__(self):
        raise ValueError("Invalid value")
