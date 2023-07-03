from typing import Any

from dbt_graph_builder.builder import create_tasks_graph, load_dbt_manifest
from dbt_graph_builder.workflow import ChainStep, ParallelStep, Step, Workflow


class MyChainStep(ChainStep):
    def get_step(self) -> Any:
        if self._next_step is None:
            return (self._step.get_step(), None)
        return (self._step.get_step(), *self._next_step.get_step())


class MyParallelStep(ParallelStep):
    def get_step(self) -> Any:
        return [step.get_step() for step in self._steps]


class MyStep(Step):
    def __init__(self, name: str) -> None:
        self._name = name

    def get_step(self) -> Any:
        return {"name": self._name}


class MyWorkflow(Workflow):
    def get_single_step(self, node: str, node_data: dict[str, Any]) -> Step:
        return MyStep(node)

    def get_chain_step(self, step: Step) -> ChainStep:
        return MyChainStep(step)

    def get_parallel_step(self) -> ParallelStep:
        return MyParallelStep([])


def test_workflow_1():
    manifest_graph = create_tasks_graph(load_dbt_manifest("tests/unit/dbt_graph_builder/manifests/manifest_2.json"))
    assert manifest_graph.get_graph_sources() == [
        "model.dbt_test.model1",
        "model.dbt_test.model5",
        "model.dbt_test.model6",
    ]
    assert manifest_graph.get_graph_sinks() == ["model.dbt_test.model12"]
    assert list(dict(manifest_graph.get_graph_nodes()).keys()) == [
        "model.dbt_test.model1",
        "model.dbt_test.model2",
        "model.dbt_test.model3",
        "model.dbt_test.model4",
        "model.dbt_test.model5",
        "model.dbt_test.model6",
        "model.dbt_test.model7",
        "model.dbt_test.model8",
        "model.dbt_test.model9",
        "model.dbt_test.model10",
        "model.dbt_test.model11",
        "model.dbt_test.model12",
    ]
    assert list(manifest_graph.get_graph_edges()) == [
        ("model.dbt_test.model1", "model.dbt_test.model2"),
        ("model.dbt_test.model2", "model.dbt_test.model3"),
        ("model.dbt_test.model3", "model.dbt_test.model10"),
        ("model.dbt_test.model4", "model.dbt_test.model12"),
        ("model.dbt_test.model5", "model.dbt_test.model3"),
        ("model.dbt_test.model6", "model.dbt_test.model7"),
        ("model.dbt_test.model6", "model.dbt_test.model8"),
        ("model.dbt_test.model7", "model.dbt_test.model9"),
        ("model.dbt_test.model8", "model.dbt_test.model9"),
        ("model.dbt_test.model9", "model.dbt_test.model10"),
        ("model.dbt_test.model10", "model.dbt_test.model4"),
        ("model.dbt_test.model10", "model.dbt_test.model11"),
        ("model.dbt_test.model11", "model.dbt_test.model12"),
    ]

    workflow = MyWorkflow(manifest_graph)
    steps = workflow.get_workflow()
    assert steps.get_step() == (
        [
            ({"name": "model.dbt_test.model1"}, {"name": "model.dbt_test.model2"}, None),
            ({"name": "model.dbt_test.model5"}, None),
            (
                {"name": "model.dbt_test.model6"},
                [({"name": "model.dbt_test.model7"}, None), ({"name": "model.dbt_test.model8"}, None)],
                None,
            ),
        ],
        [({"name": "model.dbt_test.model3"}, None), ({"name": "model.dbt_test.model9"}, None)],
        {"name": "model.dbt_test.model10"},
        [({"name": "model.dbt_test.model4"}, None), ({"name": "model.dbt_test.model11"}, None)],
        {"name": "model.dbt_test.model12"},
        None,
    )


def test_workflow_2():
    manifest_graph = create_tasks_graph(load_dbt_manifest("tests/unit/dbt_graph_builder/manifests/manifest_3.json"))
    assert manifest_graph.get_graph_sources() == [
        "model.dbt_test.model1",
        "model.dbt_test.model6",
        "model.dbt_test.model11",
    ]
    assert manifest_graph.get_graph_sinks() == ["model.dbt_test.model5"]
    assert list(manifest_graph.get_graph_edges()) == [
        ("model.dbt_test.model1", "model.dbt_test.model2"),
        ("model.dbt_test.model2", "model.dbt_test.model3"),
        ("model.dbt_test.model3", "model.dbt_test.model4"),
        ("model.dbt_test.model4", "model.dbt_test.model5"),
        ("model.dbt_test.model6", "model.dbt_test.model7"),
        ("model.dbt_test.model7", "model.dbt_test.model8"),
        ("model.dbt_test.model7", "model.dbt_test.model9"),
        ("model.dbt_test.model8", "model.dbt_test.model3"),
        ("model.dbt_test.model9", "model.dbt_test.model10"),
        ("model.dbt_test.model10", "model.dbt_test.model5"),
        ("model.dbt_test.model11", "model.dbt_test.model12"),
        ("model.dbt_test.model12", "model.dbt_test.model9"),
    ]
    workflow = MyWorkflow(manifest_graph)
    steps = workflow.get_workflow()
    assert steps.get_step() == (
        [
            ({"name": "model.dbt_test.model1"}, {"name": "model.dbt_test.model2"}, None),
            ({"name": "model.dbt_test.model11"}, {"name": "model.dbt_test.model12"}, None),
            (
                {"name": "model.dbt_test.model6"},
                {"name": "model.dbt_test.model7"},
                {"name": "model.dbt_test.model8"},
                None,
            ),
        ],
        [
            ({"name": "model.dbt_test.model3"}, {"name": "model.dbt_test.model4"}, None),
            ({"name": "model.dbt_test.model9"}, {"name": "model.dbt_test.model10"}, None),
        ],
        {"name": "model.dbt_test.model5"},
        None,
    )
