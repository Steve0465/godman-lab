"""
AT&T Bill Importer

Uses ATTBillingAPI to:
- fetch bill activity history
- extract bill IDs
- download bill PDFs
- place them in the tax inbox directory
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

from libs.att_billing_api import ATTBillingAPI

logger = logging.getLogger(__name__)


def import_att_bills(inbox_dir: str = "data/tax/inbox/att") -> Dict[str, Any]:
    """
    Import AT&T bills into the tax inbox.

    Steps:
    - Fetch activity history (REAL bill list endpoint)
    - Extract bill IDs
    - Download PDFs
    - Save into inbox_dir
    """
    logger.info(f"Importing AT&T bills to: {inbox_dir}")

    # Ensure inbox directory exists
    inbox_path = Path(inbox_dir)
    inbox_path.mkdir(parents=True, exist_ok=True)

    with ATTBillingAPI() as api:
        # 1. Fetch activity history (correct source for bills)
        logger.info("Fetching AT&T activity history…")
        activity = api.get_activity_history()

        # 2. Extract bill entries
        # AT&T returns something like:
        # { "items": [ { "billId": "...", "amount": ..., "date": ... }, … ] }
        items = activity.get("items") or activity.get("history") or []

        if not items:
            raise ValueError(
                "AT&T activity history returned no bill items. "
                "Check cookies or run scraper again."
            )

        logger.info(f"Found {len(items)} bill activity entries.")

        imported_files: List[str] = []
        total_amount = 0.0

        # 3. Loop over bill entries
        for entry in items:
            bill_id = entry.get("billId") or entry.get("bill_id")
            amount = entry.get("amount") or 0.0

            if not bill_id:
                logger.warning(f"Skipping malformed entry (no bill_id): {entry}")
                continue

            logger.info(f"Processing bill_id: {bill_id}")

            # Download PDF
            try:
                pdf_path = api.download_bill_pdf(bill_id, out_dir=inbox_dir)
                imported_files.append(str(pdf_path))
                total_amount += float(amount)
            except Exception as e:
                logger.error(f"Failed to process bill {bill_id}: {e}")

        summary = {
            "count": len(imported_files),
            "total_amount": total_amount,
            "files": imported_files,
            "inbox_dir": str(inbox_path)
        }

        logger.info(f"Imported {summary['count']} bills.")
        return summary
 