from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .graph import DbtManifestGraph


class SequentialStepsGraphFactory(ABC):
    """SequentialStepsGraphFactory is a simple workflow strategy that creates a chain of steps."""

    def __init__(self, graph: DbtManifestGraph, step_factory: StepFactory) -> None:
        """Create a new SequentialStepsGraphFactory.

        Args:
            graph (DbtManifestGraph): The graph to process.
            step_factory (StepFactory): The step factory to use.
        """
        self._graph = graph
        self._factory = step_factory
        self._init()

    def _init(self) -> None:
        self._nodes_to_process: set[str] = set()
        self._next_nodes_to_process: set[str] = set()
        self._processed_nodes: dict[str, Step] = {}
        self._processed_nodes_this_iteration: dict[str, Step] = {}

    def get_workflow(self) -> Step:
        """Process a graph.

        Raises:
            ValueError: If not all nodes were processed or no steps were created.

        Returns:
            Step: The initial step that is produced out of the graph.
        """
        self._init()
        self._nodes_to_process = set(self._graph.get_graph_sources())
        chain_step = None
        while len(self._nodes_to_process) > 0:
            parallel_step = self._factory.create_parallel_step()
            for source_node in sorted(self._nodes_to_process):
                step = self._process_node(source_node)
                parallel_step.add_step(step)
            simplified_step = parallel_step.simplify()
            if simplified_step is not None:
                if chain_step is None:
                    chain_step = self._factory.create_chain_step(simplified_step)
                else:
                    chain_step.add_step(simplified_step)
            self._processed_nodes.update(self._processed_nodes_this_iteration)
            self._nodes_to_process |= self._next_nodes_to_process
            self._nodes_to_process -= set(self._processed_nodes_this_iteration.keys())
            self._next_nodes_to_process = set()
            self._processed_nodes_this_iteration = {}

        if set(self._processed_nodes.keys()) != set(dict(self._graph.get_graph_nodes()).keys()):
            raise ValueError(
                "Not all nodes were processed: "
                f"{set(dict(self._graph.get_graph_nodes()).keys()) - set(self._processed_nodes.keys())}"
            )
        if chain_step is None:
            raise ValueError("No steps were created")
        return chain_step

    def _process_node(
        self,
        node: str,
    ) -> Step | None:
        """Process a node.

        Args:
            node (str): The node to process.

        Returns:
            Step | None: The step that is produced out of the node or None if the node is not ready to be processed.
        """
        if self._calculate_in_degree(node) <= 1:
            return self._get_step(node)
        self._next_nodes_to_process.add(node)
        return None

    def _calculate_in_degree(self, node: str) -> int:
        in_degree = int(self._graph.graph.in_degree(node))
        for predecessor in self._graph.graph.predecessors(node):
            if predecessor in self._processed_nodes:
                in_degree -= 1
        return in_degree

    def _get_step(self, node: str) -> Step:
        step = self._factory.create_single_step(node, self._graph.graph.nodes[node])
        self._processed_nodes_this_iteration[node] = step
        if self._graph.graph.out_degree(node) == 0:
            return step
        step = self._factory.create_chain_step(step)
        self._processed_nodes_this_iteration[node] = step
        if self._graph.graph.out_degree(node) == 1:
            next_step = self._process_node(next(self._graph.graph.successors(node)))
            step.add_step(next_step)
            return step
        parallel_step = self._factory.create_parallel_step()
        for next_node in self._graph.graph.successors(node):
            next_step = self._process_node(next_node)
            parallel_step.add_step(next_step)
        simplified_parallel_step = parallel_step.simplify()
        step.add_step(simplified_parallel_step)
        return step


class StepFactory(ABC):
    """StepFactory is an abstract class that defines the step creation strategy of the graph."""

    @abstractmethod
    def create_single_step(self, node: str, node_data: dict[str, Any]) -> Step:
        """Return a single step materialization.

        Args:
            node (str): The node to process.
            node_data (dict[str, Any]): The data of the node.
        """

    @abstractmethod
    def create_chain_step(self, step: Step) -> ChainStep:
        """Return a default chain step.

        Args:
            step (Step): The step to add.
        """

    @abstractmethod
    def create_parallel_step(self) -> ParallelStep:
        """Return a default parallel step."""


class Step(ABC):
    """Base abstract step class."""

    @abstractmethod
    def get_step(self) -> Any:
        """Return a step result."""


class ChainStep(Step):
    """Base chain step class."""

    def __init__(self, step: Step, next_step: ChainStep | None = None) -> None:
        """Create a new chain step.

        Args:
            step (Step): The step to add.
            next_step (ChainStep | None, optional): The next step. Defaults to None.
        """
        self._step: Step
        self._next_step: ChainStep | None
        if isinstance(step, ChainStep):
            step.add_step(next_step)
            self._step = step._step
            self._next_step = step._next_step
        else:
            self._step = step
            self._next_step = next_step

    def add_step(self, step: Step | None) -> None:
        """Add a step to the chain.

        Args:
            step (Step | None): The step to add.
        """
        if step is None:
            return
        if self._next_step is not None:
            self._next_step.add_step(step)
            return
        self._next_step = self.create_step(step)

    @classmethod
    def create_step(cls, step: Step) -> ChainStep:
        """Create a new chain step.

        Args:
            step (Step): The step to add.

        Returns:
            ChainStep: The new chain step for the provided step.
        """
        return cls(step)


class ParallelStep(Step):
    """Base parallel step class."""

    def __init__(self, steps: list[Step]) -> None:
        """Create a new parallel step.

        Args:
            steps (list[Step]): The steps to add.
        """
        self._steps = steps

    def add_step(self, step: Step | None) -> None:
        """Add a step to the parallel step.

        Args:
            step (Step | None): The step to add.
        """
        if step is None:
            return
        self._steps.append(step)

    def simplify(self) -> Step | None:
        """Simplify the parallel step.

        Returns:
            Step | None: Simplified step or None.
        """
        simplified_steps: list[Step | None] = []
        for step in self._steps:
            if isinstance(step, ParallelStep):
                simplified_steps.append(step.simplify())
            else:
                simplified_steps.append(step)
        filtered_steps = [step for step in simplified_steps if step is not None]
        if len(filtered_steps) == 0:
            return None
        if len(filtered_steps) == 1:
            return filtered_steps[0]
        return self.create_step(filtered_steps)

    @classmethod
    def create_step(cls, steps: list[Step]) -> Step:
        """Create a new parallel step.

        Args:
            steps (list[Step]): The steps to add to parallel step.

        Returns:
            Step: The new parallel step.
        """
        return cls(steps)
