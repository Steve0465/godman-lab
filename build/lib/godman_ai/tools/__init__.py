"""Tools module for godman_ai."""

from godman_ai.tools.base import BaseTool, ToolExecutionError, trace_tool
from godman_ai.tools.registry import (
    TOOL_REGISTRY,
    get_tool,
    initialize_mcp_tools,
    list_tools,
    register_function_tool,
    register_tool,
)
from godman_ai.tools.runner import ToolRunner
from godman_ai.tools.shell import ShellCommandTool

# Optional receipts import (pandas may be unavailable in minimal environments)
try:
    from .receipts import (  # type: ignore
        Receipt,
        OCRResult,
        load_receipts,
        append_receipt,
        upsert_receipts,
        infer_category,
        build_receipt_from_ocr,
        add_receipt_from_ocr,
        get_receipts_by_category,
        get_receipts_by_date_range,
        calculate_total,
    )
    _HAS_RECEIPTS = True
except Exception:  # pragma: no cover - optional dependency path
    _HAS_RECEIPTS = False
    Receipt = OCRResult = None  # type: ignore
    def _missing(*_, **__):
        raise ImportError("Receipt tools require pandas; install optional dependencies.")
    load_receipts = append_receipt = upsert_receipts = infer_category = _missing  # type: ignore
    build_receipt_from_ocr = add_receipt_from_ocr = _missing  # type: ignore
    get_receipts_by_category = get_receipts_by_date_range = calculate_total = _missing  # type: ignore

__all__ = [
    'Receipt',
    'OCRResult',
    'load_receipts',
    'append_receipt',
    'upsert_receipts',
    'infer_category',
    'build_receipt_from_ocr',
    'add_receipt_from_ocr',
    'get_receipts_by_category',
    'get_receipts_by_date_range',
    'calculate_total',
    'BaseTool',
    'ToolExecutionError',
    'trace_tool',
    'ShellCommandTool',
    'ToolRunner',
    'register_tool',
    'register_function_tool',
    'list_tools',
    'get_tool',
    'initialize_mcp_tools',
    'TOOL_REGISTRY',
]
