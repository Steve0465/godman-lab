"""Minimal job server facade for distributed workflows."""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional

from godman_ai.workflows.checkpoint_store import InMemoryCheckpointStore, WorkflowRun
from godman_ai.workflows.distributed_engine import DistributedWorkflowRunner
from godman_ai.workflows.dsl_loader import load_workflow_from_yaml

logger = logging.getLogger("distributed.job_server")
logger.addHandler(logging.NullHandler())


class JobServer:
    """Lightweight in-process job submission handler."""

    def __init__(self, runner: Optional[DistributedWorkflowRunner] = None) -> None:
        self.runner = runner or DistributedWorkflowRunner()

    def submit(self, workflow_path: str, context: Optional[Dict[str, Any]] = None) -> str:
        workflow = load_workflow_from_yaml(workflow_path)
        return self.runner.submit_workflow(workflow, context or {}, distributed=True)

    def status(self, workflow_id: str) -> WorkflowRun:
        return self.runner.get_run(workflow_id)

    def logs(self, workflow_id: str) -> Dict[str, Any]:
        store = getattr(self.runner, "store", None)
        if isinstance(store, InMemoryCheckpointStore):
            return {"logs": store.logs.get(workflow_id, [])}
        return {"logs": []}


def run_server(host: str = "0.0.0.0", port: int = 8080, runner: Optional[DistributedWorkflowRunner] = None) -> None:
    """Start a very small HTTP server for job submission."""
    server = JobServer(runner)

    class Handler(BaseHTTPRequestHandler):
        def _json(self, code: int, payload: Dict[str, Any]):
            body = json.dumps(payload).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):  # noqa: N802
            if self.path != "/jobs":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or "{}")
            workflow_path = data.get("workflow")
            context = data.get("context", {})
            if not workflow_path:
                self._json(400, {"error": "workflow path required"})
                return
            run_id = server.submit(workflow_path, context)
            self._json(200, {"id": run_id})

        def do_GET(self):  # noqa: N802
            if self.path.startswith("/jobs/") and self.path.endswith("/log"):
                workflow_id = self.path.split("/")[2]
                return self._json(200, server.logs(workflow_id))
            if self.path.startswith("/jobs/"):
                workflow_id = self.path.split("/")[2]
                run = server.status(workflow_id)
                return self._json(200, run.to_dict())
            self.send_error(404)

        def log_message(self, fmt, *args):  # noqa: D401
            """Silence default logging."""
            return

    httpd = HTTPServer((host, port), Handler)
    logger.info("Job server listening on %s:%s", host, port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover
        logger.info("Job server shutting down")
        httpd.server_close()
