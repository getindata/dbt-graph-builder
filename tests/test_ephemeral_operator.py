from os import path

from dbt_graph_builder.builder import (
    create_gateway_config,
    create_tasks_graph,
    load_dbt_manifest,
)
from dbt_graph_builder.node_type import NodeType
from tests.utils import task_group_prefix_builder


def test_ephemeral_dag():
    # given
    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(path.join(path.dirname(__file__), "manifests/manifest_ephemeral.json")),
        enable_dags_dependencies=False,
        show_ephemeral_models=True,
    )

    # then
    assert list(graph.get_graph_nodes()) == [
        (
            "model.dbt_test.model1",
            {"select": "model1", "depends_on": ["source.dbt_test.source1"], "node_type": NodeType.RUN_TEST},
        ),
        (
            "model.dbt_test.model2",
            {"select": "model2", "depends_on": ["model.dbt_test.model1"], "node_type": NodeType.EPHEMERAL},
        ),
        (
            "model.dbt_test.model3",
            {
                "select": "model3",
                "depends_on": ["model.dbt_test.model2", "model.dbt_test.model5"],
                "node_type": NodeType.EPHEMERAL,
            },
        ),
        (
            "model.dbt_test.model4",
            {"select": "model4", "depends_on": ["model.dbt_test.model10"], "node_type": NodeType.RUN_TEST},
        ),
        (
            "model.dbt_test.model5",
            {"select": "model5", "depends_on": ["source.dbt_test.source2"], "node_type": NodeType.EPHEMERAL},
        ),
        (
            "model.dbt_test.model6",
            {"select": "model6", "depends_on": ["source.dbt_test.source3"], "node_type": NodeType.RUN_TEST},
        ),
        (
            "model.dbt_test.model7",
            {"select": "model7", "depends_on": ["model.dbt_test.model6"], "node_type": NodeType.EPHEMERAL},
        ),
        (
            "model.dbt_test.model8",
            {"select": "model8", "depends_on": ["model.dbt_test.model6"], "node_type": NodeType.EPHEMERAL},
        ),
        (
            "model.dbt_test.model9",
            {
                "select": "model9",
                "depends_on": ["model.dbt_test.model7", "model.dbt_test.model8"],
                "node_type": NodeType.EPHEMERAL,
            },
        ),
        (
            "model.dbt_test.model10",
            {
                "select": "model10",
                "depends_on": ["model.dbt_test.model3", "model.dbt_test.model9"],
                "node_type": NodeType.EPHEMERAL,
            },
        ),
        (
            "model.dbt_test.model11",
            {"select": "model11", "depends_on": ["model.dbt_test.model10"], "node_type": NodeType.EPHEMERAL},
        ),
    ]
    assert list(graph.get_graph_edges()) == [
        ("model.dbt_test.model1", "model.dbt_test.model2"),
        ("model.dbt_test.model2", "model.dbt_test.model3"),
        ("model.dbt_test.model3", "model.dbt_test.model10"),
        ("model.dbt_test.model5", "model.dbt_test.model3"),
        ("model.dbt_test.model6", "model.dbt_test.model7"),
        ("model.dbt_test.model6", "model.dbt_test.model8"),
        ("model.dbt_test.model7", "model.dbt_test.model9"),
        ("model.dbt_test.model8", "model.dbt_test.model9"),
        ("model.dbt_test.model9", "model.dbt_test.model10"),
        ("model.dbt_test.model10", "model.dbt_test.model4"),
        ("model.dbt_test.model10", "model.dbt_test.model11"),
    ]
    assert graph.get_graph_sinks() == ["model.dbt_test.model4", "model.dbt_test.model11"]
    assert graph.get_graph_sources() == ["model.dbt_test.model1", "model.dbt_test.model5", "model.dbt_test.model6"]


def test_no_ephemeral_dag():
    # given
    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(path.join(path.dirname(__file__), "manifests/manifest_ephemeral.json")),
        enable_dags_dependencies=False,
        show_ephemeral_models=False,
    )

    # then
    assert list(graph.get_graph_nodes()) == [
        (
            "model.dbt_test.model1",
            {"select": "model1", "depends_on": ["source.dbt_test.source1"], "node_type": NodeType.RUN_TEST},
        ),
        (
            "model.dbt_test.model4",
            {"select": "model4", "depends_on": ["model.dbt_test.model10"], "node_type": NodeType.RUN_TEST},
        ),
        (
            "model.dbt_test.model6",
            {"select": "model6", "depends_on": ["source.dbt_test.source3"], "node_type": NodeType.RUN_TEST},
        ),
    ]
    assert list(graph.get_graph_edges()) == [
        ("model.dbt_test.model1", "model.dbt_test.model4"),
        ("model.dbt_test.model6", "model.dbt_test.model4"),
    ]
    assert graph.get_graph_sinks() == ["model.dbt_test.model4"]
    assert graph.get_graph_sources() == ["model.dbt_test.model1", "model.dbt_test.model6"]
