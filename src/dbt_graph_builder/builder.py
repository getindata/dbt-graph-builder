import json
import logging
import os
from typing import Any

from dbt_graph_builder.gateway import GatewayConfiguration
from dbt_graph_builder.graph import DbtManifestGraph

LOGGER = logging.getLogger(__name__)


def create_tasks_graph(
    gateway_config: GatewayConfiguration,
    manifest: dict[str, Any],
    enable_dags_dependencies: bool,
    show_ephemeral_models: bool,
) -> DbtManifestGraph:
    LOGGER.info("Creating tasks graph")
    dbt_airflow_graph = DbtManifestGraph(gateway_config)
    dbt_airflow_graph.add_execution_tasks(manifest)
    if enable_dags_dependencies:
        LOGGER.debug("Adding external dependencies")
        dbt_airflow_graph.add_external_dependencies(manifest)
    dbt_airflow_graph.create_edges_from_dependencies(enable_dags_dependencies)
    if not show_ephemeral_models:
        LOGGER.debug("Removing ephemeral nodes from graph")
        dbt_airflow_graph.remove_ephemeral_nodes_from_graph()
    LOGGER.debug("Contracting test nodes")
    dbt_airflow_graph.contract_test_nodes()
    return dbt_airflow_graph


def load_dbt_manifest(manifest_path: os.PathLike[str] | str) -> dict[str, Any]:
    LOGGER.info("Loading dbt manifest")
    with open(manifest_path) as f:
        manifest_content = json.load(f)
        return manifest_content


def create_gateway_config(airflow_config: dict[str, Any]) -> GatewayConfiguration:
    LOGGER.info("Creating gateway config")
    return GatewayConfiguration(
        separation_schemas=airflow_config.get("save_points", []),
        gateway_task_name="gateway",
    )
