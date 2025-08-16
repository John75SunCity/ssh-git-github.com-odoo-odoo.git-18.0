# -*- coding: utf-8 -*-
"""
Project Task Extensions for Work Order Integration

This module extends the core project.task model to support FSM integration with work orders,
container management, and records management operations with full NAID compliance tracking.

Key Features:
- Work order coordination and tracking
- Container and document retrieval workflows
- FSM integration for field service operations
- NAID compliance audit trail integration
- Legacy records management compatibility

Business Processes:
1. Work Order Integration: Link project tasks with various work order types
2. Container Operations: Track container retrieval and access operations
3. Field Service Management: Coordinate field operations with project workflows
4. Audit Trail: Maintain NAID compliance throughout task lifecycle
5. Status Synchronization: Keep work orders and tasks synchronized

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


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
        tracking=True,
        help="Work order coordinator managing this task"
    )

    work_order_type = fields.Selection([
        ('container_retrieval', 'Container Retrieval'),
        ('file_retrieval', 'File Retrieval'),
        ('scan_retrieval', 'Scan Retrieval'),
        ('container_destruction', 'Container Destruction'),
        ('container_access', 'Container Access'),
        ('pickup_delivery', 'Pickup & Delivery'),
        ('audit_inspection', 'Audit Inspection'),
    ], string='Work Order Type',
       tracking=True,
       help="Type of work order related to this task")

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
        tracking=True,
        help="Direct reference to the related work order"
    )

    work_order_priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Work Order Priority',
       default='normal',
       tracking=True,
       help="Priority level for work order execution")

    # ============================================================================
    # RECORDS MANAGEMENT FIELDS
    # ============================================================================
    container_id = fields.Many2one(
        "records.container",
        string="Related Container",
        tracking=True,
        help="Container associated with this task"
    )

    container_ids = fields.Many2many(
        "records.container",
        "project_task_container_rel",
        "task_id",
        "container_id",
        string="Multiple Containers",
        help="Multiple containers associated with this task"
    )

    pickup_request_id = fields.Many2one(
        "pickup.request",
        string="Pickup Request",
        tracking=True,
        help="The pickup request that generated this task"
    )

    task_type = fields.Selection([
        ("pickup", "Pickup"),
        ("delivery", "Delivery"),
        ("destruction", "Destruction"),
        ("storage", "Storage"),
        ("retrieval", "Document Retrieval"),
        ("audit", "Audit Task"),
        ("maintenance", "Maintenance"),
        ("scanning", "Document Scanning"),
        ("indexing", "Document Indexing"),
        ("inspection", "Container Inspection"),
    ], string="Records Task Type",
       tracking=True,
       help="Specific type of records management task")

    # ============================================================================
    # SCHEDULING AND LOGISTICS FIELDS
    # ============================================================================
    scheduled_start_time = fields.Datetime(
        string="Scheduled Start Time",
        help="Planned start time for the task"
    )

    scheduled_end_time = fields.Datetime(
        string="Scheduled End Time",
        help="Planned completion time for the task"
    )

    actual_start_time = fields.Datetime(
        string="Actual Start Time",
        help="Actual time the task was started"
    )

    actual_end_time = fields.Datetime(
        string="Actual End Time",
        help="Actual time the task was completed"
    )

    route_id = fields.Many2one(
        "pickup.route",
        string="Pickup Route",
        help="Route associated with this task"
    )

    vehicle_id = fields.Many2one(
        "records.vehicle",
        string="Assigned Vehicle",
        help="Vehicle assigned for this task"
    )

    # ============================================================================
    # COMPLIANCE AND AUDIT FIELDS
    # ============================================================================
    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=True,
        help="Whether this task requires NAID compliance"
    )

    audit_trail_ids = fields.One2many(
        "naid.audit.log",
        "task_id",
        string="Audit Trail",
        help="NAID audit trail entries for this task"
    )

    certificate_required = fields.Boolean(
        string="Certificate Required",
        compute="_compute_certificate_required",
        store=True,
        help="Whether completion certificate is required"
    )

    # ============================================================================
    # STATUS AND PROGRESS FIELDS
    # ============================================================================
    work_order_status = fields.Selection([
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ], string='Work Order Status',
       default='pending',
       tracking=True,
       help="Current status of the work order")

    completion_notes = fields.Text(
        string="Completion Notes",
        help="Notes about task completion and any issues encountered"
    )

    quality_check_passed = fields.Boolean(
        string="Quality Check Passed",
        help="Whether the completed task passed quality checks"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('task_type', 'work_order_type')
    def _compute_certificate_required(self):
        """Determine if completion certificate is required"""
        for record in self:
            certificate_types = ['destruction', 'container_destruction', 'audit_inspection']
            record.certificate_required = (
                record.task_type in ['destruction', 'audit'] or
                record.work_order_type in certificate_types
            )

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('work_order_reference')
    def _onchange_work_order_reference(self):
        """Update task details based on work order"""
        if self.work_order_reference:
            # Set work order type based on reference model
            model_type_mapping = {
                'container.retrieval.work.order': 'container_retrieval',
                'file.retrieval.work.order': 'file_retrieval',
                'scan.retrieval.work.order': 'scan_retrieval',
                'container.destruction.work.order': 'container_destruction',
                'container.access.work.order': 'container_access',
            }

            model_name = self.work_order_reference._name
            if model_name in model_type_mapping:
                self.work_order_type = model_type_mapping[model_name]

            # Copy relevant fields from work order
            if hasattr(self.work_order_reference, 'container_id'):
                self.container_id = self.work_order_reference.container_id

            if hasattr(self.work_order_reference, 'priority'):
                self.work_order_priority = self.work_order_reference.priority

    @api.onchange('container_id')
    def _onchange_container_id(self):
        """Update task name and partner based on container"""
        if self.container_id:
            if not self.name or self.name == "New":
                self.name = _("Task for Container %s", self.container_id.name)

            if self.container_id.partner_id and not self.partner_id:
                self.partner_id = self.container_id.partner_id

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_related_container(self):
        """Action to open the related container's form view"""
        self.ensure_one()
        if not self.container_id:
            raise UserError(_("No container is associated with this task."))

        return {
            "type": "ir.actions.act_window",
            "res_model": "records.container",
            "view_mode": "form",
            "res_id": self.container_id.id,
            "target": "current",
            "context": {"default_task_id": self.id}
        }

    def action_view_work_order(self):
        """Action to open the related work order's form view"""
        self.ensure_one()
        if not self.work_order_reference:
            raise UserError(_("No work order is associated with this task."))

        return {
            "type": "ir.actions.act_window",
            "res_model": self.work_order_reference._name,
            "view_mode": "form",
            "res_id": self.work_order_reference.id,
            "target": "current",
            "context": {"default_task_id": self.id}
        }

    def action_sync_with_work_order(self):
        """Sync task status with related work order"""
        self.ensure_one()
        if not self.work_order_reference:
            raise UserError(_("No work order to sync with."))

        # Update work order based on task status
        if self.stage_id.is_closed:
            if hasattr(self.work_order_reference, 'state'):
                if self.work_order_reference.state not in ['completed', 'done', 'cancelled']:
                    self.work_order_reference.write({
                        'state': 'completed',
                        'completion_date': fields.Datetime.now()
                    })
                    self.message_post(
                        body=_("Work order synchronized and marked as completed")
                    )

        return True

    def action_start_task(self):
        """Start the task execution"""
        self.ensure_one()
        if self.work_order_status != 'assigned':
            raise UserError(_("Task must be assigned before it can be started."))

        self.write({
            'work_order_status': 'in_progress',
            'actual_start_time': fields.Datetime.now()
        })

        # Create audit log entry
        self._create_audit_log('task_started')

        self.message_post(body=_("Task started by %s", self.env.user.name))
        return True

    def action_complete_task(self):
        """Complete the task"""
        self.ensure_one()
        if self.work_order_status != 'in_progress':
            raise UserError(_("Task must be in progress to be completed."))

        self.write({
            'work_order_status': 'completed',
            'actual_end_time': fields.Datetime.now()
        })

        # Sync with work order if exists
        if self.work_order_reference:
            self.action_sync_with_work_order()

        # Create audit log entry
        self._create_audit_log('task_completed')

        self.message_post(body=_("Task completed by %s", self.env.user.name))

        # Generate certificate if required
        if self.certificate_required:
            self._generate_completion_certificate()

        return True

    def action_cancel_task(self):
        """Cancel the task"""
        self.ensure_one()

        self.write({
            'work_order_status': 'cancelled',
            'actual_end_time': fields.Datetime.now()
        })

        # Create audit log entry
        self._create_audit_log('task_cancelled')

        self.message_post(body=_("Task cancelled by %s", self.env.user.name))
        return True

    def action_assign_to_route(self):
        """Assign task to pickup route"""
        self.ensure_one()

        # Find available routes
        domain = [
            ('state', '=', 'draft'),
            ('date', '>=', fields.Date.today())
        ]

        routes = self.env['pickup.route'].search(domain)
        if not routes:
            raise UserError(_("No available routes found for assignment."))

        # Open wizard to select route
        return {
            'type': 'ir.actions.act_window',
            'name': _('Assign to Route'),
            'res_model': 'route.assignment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
                'default_available_route_ids': routes.ids
            }
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _create_audit_log(self, event_type):
        """Create NAID audit log entry"""
        if not self.naid_compliant:
            return

        self.env['naid.audit.log'].create({
            'event_type': event_type,
            'description': _("Task %s: %s", self.name, event_type.replace('_', ' ').title()),
            'user_id': self.env.user.id,
            'task_id': self.id,
            'container_id': self.container_id.id if self.container_id else False,
        })

    def _generate_completion_certificate(self):
        """Generate completion certificate for the task"""
        certificate_vals = {
            'name': _("Completion Certificate - %s", self.name),
            'task_id': self.id,
            'container_id': self.container_id.id if self.container_id else False,
            'completion_date': self.actual_end_time or fields.Datetime.now(),
            'technician_id': self.user_id.id,
            'notes': self.completion_notes or '',
        }

        certificate = self.env['task.completion.certificate'].create(certificate_vals)

        self.message_post(
            body=_("Completion certificate generated: %s", certificate.name),
            attachments=[certificate._generate_pdf_attachment()]
        )

        return certificate

    def get_task_summary(self):
        """Get task summary for reporting"""
        self.ensure_one()
        return {
            'task_name': self.name,
            'task_type': self.task_type,
            'work_order_type': self.work_order_type,
            'status': self.work_order_status,
            'assigned_user': self.user_id.name if self.user_id else '',
            'container': self.container_id.name if self.container_id else '',
            'partner': self.partner_id.name if self.partner_id else '',
            'scheduled_date': self.date_deadline,
            'completion_date': self.actual_end_time,
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('scheduled_start_time', 'scheduled_end_time')
    def _check_scheduled_times(self):
        """Validate scheduled times"""
        for record in self:
            if record.scheduled_start_time and record.scheduled_end_time:
                if record.scheduled_start_time >= record.scheduled_end_time:
                    raise ValidationError(_("Scheduled start time must be before end time."))

    @api.constrains('actual_start_time', 'actual_end_time')
    def _check_actual_times(self):
        """Validate actual times"""
        for record in self:
            if record.actual_start_time and record.actual_end_time:
                if record.actual_start_time >= record.actual_end_time:
                    raise ValidationError(_("Actual start time must be before end time."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set up task relationships"""
        tasks = super().create(vals_list)

        for task in tasks:
            # Create initial audit log if NAID compliant
            if task.naid_compliant:
                task._create_audit_log('task_created')

            # Update work order reference if needed
            if task.work_order_reference and hasattr(task.work_order_reference, 'task_id'):
                task.work_order_reference.task_id = task.id

        return tasks

    def write(self, vals):
        """Override write to track important changes"""
        result = super().write(vals)

        # Track status changes
        if 'work_order_status' in vals:
            for record in self:
                if record.naid_compliant:
                    record._create_audit_log(f'status_changed_to_{vals["work_order_status"]}')

        return result

    def unlink(self):
        """Override unlink to prevent deletion of active tasks"""
        for task in self:
            if task.work_order_status == 'in_progress':
                raise UserError(_("Cannot delete tasks that are in progress."))

            if task.naid_compliant and task.audit_trail_ids:
                raise UserError(_("Cannot delete tasks with audit trail entries."))

        return super().unlink()

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.name
            if record.task_type:
                name = f"[{record.task_type.upper()}] {name}"
            if record.container_id:
                name += f" - {record.container_id.name}"
            result.append((record.id, name))
        return result

    @api.model
    def get_task_statistics(self):
        """Get task statistics for dashboard"""
        domain_base = [('project_id.is_fsm', '=', True)]

        return {
            'total_tasks': self.search_count(domain_base),
            'pending_tasks': self.search_count(domain_base + [('work_order_status', '=', 'pending')]),
            'in_progress_tasks': self.search_count(domain_base + [('work_order_status', '=', 'in_progress')]),
            'completed_today': self.search_count(domain_base + [
                ('work_order_status', '=', 'completed'),
                ('actual_end_time', '>=', fields.Date.today())
            ]),
            'overdue_tasks': self.search_count(domain_base + [
                ('date_deadline', '<', fields.Date.today()),
                ('work_order_status', 'not in', ['completed', 'cancelled'])
            ]),
        }
