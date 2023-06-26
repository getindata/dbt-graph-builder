from dbt_graph_builder.builder import (
    create_gateway_config,
    create_tasks_graph,
    load_dbt_manifest,
)
from dbt_graph_builder.node_type import NodeType

from .utils import manifest_file_with_models


def test_run_test_dependency():
    # given
    manifest_path = manifest_file_with_models({"model.dbt_test.model1": []})

    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=False,
        show_ephemeral_models=False,
    )

    # then
    assert list(graph.get_graph_edges()) == []
    assert list(graph.get_graph_nodes()) == [
        ("model.dbt_test.model1", {"select": "model1", "depends_on": [], "node_type": NodeType.RUN_TEST})
    ]
    assert graph.get_graph_sinks() == ["model.dbt_test.model1"]
    assert graph.get_graph_sources() == ["model.dbt_test.model1"]


def test_dependency():
    # given
    manifest_path = manifest_file_with_models(
        {
            "model.dbt_test.model1": [],
            "model.dbt_test.model2": ["model.dbt_test.model1"],
        }
    )

    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=False,
        show_ephemeral_models=False,
    )

    # then
    assert list(graph.get_graph_edges()) == [("model.dbt_test.model1", "model.dbt_test.model2")]
    assert list(graph.get_graph_nodes()) == [
        ("model.dbt_test.model1", {"select": "model1", "depends_on": [], "node_type": NodeType.RUN_TEST}),
        (
            "model.dbt_test.model2",
            {"select": "model2", "depends_on": ["model.dbt_test.model1"], "node_type": NodeType.RUN_TEST},
        ),
    ]
    assert graph.get_graph_sinks() == ["model.dbt_test.model2"]
    assert graph.get_graph_sources() == ["model.dbt_test.model1"]


def test_more_complex_dependencies():
    # given
    manifest_path = manifest_file_with_models(
        {
            "model.dbt_test.model1": [],
            "model.dbt_test.model2": ["model.dbt_test.model1"],
            "model.dbt_test.model3": ["model.dbt_test.model1", "model.dbt_test.model2"],
            "model.dbt_test.model4": ["model.dbt_test.model3"],
        }
    )

    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=False,
        show_ephemeral_models=False,
    )

    # then
    assert list(graph.get_graph_edges()) == [
        ("model.dbt_test.model1", "model.dbt_test.model2"),
        ("model.dbt_test.model1", "model.dbt_test.model3"),
        ("model.dbt_test.model2", "model.dbt_test.model3"),
        ("model.dbt_test.model3", "model.dbt_test.model4"),
    ]
    assert list(graph.get_graph_nodes()) == [
        ("model.dbt_test.model1", {"select": "model1", "depends_on": [], "node_type": NodeType.RUN_TEST}),
        (
            "model.dbt_test.model2",
            {"select": "model2", "depends_on": ["model.dbt_test.model1"], "node_type": NodeType.RUN_TEST},
        ),
        (
            "model.dbt_test.model3",
            {
                "select": "model3",
                "depends_on": ["model.dbt_test.model1", "model.dbt_test.model2"],
                "node_type": NodeType.RUN_TEST,
            },
        ),
        (
            "model.dbt_test.model4",
            {"select": "model4", "depends_on": ["model.dbt_test.model3"], "node_type": NodeType.RUN_TEST},
        ),
    ]
    assert graph.get_graph_sinks() == ["model.dbt_test.model4"]
    assert graph.get_graph_sources() == ["model.dbt_test.model1"]


def test_more_complex_dependencies_2():
    # given
    manifest_path = manifest_file_with_models(
        {
            "model.dbt_test.model1": [],
            "model.dbt_test.model2": ["model.dbt_test.model1"],
            "model.dbt_test.model3": ["model.dbt_test.model2"],
            "test.dbt_test.test1": ["model.dbt_test.model1"],
            "test.dbt_test.test2": ["model.dbt_test.model1", "model.dbt_test.model2"],
        }
    )

    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=False,
        show_ephemeral_models=False,
    )

    # then
    assert list(graph.get_graph_edges()) == [
        ("model.dbt_test.model1", "model.dbt_test.model2"),
        ("model.dbt_test.model1", "model1_model2_test"),
        ("model.dbt_test.model2", "model.dbt_test.model3"),
        ("model.dbt_test.model2", "model1_model2_test"),
    ]
    assert list(graph.get_graph_nodes()) == [
        ("model.dbt_test.model1", {"select": "model1", "depends_on": [], "node_type": NodeType.RUN_TEST}),
        (
            "model.dbt_test.model2",
            {"select": "model2", "depends_on": ["model.dbt_test.model1"], "node_type": NodeType.RUN_TEST},
        ),
        (
            "model.dbt_test.model3",
            {"select": "model3", "depends_on": ["model.dbt_test.model2"], "node_type": NodeType.RUN_TEST},
        ),
        (
            "model1_model2_test",
            {
                "select": "test2",
                "depends_on": ["model.dbt_test.model1", "model.dbt_test.model2"],
                "node_type": NodeType.MULTIPLE_DEPS_TEST,
            },
        ),
    ]
    assert graph.get_graph_sinks() == ["model.dbt_test.model3", "model1_model2_test"]
    assert graph.get_graph_sources() == ["model.dbt_test.model1"]


