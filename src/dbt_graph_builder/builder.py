from __future__ import annotations

import json
import logging
import os
from typing import Any

from dbt_graph_builder.gateway import GatewayConfiguration
from dbt_graph_builder.graph import DbtManifestGraph, GraphConfiguration

LOGGER = logging.getLogger(__name__)


def create_tasks_graph(
    manifest: dict[str, Any],
    graph_config: GraphConfiguration | None = None,
) -> DbtManifestGraph:
    """Create tasks graph.

    Args:
        manifest (dict[str, Any]): Manifest.
        graph_config (GraphConfiguration, optional): Graph configuration. Defaults to None.

    Returns:
        DbtManifestGraph: Tasks graph.
    """
    if graph_config is None:
        graph_config = GraphConfiguration()
    LOGGER.info("Creating tasks graph")
    dbt_airflow_graph = DbtManifestGraph(graph_config)
    dbt_airflow_graph.add_execution_tasks(manifest)
    if graph_config.enable_dags_dependencies:
        LOGGER.debug("Adding external dependencies")
        dbt_airflow_graph.add_external_dependencies(manifest)
    dbt_airflow_graph.create_edges_from_dependencies()
    if not graph_config.show_ephemeral_models:
        LOGGER.debug("Removing ephemeral nodes from graph")
        dbt_airflow_graph.remove_ephemeral_nodes_from_graph()
    LOGGER.debug("Contracting test nodes")
    dbt_airflow_graph.contract_test_nodes()
    LOGGER.debug("Creating multple deps tests dependencies")
    dbt_airflow_graph.create_multiple_deps_test_dependencies()
    return dbt_airflow_graph


def load_dbt_manifest(manifest_path: os.PathLike[str] | str) -> dict[str, Any]:
    """Load dbt manifest.

    Args:
        manifest_path (os.PathLike[str] | str): Path to dbt manifest.

    Returns:
        dict[str, Any]: Dbt manifest.
    """
    LOGGER.info("Loading dbt manifest")
    with open(manifest_path) as file:
        manifest_content = json.load(file)
        return manifest_content  # type: ignore


def create_gateway_config(airflow_config: dict[str, Any]) -> GatewayConfiguration:
    """Create gateway config.

    Args:
        airflow_config (dict[str, Any]): Airflow config.

    Returns:
        GatewayConfiguration: Gateway configuration.
    """
    LOGGER.info("Creating gateway config")
    if "save_points" in airflow_config:
        separation_schemas = airflow_config["save_points"]
    else:
        separation_schemas = []
    return GatewayConfiguration(
        separation_schemas=separation_schemas,
        gateway_task_name="gateway",
    )
