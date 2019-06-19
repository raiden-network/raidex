class Filter:

    def __init__(self):
        pass

    def process(self, event):

        if self._filter(event):
            return self._transform(event)
        return None

    def _filter(self, event):
        raise NotImplementedError

    def _transform(self, event):
        raise NotImplementedError

