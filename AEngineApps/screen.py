from typing import Any


class Screen:
    def __init__(self) -> None:
        self.__name__ = str(self.__class__).split('.')[1].split('>')[0]
    def run(self):
        raise NotImplementedError(f"Method 'run' of '{self.__name__}' is not implemeted")
    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)