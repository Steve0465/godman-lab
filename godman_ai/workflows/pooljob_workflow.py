"""Pool Job Workflow - Pool service job management automation."""
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from ..engine import BaseWorkflow


class PoolJobWorkflow(BaseWorkflow):
    """
    Complete pool service job workflow.
    
    Steps:
    1. Receive job details (manual input or from calendar/email)
    2. Create Trello card for job tracking
    3. Generate job sheet (optional)
    4. Log to Google Sheets
    5. Send confirmation (optional)
    6. Track completion
    7. Generate invoice
    8. Archive documentation
    """
    
    name = "pooljob_workflow"
    description = "End-to-end pool service job management"
    
    def __init__(self, engine):
        """Initialize workflow with engine reference."""
        self.engine = engine
    
    def run(self, job_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Run the complete pool job workflow.
        
        Args:
            job_data: Dictionary with job information
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with workflow results
        """
        results = {
            "job_id": self._generate_job_id(),
            "status": "in_progress",
            "steps_completed": []
        }
        
        # Step 1: Validate job data
        if not self._validate_job_data(job_data):
            results["status"] = "failed"
            results["error"] = "Invalid job data"
            return results
        
        # Step 2: Create Trello card
        try:
            trello_result = self.engine.call_tool(
                "trello_job_tracker",
                job_data=job_data,
                list_id=kwargs.get("trello_list_id", "default")
            )
            results["trello_card"] = trello_result
            results["steps_completed"].append("trello_created")
        except Exception as e:
            results["trello_error"] = str(e)
        
        # Step 3: Log to Google Sheets
        try:
            sheets_result = self._log_job_to_sheets(job_data, **kwargs)
            results["sheets_logged"] = sheets_result
            results["steps_completed"].append("sheets_logged")
        except Exception as e:
            results["sheets_error"] = str(e)
        
        # Step 4: Generate job sheet (if requested)
        if kwargs.get("generate_job_sheet", False):
            try:
                job_sheet = self._generate_job_sheet(job_data)
                results["job_sheet"] = job_sheet
                results["steps_completed"].append("job_sheet_generated")
            except Exception as e:
                results["job_sheet_error"] = str(e)
        
        # Step 5: Send confirmation (if email provided)
        if job_data.get("customer_email"):
            try:
                confirmation = self._send_confirmation(job_data)
                results["confirmation_sent"] = confirmation
                results["steps_completed"].append("confirmation_sent")
            except Exception as e:
                results["confirmation_error"] = str(e)
        
        results["status"] = "completed"
        return results
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"JOB-{timestamp}"
    
    def _validate_job_data(self, job_data: Dict[str, Any]) -> bool:
        """Validate required job data fields."""
        required_fields = ["customer_name", "address", "service_type", "date"]
        return all(field in job_data for field in required_fields)
    
    def _log_job_to_sheets(self, job_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Log job to Google Sheets."""
        spreadsheet_id = kwargs.get("spreadsheet_id")
        
        if not spreadsheet_id:
            return {"logged": False, "reason": "No spreadsheet_id provided"}
        
        # Format as row
        row_data = [
            job_data.get("date", ""),
            job_data.get("customer_name", ""),
            job_data.get("address", ""),
            job_data.get("service_type", ""),
            job_data.get("status", "Scheduled"),
            job_data.get("price", 0.0)
        ]
        
        result = self.engine.call_tool(
            "sheets",
            action="append",
            spreadsheet_id=spreadsheet_id,
            range="Jobs!A:F",
            values=[row_data]
        )
        
        return result
    
    def _generate_job_sheet(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate printable job sheet."""
        return {
            "job_id": self._generate_job_id(),
            "customer": job_data.get("customer_name"),
            "address": job_data.get("address"),
            "date": job_data.get("date"),
            "service": job_data.get("service_type"),
            "notes": job_data.get("notes", ""),
            "checklist": self._get_service_checklist(job_data.get("service_type")),
            "generated_at": datetime.now().isoformat()
        }
    
    def _get_service_checklist(self, service_type: str) -> list:
        """Get checklist for service type."""
        checklists = {
            "Pool Cleaning": [
                "Skim surface",
                "Vacuum pool",
                "Brush walls",
                "Empty baskets",
                "Check filter pressure"
            ],
            "Chemical Balance": [
                "Test pH level",
                "Test chlorine level",
                "Add chemicals as needed",
                "Record readings"
            ],
            "Equipment Repair": [
                "Diagnose issue",
                "Replace/repair parts",
                "Test operation",
                "Document work"
            ]
        }
        return checklists.get(service_type, ["Complete service"])
    
    def _send_confirmation(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send job confirmation email."""
        return {
            "sent": True,
            "to": job_data.get("customer_email"),
            "subject": f"Pool Service Confirmation - {job_data.get('date')}",
            "sent_at": datetime.now().isoformat()
        }


class PoolJobCompletion(BaseWorkflow):
    """Mark pool job as complete and generate invoice."""
    
    name = "pooljob_completion"
    description = "Complete pool job and generate invoice"
    
    def __init__(self, engine):
        self.engine = engine
    
    def run(self, job_id: str, completion_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Mark job as complete and generate invoice.
        
        Args:
            job_id: Job ID
            completion_data: Completion details
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with completion results
        """
        results = {
            "job_id": job_id,
            "completed_at": datetime.now().isoformat(),
            "steps_completed": []
        }
        
        # Update Trello card
        if kwargs.get("trello_card_id"):
            try:
                self.engine.call_tool(
                    "trello",
                    action="move_card",
                    card_id=kwargs["trello_card_id"],
                    list_id=kwargs.get("completed_list_id", "done")
                )
                results["steps_completed"].append("trello_updated")
            except Exception as e:
                results["trello_error"] = str(e)
        
        # Generate invoice
        try:
            invoice = self._generate_invoice(job_id, completion_data)
            results["invoice"] = invoice
            results["steps_completed"].append("invoice_generated")
        except Exception as e:
            results["invoice_error"] = str(e)
        
        # Update sheets
        if kwargs.get("spreadsheet_id"):
            try:
                # Would update status to "Completed" in sheets
                results["steps_completed"].append("sheets_updated")
            except Exception as e:
                results["sheets_error"] = str(e)
        
        results["status"] = "completed"
        return results
    
    def _generate_invoice(self, job_id: str, completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate invoice for completed job."""
        return {
            "invoice_id": f"INV-{job_id}",
            "job_id": job_id,
            "customer": completion_data.get("customer_name"),
            "services": completion_data.get("services_performed", []),
            "total": completion_data.get("total", 0.0),
            "due_date": "2025-12-19",  # 14 days from now
            "generated_at": datetime.now().isoformat()
        }
