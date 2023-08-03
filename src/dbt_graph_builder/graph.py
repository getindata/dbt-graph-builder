from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass, field
from typing import Any

import networkx as nx
from networkx.classes.reportviews import NodeDataView, OutEdgeDataView

from dbt_graph_builder.gateway import (
    GatewayConfiguration,
    NodeProperties,
    SeparationLayer,
    add_gateway_to_dependencies,
    create_gateway_name,
    get_gateway_dependencies,
    is_gateway_valid_dependency,
    should_gateway_be_added,
)
from dbt_graph_builder.node_type import NodeType
from dbt_graph_builder.utils import (
    is_ephemeral_task,
    is_model_run_task,
    is_source_sensor_task,
    is_test_task,
)


def _default_gateway_config() -> GatewayConfiguration:
    return GatewayConfiguration([], "gateway")


@dataclass(frozen=True)
class GraphConfiguration:
    """Graph configuration."""

    gateway_config: GatewayConfiguration = field(default_factory=_default_gateway_config)
    dbt_manifest_props: dict[str, str] = field(default_factory=dict)
    enable_dags_dependencies: bool = False
    show_ephemeral_models: bool = False
    check_all_deps_for_multiple_deps_tests: bool = False


class DbtManifestGraph:
    """DbtManifestGraph class is used to create a DAG from DBT manifest.json file."""

    def __init__(self, configuration: GraphConfiguration) -> None:
        """Create DbtManifestGraph.

        Args:
            configuration (GraphConfiguration): Graph configuration.
        """
        self._graph = nx.DiGraph()
        self._configuration = configuration

    @property
    def graph(self) -> nx.DiGraph:
        """Get graph.

        Returns:
            nx.DiGraph: Graph.
        """
        return self._graph

    def add_execution_tasks(self, manifest: dict[str, Any]) -> None:
        """Add execution tasks.

        Args:
            manifest (dict): DBT manifest.
        """
        self._add_gateway_execution_tasks(manifest=manifest)

        for node_name, manifest_node in manifest["nodes"].items():
            if is_model_run_task(node_name):
                logging.info("Creating tasks for: " + node_name)
                self._add_graph_node_for_model_run_task(node_name, manifest_node, manifest)
            elif (
                is_test_task(node_name)
                and len(self._get_model_dependencies_from_manifest_node(manifest_node, manifest)) > 1
            ):
                logging.info("Creating tasks for: " + node_name)
                self._add_graph_node_for_multiple_deps_test(node_name, manifest_node, manifest)

    def _add_gateway_execution_tasks(self, manifest: dict[str, Any]) -> None:
        if len(self._configuration.gateway_config.separation_schemas) >= 2:
            separation_layers = self._configuration.gateway_config.separation_schemas

            for index, _ in enumerate(separation_layers[:-1]):
                separation_layer_left = separation_layers[index]
                separation_layer_right = separation_layers[index + 1]
                self._add_gateway_node(
                    manifest=manifest,
                    separation_layer=SeparationLayer(left=separation_layer_left, right=separation_layer_right),
                )

    def add_external_dependencies(self, manifest: dict[str, Any]) -> None:
        """Add external dependencies.

        Args:
            manifest (dict): DBT manifest object.
        """
        manifest_child_map = manifest["child_map"]
        for source_name, manifest_source in manifest["sources"].items():
            if "dag" in manifest_source["source_meta"] and len(manifest_child_map[source_name]) > 0:
                logging.info("Creating source sensor for: " + source_name)
                self._add_sensor_source_node(source_name, manifest_source)

    def create_edges_from_dependencies(self, include_sensors: bool = False) -> None:
        """Create edges from dependencies.

        Args:
            include_sensors (bool, optional): If True, include sensors in the graph. Defaults to False.
        """
        for graph_node_name, graph_node in self.get_graph_nodes():
            for dependency in graph_node.get("depends_on", []):
                if is_source_sensor_task(dependency) and not include_sensors:
                    continue
                if not self._graph.has_node(dependency):
                    continue
                self._graph.add_edge(dependency, graph_node_name)

    def get_graph_nodes(self) -> NodeDataView:
        """Get graph nodes.

        Returns:
            NodeDataView: a view of graph nodes.
        """
        return self._graph.nodes(data=True)

    def get_graph_edges(self) -> OutEdgeDataView:
        """Get graph edges.

        Returns:
            OutEdgeDataView: A list of graph edges.
        """
        return self._graph.edges()

    def get_graph_sources(self) -> list[str]:
        """Return a list of graph source nodes.

        Returns:
            list[str]: A list of graph source nodes.
        """
        return [node_name for node_name in self._graph.nodes() if len(list(self._graph.predecessors(node_name))) == 0]

    def get_graph_sinks(self) -> list[str]:
        """Return a list of graph sink nodes.

        Returns:
            list[str]: A list of graph sink nodes.
        """
        return [node_name for node_name in self._graph.nodes() if len(list(self._graph.successors(node_name))) == 0]

    def remove_ephemeral_nodes_from_graph(self) -> None:
        """Remove ephemeral nodes from the graph."""
        ephemeral_nodes = [
            node_name for node_name, node in self._graph.nodes(data=True) if node["node_type"] == NodeType.EPHEMERAL
        ]
        for node_name in ephemeral_nodes:
            self._graph.add_edges_from(
                itertools.product(
                    list(self._graph.predecessors(node_name)),
                    list(self._graph.successors(node_name)),
                )
            )
            self._graph.remove_node(node_name)

    def create_multiple_deps_test_dependencies(self, check_all_predecessors: bool) -> None:
        """Create edges from dependencies to multiple deps test.

        Args:
            check_all_predecessors (bool): If True, check all predecessors when creating dependencies.
                Defaults to False.
        """
        for test_node_name, node in self._graph.nodes(data=True):
            if node["node_type"] != NodeType.MULTIPLE_DEPS_TEST:
                continue
            for node_name in self._graph.nodes():
                if self._check_if_node_predecessors_are_superset_of_test_deps(
                    node_name, test_node_name, check_all_predecessors=check_all_predecessors
                ):
                    self._graph.add_edge(test_node_name, node_name)

    def _get_all_node_predecessors(self, node_name: str) -> set[str]:
        predecessors = set(self._graph.predecessors(node_name))
        for predecessor in predecessors:
            predecessors |= self._get_all_node_predecessors(predecessor)
        return predecessors

    def _check_if_node_predecessors_are_superset_of_test_deps(
        self, node_name: str, test_node_name: str, check_all_predecessors: bool
    ) -> bool:
        node = self._graph.nodes[node_name]
        test_node = self._graph.nodes[test_node_name]
        if node["node_type"] != NodeType.RUN_TEST:
            return False
        test_deps: set[str] = set(test_node["depends_on"])
        if node_name in test_deps:
            return False
        if test_deps.issubset(set(node["depends_on"])):
            return True
        if not check_all_predecessors:
            return False
        predecessors = self._get_all_node_predecessors(node_name)
        if not test_deps.issubset(predecessors):
            return False
        if test_node_name in predecessors:
            return False
        return True

    def contract_test_nodes(self) -> None:
        """Contract test nodes."""
        tests_with_more_deps = self._get_test_with_multiple_deps_names_by_deps()
        for depends_on_tuple, test_node_names in tests_with_more_deps.items():
            self._contract_test_nodes_same_deps(depends_on_tuple, test_node_names)

    def get_default_node_values(self, manifest_node: dict[str, Any]) -> dict[str, Any]:
        """Get default node values.

        Args:
            manifest_node (dict): Manifest node.

        Returns:
            dict: Default node values.
        """
        result: dict[str, Any] = {}
        for key, value in self._configuration.dbt_manifest_props.items():
            if key in manifest_node:
                result[value] = manifest_node[key]
        return result

    def _add_execution_graph_node(
        self, node_name: str, manifest_node: dict[str, Any], node_type: NodeType, manifest: dict[str, Any]
    ) -> None:
        self._graph.add_node(
            node_name,
            select=manifest_node["name"],
            depends_on=self._get_model_dependencies_from_manifest_node(manifest_node, manifest),
            node_type=node_type,
            **self.get_default_node_values(manifest_node),
        )

    def _add_sensor_source_node(self, node_name: str, manifest_node: dict[str, Any]) -> None:
        self._graph.add_node(
            node_name,
            select=manifest_node["name"],
            dag=manifest_node["source_meta"]["dag"],
            node_type=NodeType.SOURCE_SENSOR,
            **self.get_default_node_values(manifest_node),
        )

    def _add_gateway_node(self, manifest: dict[str, Any], separation_layer: SeparationLayer) -> None:
        node_name = create_gateway_name(
            separation_layer=separation_layer,
            gateway_task_name=self._configuration.gateway_config.gateway_task_name,
        )
        self._graph.add_node(
            node_name,
            select=node_name,
            depends_on=get_gateway_dependencies(separation_layer=separation_layer, manifest=manifest),
            node_type=NodeType.MOCK_GATEWAY,
            **self.get_default_node_values({"alias": node_name}),
        )

    def _add_graph_node_for_model_run_task(
        self, node_name: str, manifest_node: dict[str, Any], manifest: dict[str, Any]
    ) -> None:
        self._add_execution_graph_node(
            node_name,
            manifest_node,
            NodeType.EPHEMERAL if is_ephemeral_task(manifest_node) else NodeType.RUN_TEST,
            manifest,
        )

    def _add_graph_node_for_multiple_deps_test(
        self, node_name: str, manifest_node: dict[str, Any], manifest: dict[str, Any]
    ) -> None:
        self._add_execution_graph_node(node_name, manifest_node, NodeType.MULTIPLE_DEPS_TEST, manifest)

    def _get_test_with_multiple_deps_names_by_deps(
        self,
    ) -> dict[tuple[str, ...], list[str]]:
        tests_with_more_deps: dict[tuple[str, ...], list[str]] = {}

        for node_name, node in self._graph.nodes(data=True):
            if node["node_type"] != NodeType.MULTIPLE_DEPS_TEST:
                continue
            model_dependencies: list[str] = sorted(node["depends_on"])
            test_key = tuple(model_dependencies)
            if test_key not in tests_with_more_deps:
                tests_with_more_deps[test_key] = []
            tests_with_more_deps[test_key].append(node_name)

        return tests_with_more_deps

    def _contract_test_nodes_same_deps(self, depends_on_tuple: tuple[str, ...], test_node_names: list[str]) -> None:
        test_names = [self._graph.nodes[test_node]["select"] for test_node in test_node_names]

        first_test_node = test_node_names[0]
        for test_node in test_node_names[1:]:
            nx.contracted_nodes(
                self._graph,
                first_test_node,
                test_node,
                self_loops=False,
                copy=False,  # in-memory
            )

        self._graph.nodes[first_test_node]["select"] = " ".join(test_names)
        nx.relabel_nodes(
            self._graph,
            {first_test_node: self._build_multiple_deps_test_name(depends_on_tuple)},
            copy=False,
        )

    def _get_model_dependencies_from_manifest_node(self, node: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
        filtered_records = list(filter(DbtManifestGraph._is_valid_dependency, node["depends_on"]["nodes"]))
        node_schema = node.get("schema", None)

        if should_gateway_be_added(
            node_schema=node_schema,
            separation_schemas=self._configuration.gateway_config.separation_schemas,
        ):
            node_schema_index = self._configuration.gateway_config.separation_schemas.index(node_schema)
            if node_schema_index >= 1:
                filtered_records = self._filter_to_gateway_conditions(
                    node_schema_index=node_schema_index,
                    manifest=manifest,
                    node=node,
                    filtered_records=filtered_records,
                )

        return filtered_records

    def _filter_to_gateway_conditions(
        self,
        node_schema_index: int,
        manifest: dict[str, Any],
        node: dict[str, Any],
        filtered_records: list[str],
    ) -> list[str]:
        separation_layers = self._configuration.gateway_config.separation_schemas
        separation_layer_left = separation_layers[node_schema_index - 1]
        separation_layer_right = separation_layers[node_schema_index]

        filtered_dependencies = list(
            filter(
                lambda dep_node: is_gateway_valid_dependency(
                    separation_layer=SeparationLayer(left=separation_layer_left, right=separation_layer_right),
                    dependency_node_properties=_get_node_properties(node_name=dep_node, manifest=manifest),
                    node_schema=node["schema"],
                ),
                filtered_records,
            )
        )

        add_gateway_to_dependencies(
            filtered_dependencies=filtered_dependencies,
            filtered_records=filtered_records,
            gateway_name=create_gateway_name(
                separation_layer=SeparationLayer(left=separation_layer_left, right=separation_layer_right),
                gateway_task_name=self._configuration.gateway_config.gateway_task_name,
            ),
        )
        return filtered_dependencies

    @staticmethod
    def _is_valid_dependency(node_name: str) -> bool:
        return is_model_run_task(node_name) or is_source_sensor_task(node_name)  # type: ignore

    @staticmethod
    def _build_multiple_deps_test_name(dependencies: tuple[str, ...]) -> str:
        return "_".join(node_name.split(".")[-1] for node_name in dependencies) + "_test"


def _get_node_properties(node_name: str, manifest: dict[str, Any]) -> NodeProperties:
    resources = manifest["sources"] if is_source_sensor_task(node_name) else manifest["nodes"]
    return NodeProperties(
        node_name=node_name,
        schema_name=resources[node_name]["schema"],
    )