def test_more_complex_dependencies_3():
    # given
    manifest_path = manifest_file_with_models(
        {
            "model.dbt_test.model1": [],
            "model.dbt_test.model2": ["model.dbt_test.model1"],
            "model.dbt_test.model3": ["model.dbt_test.model2"],
            "model.dbt_test.model4": ["model.dbt_test.model1", "model.dbt_test.model2"],
            "model.dbt_test.model5": [],
            "model.dbt_test.model6": [],
            "model.dbt_test.model7": ["model.dbt_test.model6", "model.dbt_test.model5"],
            "test.dbt_test.test1": ["model.dbt_test.model6", "model.dbt_test.model5"],
            "test.dbt_test.test2": ["model.dbt_test.model7", "model.dbt_test.model2"],
            "test.dbt_test.test3": ["model.dbt_test.model2", "model.dbt_test.model3"],
            "test.dbt_test.test4": ["model.dbt_test.model3", "model.dbt_test.model2"],
            "test.dbt_test.test5": ["model.dbt_test.model3", "model.dbt_test.model2"],
        }
    )

    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=False,
        show_ephemeral_models=False,
    )

    # then
    assert list(graph.get_graph_edges()) == [
        ("model.dbt_test.model1", "model.dbt_test.model2"),
        ("model.dbt_test.model1", "model.dbt_test.model4"),
        ("model.dbt_test.model2", "model.dbt_test.model3"),
        ("model.dbt_test.model2", "model.dbt_test.model4"),
        ("model.dbt_test.model2", "model2_model7_test"),
        ("model.dbt_test.model2", "model2_model3_test"),
        ("model.dbt_test.model3", "model2_model3_test"),
        ("model.dbt_test.model5", "model.dbt_test.model7"),
        ("model.dbt_test.model5", "model5_model6_test"),
        ("model.dbt_test.model6", "model.dbt_test.model7"),
        ("model.dbt_test.model6", "model5_model6_test"),
        ("model.dbt_test.model7", "model2_model7_test"),
    ]
    assert list(graph.get_graph_nodes()) == [
        ("model.dbt_test.model1", {"select": "model1", "depends_on": [], "node_type": NodeType.RUN_TEST}),
        (
            "model.dbt_test.model2",
            {"select": "model2", "depends_on": ["model.dbt_test.model1"], "node_type": NodeType.RUN_TEST},
        ),
        (
            "model.dbt_test.model3",
            {"select": "model3", "depends_on": ["model.dbt_test.model2"], "node_type": NodeType.RUN_TEST},
        ),
        (
            "model.dbt_test.model4",
            {
                "select": "model4",
                "depends_on": ["model.dbt_test.model1", "model.dbt_test.model2"],
                "node_type": NodeType.RUN_TEST,
            },
        ),
        ("model.dbt_test.model5", {"select": "model5", "depends_on": [], "node_type": NodeType.RUN_TEST}),
        ("model.dbt_test.model6", {"select": "model6", "depends_on": [], "node_type": NodeType.RUN_TEST}),
        (
            "model.dbt_test.model7",
            {
                "select": "model7",
                "depends_on": ["model.dbt_test.model6", "model.dbt_test.model5"],
                "node_type": NodeType.RUN_TEST,
            },
        ),
        (
            "model5_model6_test",
            {
                "select": "test1",
                "depends_on": ["model.dbt_test.model5", "model.dbt_test.model6"],
                "node_type": NodeType.MULTIPLE_DEPS_TEST,
            },
        ),
        (
            "model2_model7_test",
            {
                "select": "test2",
                "depends_on": ["model.dbt_test.model2", "model.dbt_test.model7"],
                "node_type": NodeType.MULTIPLE_DEPS_TEST,
            },
        ),
        (
            "model2_model3_test",
            {
                "select": "test3 test4 test5",
                "depends_on": ["model.dbt_test.model2", "model.dbt_test.model3"],
                "node_type": NodeType.MULTIPLE_DEPS_TEST,
                "contraction": {
                    "test.dbt_test.test4": {
                        "select": "test4",
                        "depends_on": ["model.dbt_test.model2", "model.dbt_test.model3"],
                        "node_type": NodeType.MULTIPLE_DEPS_TEST,
                    },
                    "test.dbt_test.test5": {
                        "select": "test5",
                        "depends_on": ["model.dbt_test.model2", "model.dbt_test.model3"],
                        "node_type": NodeType.MULTIPLE_DEPS_TEST,
                    },
                },
            },
        ),
    ]
    assert graph.get_graph_sinks() == [
        "model.dbt_test.model4",
        "model5_model6_test",
        "model2_model7_test",
        "model2_model3_test",
    ]
    assert graph.get_graph_sources() == ["model.dbt_test.model1", "model.dbt_test.model5", "model.dbt_test.model6"]
