from dbt_graph_builder.builder import (
    create_gateway_config,
    create_tasks_graph,
    load_dbt_manifest,
)
from dbt_graph_builder.node_type import NodeType

from .utils import manifest_file_with_models

extra_metadata_data = {
    "child_map": {
        "source.upstream_pipeline_sources.upstream_pipeline.some_final_model": ["model.dbt_test.dependent_model"],
        "source.upstream_pipeline_sources.upstream_pipeline.unused": [],
    },
    "sources": {
        "source.upstream_pipeline_sources.upstream_pipeline.some_final_model": {
            "database": "gid-dataops-labs",
            "schema": "presentation",
            "name": "some_final_model",
            "unique_id": "source.upstream_pipeline_sources.upstream_pipeline.some_final_model",
            "source_meta": {"dag": "dbt-tpch-test"},
        },
        "source.upstream_pipeline_sources.upstream_pipeline.unused": {
            "database": "gid-dataops-labs",
            "schema": "presentation",
            "name": "unused",
            "unique_id": "source.upstream_pipeline_sources.upstream_pipeline.unused",
            "source_meta": {"dag": "dbt-tpch-test"},
        },
        "source.upstream_pipeline_sources.upstream_pipeline.no_dag": {
            "database": "gid-dataops-labs",
            "schema": "presentation",
            "name": "no_dag",
            "unique_id": "source.upstream_pipeline_sources.upstream_pipeline.no_dag",
            "source_meta": {},
        },
    },
}


def test_dag_sensor():
    # given
    manifest_path = manifest_file_with_models(
        {"model.dbt_test.dependent_model": ["source.upstream_pipeline_sources.upstream_pipeline.some_final_model"]},
        extra_metadata_data,
    )
    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    )
    # then
    assert graph.get_graph_sources() == ["source.upstream_pipeline_sources.upstream_pipeline.some_final_model"]
    assert graph.get_graph_sinks() == ["model.dbt_test.dependent_model"]
    assert list(graph.get_graph_nodes()) == [
        (
            "model.dbt_test.dependent_model",
            {
                "select": "dependent_model",
                "depends_on": ["source.upstream_pipeline_sources.upstream_pipeline.some_final_model"],
                "node_type": NodeType.RUN_TEST,
            },
        ),
        (
            "source.upstream_pipeline_sources.upstream_pipeline.some_final_model",
            {
                "select": "some_final_model",
                "dag": "dbt-tpch-test",
                "node_type": NodeType.SOURCE_SENSOR,
            },
        ),
    ]
    assert list(graph.get_graph_edges()) == [
        (
            "source.upstream_pipeline_sources.upstream_pipeline.some_final_model",
            "model.dbt_test.dependent_model",
        )
    ]


def test_dag_sensor_no_meta():
    # given
    manifest_path = manifest_file_with_models(
        {
            "model.dbt_test.dependent_model": [
                "source.upstream_pipeline_sources.upstream_pipeline.some_final_model",
                "source.upstream_pipeline_sources.upstream_pipeline.no_dag",
            ]
        },
        extra_metadata_data,
    )

    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    )

    # then
    assert graph.get_graph_sources() == ["source.upstream_pipeline_sources.upstream_pipeline.some_final_model"]
    assert graph.get_graph_sinks() == ["model.dbt_test.dependent_model"]
    assert list(graph.get_graph_nodes()) == [
        (
            "model.dbt_test.dependent_model",
            {
                "select": "dependent_model",
                "depends_on": [
                    "source.upstream_pipeline_sources.upstream_pipeline.some_final_model",
                    "source.upstream_pipeline_sources.upstream_pipeline.no_dag",
                ],
                "node_type": NodeType.RUN_TEST,
            },
        ),
        (
            "source.upstream_pipeline_sources.upstream_pipeline.some_final_model",
            {"select": "some_final_model", "dag": "dbt-tpch-test", "node_type": NodeType.SOURCE_SENSOR},
        ),
    ]
    assert list(graph.get_graph_edges()) == [
        (
            "source.upstream_pipeline_sources.upstream_pipeline.some_final_model",
            "model.dbt_test.dependent_model",
        )
    ]
