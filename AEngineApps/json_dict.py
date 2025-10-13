import json


class JsonDict:
    def __init__(self, path, encoding="utf-8"):
        self.path = path
        self.encoding = encoding
        self.dictionary = self.load()

    def __getitem__(self, item):
        self.dictionary = self.load()
        return self.__getattribute__(item)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __setattr__(self, key, value):
        if "dictionary" in list(self.__dict__):
            if not (key == "dictionary"):
                self.dictionary[key] = value
            self.push(self.dictionary)
        self.__dict__[key] = value
    
    def keys(self) -> list:
        return list(self.dictionary)

    def load(self) -> dict:
        with open(self.path, "r", encoding=self.encoding) as file:
            content = file.read()
            if not content:
                content = "{}"
            dictionary = json.loads(content)

        for k, v in dictionary.items():
            self.__setattr__(k, v)

        return dictionary

    def push(self, data: dict) -> None:
        data = json.dumps(data, indent=2)
        with open(self.path, "w", encoding=self.encoding) as file:
            file.write(data)

    def delete_item(self, key: str) -> None:
        dictionary = self.load()
        del dictionary[key]
        self.push(dictionary)

    def get(self, key: str):
        return self.dictionary.get(key)

    def __repr__(self):
        self.dictionary = self.load()
        return json.dumps(self.dictionary, indent=2)