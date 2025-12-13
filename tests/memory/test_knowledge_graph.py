from godman_ai.memory.graph import GraphEdge, GraphNode, KnowledgeGraph


def test_add_nodes_edges_and_neighbors():
    kg = KnowledgeGraph()
    node_a = GraphNode(id="a", type="WORKFLOW")
    node_b = GraphNode(id="b", type="STEP")
    kg.add_node(node_a)
    kg.add_node(node_b)
    kg.add_edge(GraphEdge(src_id="a", dst_id="b", relation_type="HAS_STEP"))
    neighbors = kg.neighbors("a")
    assert neighbors and neighbors[0].id == "b"


def test_find_paths():
    kg = KnowledgeGraph()
    kg.add_node(GraphNode(id="1", type="A"))
    kg.add_node(GraphNode(id="2", type="B"))
    kg.add_node(GraphNode(id="3", type="C"))
    kg.add_edge(GraphEdge(src_id="1", dst_id="2", relation_type="LINK"))
    kg.add_edge(GraphEdge(src_id="2", dst_id="3", relation_type="LINK"))
    paths = kg.find_paths("1", "3", max_depth=3)
    assert ["1", "2", "3"] in paths
