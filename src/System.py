import enum

class System(enum.Enum):
    SPIRE      = 'spire'
    HEART      = 'heart'
    DIE        = 'die'
    GHOST_GAME = 'get_out_run'
    GOBLIN     = 'goblin_quest'
    ASTIR      = 'astir'

    def __hash__(self):
        return hash(self.value)