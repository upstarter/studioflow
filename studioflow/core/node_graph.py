"""
Simplified node graph for composable video processing
Clean, functional, and extensible
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import json


class NodeType(Enum):
    """Node categories"""
    INPUT = "input"
    OUTPUT = "output"
    EFFECT = "effect"
    TRANSFORM = "transform"
    COMPOSITE = "composite"
    AUDIO = "audio"
    GENERATOR = "generator"


@dataclass
class Port:
    """Connection point on a node"""
    name: str
    type: str  # "video", "audio", "data"
    direction: str  # "input" or "output"
    optional: bool = False
    value: Any = None


@dataclass
class Node:
    """Single processing node"""
    id: str
    type: NodeType
    name: str
    inputs: Dict[str, Port] = field(default_factory=dict)
    outputs: Dict[str, Port] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    process_func: Optional[Callable] = None


@dataclass
class Connection:
    """Connection between nodes"""
    from_node: str
    from_port: str
    to_node: str
    to_port: str


class NodeGraph:
    """Simplified node-based processing graph"""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.connections: List[Connection] = []
        self.execution_order: List[str] = []

    def add_node(self, node: Node) -> None:
        """Add node to graph"""
        self.nodes[node.id] = node
        self._update_execution_order()

    def connect(self, from_node: str, from_port: str,
               to_node: str, to_port: str) -> bool:
        """Connect two nodes"""

        # Validate connection
        if from_node not in self.nodes or to_node not in self.nodes:
            return False

        # Check ports exist
        if (from_port not in self.nodes[from_node].outputs or
            to_port not in self.nodes[to_node].inputs):
            return False

        # Add connection
        self.connections.append(Connection(
            from_node, from_port, to_node, to_port
        ))

        self._update_execution_order()
        return True

    def _update_execution_order(self):
        """Calculate execution order (topological sort)"""

        # Build adjacency list
        graph = {node_id: [] for node_id in self.nodes}
        in_degree = {node_id: 0 for node_id in self.nodes}

        for conn in self.connections:
            graph[conn.from_node].append(conn.to_node)
            in_degree[conn.to_node] += 1

        # Find nodes with no inputs
        queue = [node for node, degree in in_degree.items() if degree == 0]
        order = []

        while queue:
            node = queue.pop(0)
            order.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        self.execution_order = order

    def execute(self) -> Any:
        """Execute the graph"""

        results = {}

        for node_id in self.execution_order:
            node = self.nodes[node_id]

            # Gather inputs
            inputs = {}
            for conn in self.connections:
                if conn.to_node == node_id:
                    from_node = self.nodes[conn.from_node]
                    if conn.from_node in results:
                        inputs[conn.to_port] = results[conn.from_node].get(conn.from_port)

            # Execute node
            if node.process_func:
                results[node_id] = node.process_func(inputs, node.params)
            else:
                results[node_id] = self._default_process(node, inputs)

        return results

    def _default_process(self, node: Node, inputs: Dict) -> Dict:
        """Default processing for built-in nodes"""

        if node.type == NodeType.INPUT:
            return {"output": node.params.get("path")}

        elif node.type == NodeType.EFFECT:
            # Apply effect using FFmpeg
            from .ffmpeg import FFmpegProcessor
            from .simple_effects import SimpleEffects

            input_file = inputs.get("input")
            if input_file and node.name in ["fade_in", "fade_out", "blur"]:
                output = Path(f"/tmp/{node.id}.mp4")
                result = SimpleEffects.apply_effect(
                    Path(input_file), node.name, output, node.params
                )
                return {"output": str(output) if result.success else None}

        return {"output": None}

    def save(self, path: Path) -> None:
        """Save graph to JSON"""

        data = {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "name": n.name,
                    "params": n.params,
                    "inputs": {k: {"name": p.name, "type": p.type}
                              for k, p in n.inputs.items()},
                    "outputs": {k: {"name": p.name, "type": p.type}
                               for k, p in n.outputs.items()}
                }
                for n in self.nodes.values()
            ],
            "connections": [
                {
                    "from_node": c.from_node,
                    "from_port": c.from_port,
                    "to_node": c.to_node,
                    "to_port": c.to_port
                }
                for c in self.connections
            ]
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "NodeGraph":
        """Load graph from JSON"""

        graph = cls()

        with open(path) as f:
            data = json.load(f)

        # Recreate nodes
        for node_data in data["nodes"]:
            node = Node(
                id=node_data["id"],
                type=NodeType(node_data["type"]),
                name=node_data["name"],
                params=node_data.get("params", {})
            )

            # Add ports
            for port_name, port_data in node_data.get("inputs", {}).items():
                node.inputs[port_name] = Port(
                    name=port_data["name"],
                    type=port_data["type"],
                    direction="input"
                )

            for port_name, port_data in node_data.get("outputs", {}).items():
                node.outputs[port_name] = Port(
                    name=port_data["name"],
                    type=port_data["type"],
                    direction="output"
                )

            graph.add_node(node)

        # Recreate connections
        for conn_data in data["connections"]:
            graph.connect(
                conn_data["from_node"],
                conn_data["from_port"],
                conn_data["to_node"],
                conn_data["to_port"]
            )

        return graph


class NodeLibrary:
    """Library of reusable nodes"""

    @staticmethod
    def input_node(file_path: Path) -> Node:
        """Create file input node"""
        node = Node(
            id=f"input_{file_path.stem}",
            type=NodeType.INPUT,
            name="File Input",
            params={"path": str(file_path)}
        )
        node.outputs["output"] = Port("output", "video", "output")
        return node

    @staticmethod
    def output_node(file_path: Path) -> Node:
        """Create file output node"""
        node = Node(
            id=f"output_{file_path.stem}",
            type=NodeType.OUTPUT,
            name="File Output",
            params={"path": str(file_path)}
        )
        node.inputs["input"] = Port("input", "video", "input")
        return node

    @staticmethod
    def effect_node(effect_name: str, **params) -> Node:
        """Create effect node"""
        node = Node(
            id=f"effect_{effect_name}",
            type=NodeType.EFFECT,
            name=effect_name,
            params=params
        )
        node.inputs["input"] = Port("input", "video", "input")
        node.outputs["output"] = Port("output", "video", "output")
        return node

    @staticmethod
    def composite_node(mode: str = "over") -> Node:
        """Create composite node"""
        node = Node(
            id=f"composite_{mode}",
            type=NodeType.COMPOSITE,
            name="Composite",
            params={"mode": mode}
        )
        node.inputs["background"] = Port("background", "video", "input")
        node.inputs["foreground"] = Port("foreground", "video", "input")
        node.inputs["mask"] = Port("mask", "video", "input", optional=True)
        node.outputs["output"] = Port("output", "video", "output")
        return node

    @staticmethod
    def transform_node(scale: float = 1.0, rotation: float = 0,
                      position: tuple = (0, 0)) -> Node:
        """Create transform node"""
        node = Node(
            id="transform",
            type=NodeType.TRANSFORM,
            name="Transform",
            params={"scale": scale, "rotation": rotation, "position": position}
        )
        node.inputs["input"] = Port("input", "video", "input")
        node.outputs["output"] = Port("output", "video", "output")
        return node


def create_simple_pipeline(input_file: Path, output_file: Path,
                          effects: List[str]) -> NodeGraph:
    """Create a simple linear effects pipeline"""

    graph = NodeGraph()

    # Add input node
    input_node = NodeLibrary.input_node(input_file)
    graph.add_node(input_node)

    # Add effect nodes
    prev_node = input_node.id
    for effect in effects:
        effect_node = NodeLibrary.effect_node(effect)
        graph.add_node(effect_node)
        graph.connect(prev_node, "output", effect_node.id, "input")
        prev_node = effect_node.id

    # Add output node
    output_node = NodeLibrary.output_node(output_file)
    graph.add_node(output_node)
    graph.connect(prev_node, "output", output_node.id, "input")

    return graph


def create_composite_pipeline(background: Path, foreground: Path,
                             output: Path, blend_mode: str = "over") -> NodeGraph:
    """Create a compositing pipeline"""

    graph = NodeGraph()

    # Input nodes
    bg_input = NodeLibrary.input_node(background)
    fg_input = NodeLibrary.input_node(foreground)
    graph.add_node(bg_input)
    graph.add_node(fg_input)

    # Composite node
    comp = NodeLibrary.composite_node(blend_mode)
    graph.add_node(comp)

    # Connect inputs to composite
    graph.connect(bg_input.id, "output", comp.id, "background")
    graph.connect(fg_input.id, "output", comp.id, "foreground")

    # Output node
    output_node = NodeLibrary.output_node(output)
    graph.add_node(output_node)
    graph.connect(comp.id, "output", output_node.id, "input")

    return graph