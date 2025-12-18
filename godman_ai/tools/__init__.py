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
        receipt_ingest,
    )
    _HAS_RECEIPTS = True
except Exception:  # pragma: no cover - optional dependency path
    _HAS_RECEIPTS = False
    Receipt = OCRResult = None  # type: ignore
    def _missing(*_, **__):
        raise ImportError("Receipt tools require pandas; install optional dependencies.")
    load_receipts = append_receipt = upsert_receipts = infer_category = _missing  # type: ignore
    build_receipt_from_ocr = add_receipt_from_ocr = receipt_ingest = _missing  # type: ignore
    get_receipts_by_category = get_receipts_by_date_range = calculate_total = _missing  # type: ignore

# Optional banking import (pandas may be unavailable in minimal environments)
try:
    from .banking import (  # type: ignore
        bank_statement_ingest,
        extract_dates_from_statement,
        determine_primary_tax_year,
        ensure_bank_csv_exists,
    )
    _HAS_BANKING = True
except Exception:  # pragma: no cover - optional dependency path
    _HAS_BANKING = False
    def _banking_missing(*_, **__):
        raise ImportError("Banking tools require pandas; install optional dependencies.")
    bank_statement_ingest = extract_dates_from_statement = _banking_missing  # type: ignore
    determine_primary_tax_year = ensure_bank_csv_exists = _banking_missing  # type: ignore

# Optional Trello import
try:
    from .trello import (  # type: ignore
        FavoritesManager,
        add_part_info_to_card,
        get_card_part_comments,
    )
    _HAS_TRELLO = True
except Exception:  # pragma: no cover - optional dependency path
    _HAS_TRELLO = False
    FavoritesManager = None  # type: ignore
    def _trello_missing(*_, **__):
        raise ImportError("Trello tools require libs.trello_client; check dependencies.")
    add_part_info_to_card = get_card_part_comments = _trello_missing  # type: ignore

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
    'receipt_ingest',
    'bank_statement_ingest',
    'extract_dates_from_statement',
    'determine_primary_tax_year',
    'ensure_bank_csv_exists',
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
    'FavoritesManager',
    'add_part_info_to_card',
    'get_card_part_comments',
]
