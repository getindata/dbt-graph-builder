from .utils import manifest_file_with_models, task_group_prefix_builder


def test_task_group():
    # given
    manifest_path = manifest_file_with_models(
        {
            "model.dbt_test.model1": [],
            "model.dbt_test.model2": ["model.dbt_test.model1"],
            "model.dbt_test.model3": ["model.dbt_test.model1"],
            "model.dbt_test.model4": ["model.dbt_test.model2", "model.dbt_test.model3"],
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
    assert (
        task_group_prefix_builder("model1", "test")
        in tasks.get_task("model.dbt_test.model1").execution_airflow_task.downstream_task_ids
    )
    assert (
        task_group_prefix_builder("model1", "run")
        in tasks.get_task("model.dbt_test.model1").test_airflow_task.upstream_task_ids
    )

    assert (
        task_group_prefix_builder("model1", "test")
        in tasks.get_task("model.dbt_test.model2").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model2", "run")
        in tasks.get_task("model.dbt_test.model1").test_airflow_task.downstream_task_ids
    )

    assert (
        task_group_prefix_builder("model1", "test")
        in tasks.get_task("model.dbt_test.model3").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model3", "run")
        in tasks.get_task("model.dbt_test.model1").test_airflow_task.downstream_task_ids
    )

    assert (
        task_group_prefix_builder("model2", "test")
        in tasks.get_task("model.dbt_test.model4").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model3", "test")
        in tasks.get_task("model.dbt_test.model4").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model4", "run")
        in tasks.get_task("model.dbt_test.model2").test_airflow_task.downstream_task_ids
    )
    assert (
        task_group_prefix_builder("model4", "run")
        in tasks.get_task("model.dbt_test.model3").test_airflow_task.downstream_task_ids
    )


def test_no_task_group():
    # given
    manifest_path = manifest_file_with_models(
        {
            "model.dbt_test.model1": [],
            "model.dbt_test.model2": ["model.dbt_test.model1"],
            "model.dbt_test.model3": ["model.dbt_test.model1"],
            "model.dbt_test.model4": ["model.dbt_test.model2", "model.dbt_test.model3"],
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
    assert "model1_test" in tasks.get_task("model.dbt_test.model1").execution_airflow_task.downstream_task_ids
    assert "model1_run" in tasks.get_task("model.dbt_test.model1").test_airflow_task.upstream_task_ids

    assert "model1_test" in tasks.get_task("model.dbt_test.model2").execution_airflow_task.upstream_task_ids
    assert "model2_run" in tasks.get_task("model.dbt_test.model1").test_airflow_task.downstream_task_ids

    assert "model1_test" in tasks.get_task("model.dbt_test.model3").execution_airflow_task.upstream_task_ids
    assert "model3_run" in tasks.get_task("model.dbt_test.model1").test_airflow_task.downstream_task_ids

    assert "model2_test" in tasks.get_task("model.dbt_test.model4").execution_airflow_task.upstream_task_ids
    assert "model3_test" in tasks.get_task("model.dbt_test.model4").execution_airflow_task.upstream_task_ids
    assert "model4_run" in tasks.get_task("model.dbt_test.model2").test_airflow_task.downstream_task_ids
    assert "model4_run" in tasks.get_task("model.dbt_test.model3").test_airflow_task.downstream_task_ids
