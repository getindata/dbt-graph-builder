from os import path

from dbt_graph_builder.builder import (
    create_gateway_config,
    create_tasks_graph,
    load_dbt_manifest,
)

from .utils import (
    builder_factory,
    manifest_file_with_models,
    task_group_prefix_builder,
    test_dag,
)


def test_get_dag():
    # given
    manifest_path = manifest_file_with_models({"model.dbt_test.dim_users": []})

    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    )

    # then
    assert tasks.length() == 1
    assert tasks.get_task("model.dbt_test.dim_users") is not None
    assert tasks.get_task("model.dbt_test.dim_users").execution_airflow_task is not None
    assert tasks.get_task("model.dbt_test.dim_users").test_airflow_task is not None


def test_run_task():
    # given
    manifest_path = manifest_file_with_models({"model.dbt_test.dim_users": []})

    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    )

    # then
    run_task = tasks.get_task("model.dbt_test.dim_users").execution_airflow_task
    assert run_task.cmds == ["bash", "-c"]
    assert "dbt --no-write-json run " in run_task.arguments[0]
    assert "--select dim_users" in run_task.arguments[0]
    assert '--vars "{}"' in run_task.arguments[0]
    assert run_task.name == "dim-users-run" if IS_FIRST_AIRFLOW_VERSION else "run"
    assert run_task.task_id == task_group_prefix_builder("dim_users", "run")


def test_test_task():
    # given
    manifest_path = manifest_file_with_models({"model.dbt_test.dim_users": []})

    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    )

    # then
    test_task = tasks.get_task("model.dbt_test.dim_users").test_airflow_task
    assert test_task.cmds == ["bash", "-c"]
    assert "dbt --no-write-json test " in test_task.arguments[0]
    assert "--select dim_users" in test_task.arguments[0]
    assert '--vars "{}"' in test_task.arguments[0]
    assert test_task.name == "dim-users-test" if IS_FIRST_AIRFLOW_VERSION else "test"
    assert test_task.task_id == task_group_prefix_builder("dim_users", "test")


def test_dbt_vars():
    # given
    manifest_path = manifest_file_with_models({"model.dbt_test.dim_users": []})
    factory = DbtAirflowTasksBuilderFactory(path.dirname(path.abspath(__file__)), "vars", {})

    # when
    graph = create_tasks_graph(
        gateway_config=create_gateway_config({}),
        manifest=load_dbt_manifest(manifest_path),
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    )

    # then
    run_task = tasks.get_task("model.dbt_test.dim_users").execution_airflow_task
    assert run_task.cmds == ["bash", "-c"]
    assert "dbt --no-write-json run " in run_task.arguments[0]
    assert '--vars "{variable_1: 123, variable_2: var2}"' in run_task.arguments[0]
