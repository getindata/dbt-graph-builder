import json
import logging
import os
from typing import Any, NamedTuple, cast

from dbt_graph_builder.gateway import GatewayConfiguration, TaskGraphConfiguration
from dbt_graph_builder.graph import DbtManifestGraph

LOGGER = logging.getLogger(__name__)


class GraphConfiguration(NamedTuple):
    """Graph configuration."""

    enable_dags_dependencies: bool = False
    show_ephemeral_models: bool = False


def create_tasks_graph(
    gateway_config: GatewayConfiguration,
    manifest: dict[str, Any],
    graph_config: GraphConfiguration = GraphConfiguration(),
) -> DbtManifestGraph:
    """Create tasks graph.

    Args:
        gateway_config (GatewayConfiguration): Gateway configuration.
        manifest (dict[str, Any]): Manifest.
        graph_config (GraphConfiguration, optional): Graph configuration. Defaults to GraphConfiguration().

    Returns:
        DbtManifestGraph: Tasks graph.
    """
    LOGGER.info("Creating tasks graph")
    dbt_airflow_graph = DbtManifestGraph(TaskGraphConfiguration(gateway_config))
    dbt_airflow_graph.add_execution_tasks(manifest)
    if graph_config.enable_dags_dependencies:
        LOGGER.debug("Adding external dependencies")
        dbt_airflow_graph.add_external_dependencies(manifest)
    dbt_airflow_graph.create_edges_from_dependencies(graph_config.enable_dags_dependencies)
    if not graph_config.show_ephemeral_models:
        LOGGER.debug("Removing ephemeral nodes from graph")
        dbt_airflow_graph.remove_ephemeral_nodes_from_graph()
    LOGGER.debug("Contracting test nodes")
    dbt_airflow_graph.contract_test_nodes()
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
        return cast(dict[str, Any], manifest_content)


def create_gateway_config(airflow_config: dict[str, Any]) -> GatewayConfiguration:
    """Create gateway config.

    Args:
        airflow_config (dict[str, Any]): Airflow config.

    Returns:
        GatewayConfiguration: Gateway configuration.
    """
    LOGGER.info("Creating gateway config")
    return GatewayConfiguration(
        separation_schemas=airflow_config.get("save_points", []),
        gateway_task_name="gateway",
    )
