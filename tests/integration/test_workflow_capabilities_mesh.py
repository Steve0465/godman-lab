from godman_ai.capabilities.registry import CapabilityMetadata, CapabilityRegistry, CapabilityType
from godman_ai.capabilities.graph import CapabilityGraph
from godman_ai.workflows.engine import Step, Workflow
from godman_ai.workflows.distributed_engine import DistributedWorkflowRunner


def test_workflow_records_capability_usage():
    registry = CapabilityRegistry()
    graph = CapabilityGraph()
    cap = CapabilityMetadata(id="wf_cap", type=CapabilityType.WORKFLOW_TEMPLATE, name="wf", description="d")
    registry.register_capability(cap)
    graph.add_capability_node(cap)
    wf = Workflow([Step("ok", lambda ctx: "done")])
    runner = DistributedWorkflowRunner()
    run_id = runner.submit_workflow(wf, {}, distributed=True)
    assert isinstance(run_id, str)
