from dbt_graph_builder.builder import create_tasks_graph, load_dbt_manifest, create_gateway_config
from .utils import (manifest_file_with_models)


def test_run_test_dependency():
    # given
    manifest_path = manifest_file_with_models({"model.dbt_test.model1": []})

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
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    ))

    # then
    assert tasks.length() == 2

    assert (
        task_group_prefix_builder("model1", "test")
        in tasks.get_task("model.dbt_test.model2").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model2", "run")
        in tasks.get_task("model.dbt_test.model1").test_airflow_task.downstream_task_ids
    )


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
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    )

    # then
    assert tasks.length() == 4
    assert (
        task_group_prefix_builder("model1", "test")
        in tasks.get_task("model.dbt_test.model2").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model1", "test")
        in tasks.get_task("model.dbt_test.model3").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model2", "run")
        in tasks.get_task("model.dbt_test.model1").test_airflow_task.downstream_task_ids
    )
    assert (
        task_group_prefix_builder("model3", "run")
        in tasks.get_task("model.dbt_test.model1").test_airflow_task.downstream_task_ids
    )
    assert (
        task_group_prefix_builder("model1", "test")
        in tasks.get_task("model.dbt_test.model3").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model2", "test")
        in tasks.get_task("model.dbt_test.model3").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model4", "run")
        in tasks.get_task("model.dbt_test.model3").test_airflow_task.downstream_task_ids
    )


def test_test_dependencies():
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
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    )

    # then
    assert tasks.length() == 4
    assert (
        task_group_prefix_builder("model1", "test")
        in tasks.get_task("model.dbt_test.model2").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model2", "test")
        in tasks.get_task("model.dbt_test.model3").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model2", "run")
        in tasks.get_task("model.dbt_test.model1").test_airflow_task.downstream_task_ids
    )
    assert (
        task_group_prefix_builder("model3", "run")
        in tasks.get_task("model.dbt_test.model2").test_airflow_task.downstream_task_ids
    )

    assert "model1_model2_test" in tasks.get_task("model.dbt_test.model1").test_airflow_task.downstream_task_ids
    assert (
        task_group_prefix_builder("model1", "test")
        in tasks.get_task("model1_model2_test").execution_airflow_task.upstream_task_ids
    )
    assert "model1_model2_test" in tasks.get_task("model.dbt_test.model2").test_airflow_task.downstream_task_ids
    assert (
        task_group_prefix_builder("model2", "test")
        in tasks.get_task("model1_model2_test").execution_airflow_task.upstream_task_ids
    )


def test_complex_test_dependencies():
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
        enable_dags_dependencies=True,
        show_ephemeral_models=False,
    )

    # then
    assert tasks.length() == 10
    assert (
        task_group_prefix_builder("model1", "test")
        in tasks.get_task("model.dbt_test.model2").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model2", "run")
        in tasks.get_task("model.dbt_test.model1").test_airflow_task.downstream_task_ids
    )
    assert (
        task_group_prefix_builder("model2", "test")
        in tasks.get_task("model.dbt_test.model3").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model3", "run")
        in tasks.get_task("model.dbt_test.model2").test_airflow_task.downstream_task_ids
    )
    assert (
        task_group_prefix_builder("model1", "test")
        in tasks.get_task("model.dbt_test.model4").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model2", "test")
        in tasks.get_task("model.dbt_test.model4").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model4", "run")
        in tasks.get_task("model.dbt_test.model1").test_airflow_task.downstream_task_ids
    )
    assert (
        task_group_prefix_builder("model4", "run")
        in tasks.get_task("model.dbt_test.model2").test_airflow_task.downstream_task_ids
    )
    assert (
        task_group_prefix_builder("model5", "test")
        in tasks.get_task("model.dbt_test.model7").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model7", "run")
        in tasks.get_task("model.dbt_test.model5").test_airflow_task.downstream_task_ids
    )
    assert (
        task_group_prefix_builder("model6", "test")
        in tasks.get_task("model.dbt_test.model7").execution_airflow_task.upstream_task_ids
    )
    assert (
        task_group_prefix_builder("model7", "run")
        in tasks.get_task("model.dbt_test.model6").test_airflow_task.downstream_task_ids
    )

    def extract_model_arguments(args: str) -> list[str]:
        return list(filter(lambda s: not s.startswith("-"), args.split("--select ")[1].split()))

    assert "model2_model3_test" in tasks.get_task("model.dbt_test.model2").test_airflow_task.downstream_task_ids
    assert (
        task_group_prefix_builder("model2", "test")
        in tasks.get_task("model2_model3_test").execution_airflow_task.upstream_task_ids
    )
    assert "model2_model3_test" in tasks.get_task("model.dbt_test.model3").test_airflow_task.downstream_task_ids
    assert (
        task_group_prefix_builder("model3", "test")
        in tasks.get_task("model2_model3_test").execution_airflow_task.upstream_task_ids
    )
    assert all(
        test_name in extract_model_arguments(tasks.get_task("model2_model3_test").execution_airflow_task.arguments[0])
        for test_name in ["test3", "test4", "test5"]
    )
    assert all(
        test_name
        not in extract_model_arguments(tasks.get_task("model2_model3_test").execution_airflow_task.arguments[0])
        for test_name in ["test1", "test2"]
    )
    assert "model2_model7_test" in tasks.get_task("model.dbt_test.model2").test_airflow_task.downstream_task_ids
    assert (
        task_group_prefix_builder("model2", "test")
        in tasks.get_task("model2_model7_test").execution_airflow_task.upstream_task_ids
    )
    assert "model2_model7_test" in tasks.get_task("model.dbt_test.model7").test_airflow_task.downstream_task_ids
    assert (
        task_group_prefix_builder("model7", "test")
        in tasks.get_task("model2_model7_test").execution_airflow_task.upstream_task_ids
    )
    assert "test2" in extract_model_arguments(tasks.get_task("model2_model7_test").execution_airflow_task.arguments[0])
    assert all(
        test_name
        not in extract_model_arguments(tasks.get_task("model2_model7_test").execution_airflow_task.arguments[0])
        for test_name in ["test1", "test3", "test4", "test5"]
    )
    assert "model5_model6_test" in tasks.get_task("model.dbt_test.model5").test_airflow_task.downstream_task_ids
    assert (
        task_group_prefix_builder("model5", "test")
        in tasks.get_task("model5_model6_test").execution_airflow_task.upstream_task_ids
    )
    assert "model5_model6_test" in tasks.get_task("model.dbt_test.model6").test_airflow_task.downstream_task_ids
    assert (
        task_group_prefix_builder("model6", "test")
        in tasks.get_task("model5_model6_test").execution_airflow_task.upstream_task_ids
    )
    assert "test1" in extract_model_arguments(tasks.get_task("model5_model6_test").execution_airflow_task.arguments[0])
    assert all(
        test_name
        not in extract_model_arguments(tasks.get_task("model5_model6_test").execution_airflow_task.arguments[0])
        for test_name in ["test2", "test3", "test4", "test5"]
    )
