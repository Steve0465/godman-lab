from godman_ai.capabilities.graph import CapabilityGraph
from godman_ai.capabilities.registry import CapabilityMetadata, CapabilityType


def test_graph_nodes_and_relations():
    graph = CapabilityGraph()
    cap1 = CapabilityMetadata(id="tool1", type=CapabilityType.TOOL, name="Tool1", description="d")
    cap2 = CapabilityMetadata(id="tool2", type=CapabilityType.TOOL, name="Tool2", description="d")
    graph.add_capability_node(cap1)
    graph.add_capability_node(cap2)
    graph.add_relationship("tool1", "tool2", "ALTERNATIVE_FOR")
    neighbors = graph.get_related_capabilities("tool1", "ALTERNATIVE_FOR")
    assert neighbors and neighbors[0].id == "tool2"
