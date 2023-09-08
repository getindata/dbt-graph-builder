from __future__ import annotations

import json
import tempfile
from typing import Any


def manifest_file_with_models(nodes_with_dependencies: dict, extra_metadata: dict = None):
    content_nodes = {}
    for node_name in nodes_with_dependencies.keys():
        content_nodes[node_name] = {
            "depends_on": {"nodes": nodes_with_dependencies[node_name]},
            "config": {"materialized": "view"},
            "name": node_name.split(".")[-1],
        }
    content = {"nodes": content_nodes, "child_map": {}}
    if extra_metadata:
        content.update(extra_metadata)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(str.encode(json.dumps(content)))
        return tmp.name


def get_default_airflow_config(
    enable_dags_dependencies: bool = False, use_task_group: bool = False, show_ephemeral_models: bool = True
) -> dict[str, Any]:
    return {
        "enable_dags_dependencies": enable_dags_dependencies,
        "use_task_group": use_task_group,
        "show_ephemeral_models": show_ephemeral_models,
    }


def task_group_prefix_builder(task_model_id: str, task_command: str, is_first_airflow_version: bool = False) -> str:
    return f"{task_model_id}_{task_command}" if is_first_airflow_version else f"{task_model_id}.{task_command}"
