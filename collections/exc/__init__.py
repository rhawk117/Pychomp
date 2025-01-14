


class ChunkOverflowError(Exception):
    def __init__(self, message):
        self.message = message
        self.name = "ChunkOverflowError"
        super().__init__(self.message)