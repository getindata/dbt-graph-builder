from dbt_graph_builder.builder import (
    create_gateway_config,
    create_tasks_graph,
    load_dbt_manifest,
)

from .utils import manifest_file_with_models


def test_starting_tasks():
    # given
    manifest_path = manifest_file_with_models(
        {
            "model.dbt_test.model1": [],
            "model.dbt_test.model2": [],
            "model.dbt_test.model3": ["model.dbt_test.model1", "model.dbt_test.model2"],
            "model.dbt_test.model4": ["model.dbt_test.model3"],
            "model.dbt_test.model5": [],
        }
    )

    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    )

    # then
    starting_tasks_names = [task.execution_airflow_task.task_id for task in tasks.get_starting_tasks()]
    assert task_group_prefix_builder("model1", "run") in starting_tasks_names
    assert task_group_prefix_builder("model2", "run") in starting_tasks_names
    assert task_group_prefix_builder("model5", "run") in starting_tasks_names


def test_ending_tasks():
    # given
    manifest_path = manifest_file_with_models(
        {
            "model.dbt_test.model1": [],
            "model.dbt_test.model2": [],
            "model.dbt_test.model3": ["model.dbt_test.model1", "model.dbt_test.model2"],
            "model.dbt_test.model4": ["model.dbt_test.model3"],
            "model.dbt_test.model5": [],
        }
    )

    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    )

    # then
    ending_tasks_names = [task.test_airflow_task.task_id for task in tasks.get_ending_tasks()]
    assert task_group_prefix_builder("model4", "test") in ending_tasks_names
    assert task_group_prefix_builder("model5", "test") in ending_tasks_names
