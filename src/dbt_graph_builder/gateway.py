from dataclasses import dataclass
from typing import Any

from dbt_graph_builder.utils import is_model_run_task


@dataclass
class NodeProperties:
    """NodeProperties class is used to store node properties from manifest.json file."""

    node_name: str
    schema_name: str


@dataclass
class GatewayConfiguration:
    """GatewayConfiguration class is used to store gateway configuration from dbt_project.yml file."""

    separation_schemas: list[str]
    gateway_task_name: str


@dataclass
class TaskGraphConfiguration:
    """TaskGraphConfiguration class is used to store task graph configuration from dbt_project.yml file."""

    gateway: GatewayConfiguration


@dataclass
class SeparationLayer:
    """Separation layer class."""

    left: str
    right: str


def is_gateway_valid_dependency(
    separation_layer: SeparationLayer, dependency_node_properties: NodeProperties, node_schema: str
) -> bool:
    """Check if the dependency is valid for the gateway.

    Args:
        separation_layer (SeparationLayer): Separation layer.
        dependency_node_properties (NodeProperties): Dependency node properties.
        node_schema (str): Node schema.

    Returns:
        bool: True if the dependency is valid for the gateway, False otherwise.
    """
    if is_model_run_task(dependency_node_properties.node_name):
        dep_schema = dependency_node_properties.schema_name
        if dep_schema == separation_layer.left and node_schema == separation_layer.right:
            return False
        return True
    return True


def get_gateway_dependencies(manifest: dict[str, Any], separation_layer: SeparationLayer) -> list[str]:
    """Get gateway dependencies.

    Args:
        manifest (dict): Manifest.
        separation_layer (SeparationLayer): Separation layer.

    Returns:
        list: Gateway dependencies.
    """
    downstream_dependencies = _get_downstream_dependencies(
        manifest=manifest, separation_layer_right=separation_layer.right
    )

    upstream_dependencies_connected_to_downstream = _get_upstream_dependencies_connected_to_downstream(
        manifest=manifest,
        separation_layer_left=separation_layer.left,
        downstream_dependencies=downstream_dependencies,
    )
    dependencies = [
        node_name
        for node_name, values in manifest["nodes"].items()
        if values["schema"] == separation_layer.left and node_name in upstream_dependencies_connected_to_downstream
    ]
    return dependencies


def _get_downstream_dependencies(manifest: dict[str, Any], separation_layer_right: str) -> list[str]:
    downstream_dependencies = [
        node_name for node_name, values in manifest["nodes"].items() if values["schema"] == separation_layer_right
    ]
    return downstream_dependencies


def _get_upstream_dependencies_connected_to_downstream(
    manifest: dict[str, Any], separation_layer_left: str, downstream_dependencies: list[str]
) -> list[str]:
    upstream_deps_connected_to_downstream: list[str] = []

    for downstream_node in downstream_dependencies:
        upstream_deps = manifest["nodes"][downstream_node]["depends_on"]["nodes"]
        for dep in upstream_deps:
            _add_upstream_dep_based_on_downstream(
                dep=dep,
                manifest=manifest,
                separation_layer_left=separation_layer_left,
                upstream_dependencies_connected_to_downstream=upstream_deps_connected_to_downstream,
            )
    return upstream_deps_connected_to_downstream


def _add_upstream_dep_based_on_downstream(
    dep: str,
    manifest: dict[str, Any],
    separation_layer_left: str,
    upstream_dependencies_connected_to_downstream: list[str],
) -> None:
    if is_model_run_task(dep) and manifest["nodes"][dep]["schema"] == separation_layer_left:
        upstream_dependencies_connected_to_downstream.append(dep)


def add_gateway_to_dependencies(
    gateway_name: str, filtered_dependencies: list[str], filtered_records: list[str]
) -> None:
    """Add gateway to dependencies.

    Args:
        gateway_name (str): Gateway name.
        filtered_dependencies (list[str]): Filtered dependencies.
        filtered_records (list[str]): Filtered records.
    """
    if len(filtered_dependencies) < len(filtered_records):
        filtered_dependencies.append(gateway_name)


def create_gateway_name(separation_layer: SeparationLayer, gateway_task_name: str) -> str:
    """Create gateway name.

    Args:
        separation_layer (SeparationLayer): Separation layer.
        gateway_task_name (str): Gateway task name.

    Returns:
        str: Created gateway name.
    """
    return f"{separation_layer.left}_{separation_layer.right}_{gateway_task_name}"


def should_gateway_be_added(node_schema: str, separation_schemas: list[str]) -> bool:
    """Check if the gateway should be added.

    Args:
        node_schema (str): Node schema.
        separation_schemas (list[str]): Separation schemas.

    Returns:
        bool: True if the gateway should be added, False otherwise.
    """
    valid_schemas_input_length = len(separation_schemas) >= 2
    schema_is_in_given_schemas = node_schema in separation_schemas
    return valid_schemas_input_length and schema_is_in_given_schemas
