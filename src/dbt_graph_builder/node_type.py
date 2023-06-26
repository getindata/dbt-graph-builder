from enum import Enum


class NodeType(Enum):
    """Enum for the different types of nodes in the graph."""

    RUN_TEST = "run_test"
    MULTIPLE_DEPS_TEST = "multiple_deps_test"
    EPHEMERAL = "ephemeral"
    SOURCE_SENSOR = "source_sensor"
    MOCK_GATEWAY = "mock_gateway"
