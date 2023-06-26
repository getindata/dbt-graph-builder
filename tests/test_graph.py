from os import path

from dbt_graph_builder.builder import (
    create_gateway_config,
    create_tasks_graph,
    load_dbt_manifest,
)
from dbt_graph_builder.node_type import NodeType


def test_manifest_graph():
    # given
    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({"save_points": ["stg", "pp_private_working_schema_dbt_test__audit"]}),
        manifest=load_dbt_manifest(path.join(path.dirname(__file__), "manifests/manifest.json")),
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    )

    # then
    assert list(graph.get_graph_nodes()) == [
        (
            "stg_pp_private_working_schema_dbt_test__audit_gateway",
            {
                "select": "stg_pp_private_working_schema_dbt_test__audit_gateway",
                "depends_on": [],
                "node_type": NodeType.MOCK_GATEWAY,
            },
        ),
        (
            "model.dbt_test.dim_eatopi_users",
            {
                "select": "dim_eatopi_users",
                "depends_on": ["source.dbt_test.raw_schema.eatopi_users"],
                "node_type": NodeType.RUN_TEST,
            },
        ),
    ]
    assert list(graph.get_graph_edges()) == []
    assert graph.get_graph_sinks() == [
        "stg_pp_private_working_schema_dbt_test__audit_gateway",
        "model.dbt_test.dim_eatopi_users",
    ]
    assert graph.get_graph_sources() == [
        "stg_pp_private_working_schema_dbt_test__audit_gateway",
        "model.dbt_test.dim_eatopi_users",
    ]
