class Resource(object):

    def __init__(self, space_name: str) -> None:
        self._space_name = space_name
        self._url = f"/spaces/{space_name}"
