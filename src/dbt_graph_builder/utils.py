def is_task_type(node_name: str, task_type: str) -> bool:
    """_summary_

    Args:
        node_name (str): _description_
        task_type (str): _description_

    Returns:
        bool: _description_
    """
    return node_name.split(".")[0] == task_type


def is_model_run_task(node_name: str) -> bool:
    """_summary_

    Args:
        node_name (str): _description_

    Returns:
        bool: _description_
    """
    return is_task_type(node_name, "model")


def is_source_sensor_task(node_name: str) -> bool:
    """_summary_

    Args:
        node_name (str): _description_

    Returns:
        bool: _description_
    """
    return is_task_type(node_name, "source")


def is_test_task(node_name: str) -> bool:
    """_summary_

    Args:
        node_name (str): _description_

    Returns:
        bool: _description_
    """
    return is_task_type(node_name, "test")


def is_ephemeral_task(node: dict) -> bool:
    return node["config"]["materialized"] == "ephemeral"
