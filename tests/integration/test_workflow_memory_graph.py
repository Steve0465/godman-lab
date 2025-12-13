from godman_ai.memory.manager import MemoryManager
from godman_ai.workflows.distributed_engine import DistributedWorkflowRunner
from godman_ai.workflows.engine import Step, Workflow


def test_workflow_records_graph():
    mm = MemoryManager()
    wf = Workflow([Step("ok", lambda ctx: "done")])
    runner = DistributedWorkflowRunner(memory_manager=mm)
    run_id = runner.submit_workflow(wf, {}, distributed=True)
    node = mm.graph.nodes.get(run_id)
    assert node is not None
