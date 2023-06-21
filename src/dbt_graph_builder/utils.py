def is_task_type(node_name: str, task_type: str) -> bool:
    """Check if node name is of a certain task type.

    Args:
        node_name (str): Node name.
        task_type (str): Task type.

    Returns:
        bool: True if node name is of a certain task type, False otherwise.
    """
    return node_name.split(".")[0] == task_type


def is_model_run_task(node_name: str) -> bool:
    """Check if node name is a model run task.

    Args:
        node_name (str): Node name.

    Returns:
        bool: True if node name is a model run task, False otherwise.
    """
    return is_task_type(node_name, "model")


def is_source_sensor_task(node_name: str) -> bool:
    """Check if node name is a source sensor task.

    Args:
        node_name (str): Node name.

    Returns:
        bool: True if node name is a source sensor task, False otherwise.
    """
    return is_task_type(node_name, "source")


def is_test_task(node_name: str) -> bool:
    """Check if node name is a test task.

    Args:
        node_name (str): Node name.

    Returns:
        bool: True if node name is a test task, False otherwise.
    """
    return is_task_type(node_name, "test")


def is_ephemeral_task(node: dict[str, dict[str, str]]) -> bool:
    """Check if node is ephemeral.

    Args:
        node (dict): Node.

    Returns:
        bool: True if node is ephemeral, False otherwise.
    """
    return node["config"]["materialized"] == "ephemeral"
