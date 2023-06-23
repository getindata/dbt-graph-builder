"""Classes representing tasks corresponding to a single DBT model."""

from collections.abc import Iterable

from airflow.models.baseoperator import BaseOperator


class ModelExecutionTask:
    """Wrapper around tasks corresponding to a single DBT model."""

    def __init__(
        self,
        execution_airflow_task: BaseOperator,
        test_airflow_task: BaseOperator | None = None,
        task_group: BaseOperator | None = None,
    ) -> None:
        """Initialize model's tasks.

        Args:
            execution_airflow_task (BaseOperator): _description_
            test_airflow_task (BaseOperator | None, optional): _description_. Defaults to None.
            task_group (BaseOperator | None, optional): _description_. Defaults to None.
        """
        self.execution_airflow_task = execution_airflow_task
        self.test_airflow_task = test_airflow_task
        self.task_group = task_group

    def __repr__(self) -> str:
        return (
            repr(self.task_group)
            if self.task_group
            else repr([self.execution_airflow_task] + ([self.test_airflow_task] if self.test_airflow_task else []))
        )

    def get_start_task(self) -> BaseOperator:
        """Return model's first task.

        It is either a whole TaskGroup or ``run`` task.

        Returns:
            BaseOperator: Model's first task.
        """
        return self.task_group or self.execution_airflow_task

    def get_end_task(self) -> BaseOperator:
        """Return model's last task.

        It is either a whole TaskGroup, ``test`` task, or ``run`` task, depending
        on version of Airflow and existence of ``test`` task.

        Returns:
            BaseOperator: Model's last task.
        """
        return self.task_group or self.test_airflow_task or self.execution_airflow_task


class ModelExecutionTasks:
    """Dictionary of all Operators corresponding to DBT tasks."""

    def __init__(
        self,
        tasks: dict[str, ModelExecutionTask],
        starting_task_names: list[str],
        ending_task_names: list[str],
    ) -> None:
        """Create ModelExecutionTasks.

        Args:
            tasks (dict[str, ModelExecutionTask]): Dictionary of all Operators corresponding to DBT tasks.
            starting_task_names (list[str]): List of all DAG sources.
            ending_task_names (list[str]): List of all DAG sinks.
        """
        self._tasks = tasks
        self._starting_task_names = starting_task_names
        self._ending_task_names = ending_task_names

    def __repr__(self) -> str:
        return f"ModelExecutionTasks(\n {self._tasks} \n)"

    def get_task(self, node_name: str) -> ModelExecutionTask:
        """Get TaskGroup corresponding to a single DBT model.

        Args:
            node_name (str): Name of the DBT model.

        Returns:
            ModelExecutionTask: TaskGroup corresponding to a single DBT model.
        """
        return self._tasks[node_name]

    def length(self) -> int:
        """Count TaskGroups corresponding to a single DBT model.

        Returns:
            int: Number of TaskGroups corresponding to a single DBT model.
        """
        return len(self._tasks)

    def get_starting_tasks(self) -> list[ModelExecutionTask]:
        """Return a list of all DAG sources.

        Returns:
            list[ModelExecutionTask]: List of all DAG sources.
        """
        return self._extract_by_keys(self._starting_task_names)

    def get_ending_tasks(self) -> list[ModelExecutionTask]:
        """Get a list of all DAG sinks.

        Returns:
            list[ModelExecutionTask]: List of all DAG sinks.
        """
        return self._extract_by_keys(self._ending_task_names)

    def _extract_by_keys(self, keys: Iterable[str]) -> list[ModelExecutionTask]:
        tasks = []
        for key in keys:
            tasks.append(self._tasks[key])
        return tasks
