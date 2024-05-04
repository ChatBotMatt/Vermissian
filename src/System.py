import enum

class System(enum.Enum):
    SPIRE = 'spire'
    HEART = 'heart'

    def __hash__(self):
        return hash(self.value)