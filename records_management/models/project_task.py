# -*- coding: utf-8 -*-
"""
Project Task Extensions for Work Order Integration

Extends project.task model to support FSM integration with work orders.
"""

from odoo import models, fields, api, _


class ProjectTask(models.Model):
    """
    Extends the core Project Task model to add fields and functionality
    for records management operations, including work order integration.
    """
    _inherit = "project.task"

    # ============================================================================
    # WORK ORDER INTEGRATION FIELDS
    # ============================================================================
    work_order_coordinator_id = fields.Many2one(
        "work.order.coordinator",
        string="Work Order Coordinator",
        help="Work order coordinator managing this task"
    )
    work_order_type = fields.Selection([
        ('container_retrieval', 'Container Retrieval'),
        ('file_retrieval', 'File Retrieval'),
        ('scan_retrieval', 'Scan Retrieval'),
        ('container_destruction', 'Container Destruction'),
        ('container_access', 'Container Access'),
    ], string='Work Order Type', help="Type of work order related to this task")

    # Reference field for direct work order links
    work_order_reference = fields.Reference(
        selection=[
            ('container.retrieval.work.order', 'Container Retrieval'),
            ('file.retrieval.work.order', 'File Retrieval'),
            ('scan.retrieval.work.order', 'Scan Retrieval'),
            ('container.destruction.work.order', 'Container Destruction'),
            ('container.access.work.order', 'Container Access'),
        ],
        string='Related Work Order',
        help="Direct reference to the related work order"
    )

    # ============================================================================
    # LEGACY RECORDS MANAGEMENT FIELDS (PRESERVED)
    # ============================================================================
    container_id = fields.Many2one(
        "records.container",
        string="Related Container",
        help="Container associated with this task.",
    )
    pickup_request_id = fields.Many2one(
        "pickup.request",
        string="Pickup Request",
        help="The pickup request that generated this task.",
    )
    task_type = fields.Selection(
        [
            ("pickup", "Pickup"),
            ("delivery", "Delivery"),
            ("destruction", "Destruction"),
            ("storage", "Storage"),
            ("retrieval", "Document Retrieval"),
            ("audit", "Audit Task"),
            ("maintenance", "Maintenance"),
        ],
        string="Records Task Type",
        help="Specific type of records management task.",
    )

    # ============================================================================
    # FIELD SETUP
    # ============================================================================
    @api.model
    def _setup_fields(self):
        super()._setup_fields()
        # Example of modifying an existing field property
        if "user_id" in self._fields:
            self._fields["user_id"].required = True

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_related_container(self):
        """Action to open the related container's form view."""
        self.ensure_one()
        if not self.container_id:
            return
        return {
            "type": "ir.actions.act_window",
            "res_model": "records.container",
            "view_mode": "form",
            "res_id": self.container_id.id,
            "target": "current",
        }

    def action_view_work_order(self):
        """Action to open the related work order's form view."""
        self.ensure_one()
        if not self.work_order_reference:
            return
        return {
            "type": "ir.actions.act_window",
            "res_model": self.work_order_reference._name,
            "view_mode": "form",
            "res_id": self.work_order_reference.id,
            "target": "current",
        }

    def action_sync_with_work_order(self):
        """Sync task status with related work order"""
        self.ensure_one()
        if self.work_order_reference:
            # Update work order based on task status
            if self.stage_id.is_closed:
                if hasattr(self.work_order_reference, 'state'):
                    if self.work_order_reference.state not in ['completed', 'done']:
                        self.work_order_reference.state = 'completed'
