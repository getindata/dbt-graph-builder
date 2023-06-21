from enum import Enum


class NodeType(Enum):
    """Enum for the different types of nodes in the graph."""
    RUN_TEST = 1
    MULTIPLE_DEPS_TEST = 2
    EPHEMERAL = 3
    SOURCE_SENSOR = 4
    MOCK_GATEWAY = 5
