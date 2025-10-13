class GlobalStorage:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(GlobalStorage, cls).__new__(cls)
        return cls.__instance

    def __setattr__(self, key, value):
        self.__dict__[key] = value

    def __getattr__(self, item):
        return self.__dict__[item]