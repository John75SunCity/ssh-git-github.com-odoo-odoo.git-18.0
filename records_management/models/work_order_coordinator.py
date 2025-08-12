# -*- coding: utf-8 -*-
"""
Work Order Integration Coordinator Module

This module provides seamless integration between all work order types:
- Container Retrieval Work Orders
- File Retrieval Work Orders  
- Scan Retrieval Work Orders
- Container Destruction Work Orders
- Container Access Work Orders

Key Integration Features:
- Cross-work order dependencies and workflows
- Shared resource coordination (vehicles, staff, equipment)
- Customer portal unified interface
- FSM integration for all work order types
- Billing consolidation across multiple work orders
- Chain of custody across different work order types
- Priority and scheduling optimization

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WorkOrderCoordinator(models.Model):
    """Central coordination for all work order types"""
    _name = "work.order.coordinator"
    _description = "Work Order Integration Coordinator"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "priority desc, scheduled_date asc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION
    # ============================================================================
    name = fields.Char(
        string="Coordination Number",
        required=True,
        tracking=True,
        index=True,
        copy=False,
        default=lambda self: _("New"),
        help="Unique coordination reference number"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        help="Customer for coordinated work orders"
    )

    # ============================================================================
    # WORK ORDER RELATIONSHIPS
    # ============================================================================
    container_retrieval_ids = fields.One2many(
        "container.retrieval.work.order",
        "coordinator_id",
        string="Container Retrievals"
    )
    file_retrieval_ids = fields.One2many(
        "file.retrieval.work.order", 
        "coordinator_id",
        string="File Retrievals"
    )
    scan_retrieval_ids = fields.One2many(
        "scan.retrieval.work.order",
        "coordinator_id", 
        string="Scan Retrievals"
    )
    destruction_ids = fields.One2many(
        "container.destruction.work.order",
        "coordinator_id",
        string="Destructions"
    )
    access_ids = fields.One2many(
        "container.access.work.order",
        "coordinator_id",
        string="Access Sessions"
    )

    # ============================================================================
    # COORDINATION METRICS
    # ============================================================================
    total_work_orders = fields.Integer(
        string="Total Work Orders",
        compute="_compute_coordination_metrics",
        store=True
    )
    completed_work_orders = fields.Integer(
        string="Completed",
        compute="_compute_coordination_metrics", 
        store=True
    )
    coordination_progress = fields.Float(
        string="Progress %",
        compute="_compute_coordination_metrics",
        store=True
    )

    # ============================================================================
    # SCHEDULING AND RESOURCE COORDINATION
    # ============================================================================
    scheduled_date = fields.Datetime(
        string="Coordinated Start Date",
        required=True,
        tracking=True
    )
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'), 
        ('2', 'High'),
        ('3', 'Urgent'),
        ('4', 'Emergency'),
    ], string='Priority', default='1', tracking=True)

    coordination_type = fields.Selection([
        ('sequential', 'Sequential (One after another)'),
        ('parallel', 'Parallel (Simultaneous)'), 
        ('mixed', 'Mixed (Some parallel, some sequential)'),
    ], string='Coordination Type', default='sequential', required=True)

    # ============================================================================
    # SHARED RESOURCES
    # ============================================================================
    vehicle_ids = fields.Many2many(
        "fleet.vehicle",
        string="Shared Vehicles",
        help="Vehicles available for all work orders"
    )
    employee_ids = fields.Many2many(
        "hr.employee", 
        string="Assigned Team",
        help="Staff members assigned to coordinated work orders"
    )

    # ============================================================================
    # FSM INTEGRATION
    # ============================================================================
    fsm_project_id = fields.Many2one(
        "project.project",
        string="FSM Project",
        help="Field service project for coordinated work orders"
    )
    fsm_task_ids = fields.One2many(
        "project.task",
        "work_order_coordinator_id",
        string="FSM Tasks"
    )

    # ============================================================================
    # PORTAL AND CUSTOMER INTERFACE
    # ============================================================================
    portal_request_id = fields.Many2one(
        "portal.request", 
        string="Originating Portal Request",
        help="Portal request that initiated coordination"
    )
    customer_visible = fields.Boolean(
        string="Visible in Customer Portal",
        default=True,
        help="Customer can view coordination status in portal"
    )
    
    # ============================================================================
    # BILLING COORDINATION
    # ============================================================================
    consolidated_billing = fields.Boolean(
        string="Consolidated Billing",
        default=True,
        help="Create single invoice for all work orders"
    )
    invoice_id = fields.Many2one(
        "account.move",
        string="Consolidated Invoice",
        help="Single invoice for all coordinated work orders"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity", 
        "res_id", 
        string="Activities",
        domain=lambda self: [('res_model', '=', self._name)]
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [('res_model', '=', self._name)]
    )
    message_ids = fields.One2many(
        "mail.message", 
        "res_id", 
        string="Messages",
        domain=lambda self: [('res_model', '=', self._name)]
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'work.order.coordinator') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('container_retrieval_ids', 'file_retrieval_ids', 'scan_retrieval_ids',
                 'destruction_ids', 'access_ids')
    def _compute_coordination_metrics(self):
        for record in self:
            all_orders = (record.container_retrieval_ids + 
                         record.file_retrieval_ids +
                         record.scan_retrieval_ids + 
                         record.destruction_ids +
                         record.access_ids)
            
            record.total_work_orders = len(all_orders)
            
            completed = all_orders.filtered(
                lambda wo: wo.state in ['completed', 'closed', 'done'])
            record.completed_work_orders = len(completed)
            
            if record.total_work_orders > 0:
                record.coordination_progress = (
                    record.completed_work_orders / record.total_work_orders * 100)
            else:
                record.coordination_progress = 0.0

    # ============================================================================
    # INTEGRATION ACTION METHODS
    # ============================================================================
    def action_coordinate_all(self):
        """Start coordination of all work orders"""
        self.ensure_one()
        
        # Update all work orders with shared resources
        all_orders = self._get_all_work_orders()
        
        for order in all_orders:
            if hasattr(order, 'coordinator_id'):
                order.coordinator_id = self.id
            if hasattr(order, 'vehicle_ids') and self.vehicle_ids:
                order.vehicle_ids = [(6, 0, self.vehicle_ids.ids)]
            if hasattr(order, 'employee_ids') and self.employee_ids:
                order.employee_ids = [(6, 0, self.employee_ids.ids)]
        
        self.message_post(
            body=_("Coordination started for %s work orders", len(all_orders))
        )

    def action_create_fsm_tasks(self):
        """Create FSM tasks for all work orders"""
        self.ensure_one()
        
        if not self.fsm_project_id:
            # Create FSM project if not exists
            project_vals = {
                'name': _("Records Management - %s", self.partner_id.name),
                'is_fsm': True,
                'partner_id': self.partner_id.id,
                'allow_timesheets': True,
            }
            self.fsm_project_id = self.env['project.project'].create(project_vals)
        
        # Create FSM tasks for each work order type
        task_count = 0
        for order in self._get_all_work_orders():
            if hasattr(order, 'create_fsm_task'):
                order.create_fsm_task(self.fsm_project_id.id)
                task_count += 1
        
        self.message_post(
            body=_("Created %s FSM tasks for coordinated work orders", task_count)
        )

    def action_consolidate_billing(self):
        """Create consolidated invoice for all work orders"""
        self.ensure_one()
        
        if not self.consolidated_billing:
            raise UserError(_("Consolidated billing is not enabled"))
        
        if self.invoice_id:
            raise UserError(_("Consolidated invoice already exists"))
        
        # Create invoice
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'ref': self.name,
        }
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Add invoice lines from all work orders
        line_count = 0
        for order in self._get_all_work_orders():
            if hasattr(order, 'create_invoice_lines'):
                lines = order.create_invoice_lines(invoice.id)
                line_count += len(lines)
        
        self.invoice_id = invoice.id
        self.message_post(
            body=_("Consolidated invoice created with %s lines", line_count)
        )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def _get_all_work_orders(self):
        """Get all work orders managed by this coordinator"""
        return (self.container_retrieval_ids + 
                self.file_retrieval_ids +
                self.scan_retrieval_ids + 
                self.destruction_ids +
                self.access_ids)

    def get_next_available_slot(self, duration_hours=2):
        """Find next available time slot considering all work orders"""
        self.ensure_one()
        
        # Logic to find optimal scheduling slot
        base_date = self.scheduled_date or fields.Datetime.now()
        
        if self.coordination_type == 'sequential':
            # Sequential: each starts after previous completes
            current_date = base_date
            for order in self._get_all_work_orders().sorted('priority', reverse=True):
                order.scheduled_date = current_date
                if hasattr(order, 'estimated_duration_hours'):
                    current_date += timedelta(hours=order.estimated_duration_hours or 2)
                else:
                    current_date += timedelta(hours=duration_hours)
        
        elif self.coordination_type == 'parallel':
            # Parallel: all start at same time
            for order in self._get_all_work_orders():
                order.scheduled_date = base_date
        
        # Mixed coordination handled case by case

    def create_customer_notification(self):
        """Create customer notification for coordination status"""
        self.ensure_one()
        
        # Create portal notification or email
        template = self.env.ref('records_management.email_template_work_order_coordination', 
                               raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)


class WorkOrderIntegrationMixin(models.AbstractModel):
    """Mixin to add integration capabilities to all work order models"""
    _name = 'work.order.integration.mixin'
    _description = 'Work Order Integration Capabilities'

    # ============================================================================
    # INTEGRATION FIELDS
    # ============================================================================
    coordinator_id = fields.Many2one(
        "work.order.coordinator",
        string="Coordinator",
        help="Work order coordination manager"
    )
    
    # Related work orders (for dependencies)
    prerequisite_work_order_ids = fields.Many2many(
        "work.order.coordinator",
        "work_order_prerequisite_rel",
        "work_order_id", 
        "prerequisite_id",
        string="Prerequisite Work Orders",
        help="Work orders that must complete before this one"
    )
    
    # FSM Integration
    fsm_task_id = fields.Many2one(
        "project.task",
        string="FSM Task",
        help="Related field service management task"
    )
    
    # Portal integration  
    portal_visible = fields.Boolean(
        string="Visible in Portal",
        default=True,
        help="Customer can view this work order in portal"
    )
    
    # Billing integration
    invoice_line_ids = fields.One2many(
        "account.move.line",
        "work_order_id",
        string="Invoice Lines"
    )

    # ============================================================================
    # INTEGRATION METHODS
    # ============================================================================
    def create_fsm_task(self, project_id=None):
        """Create FSM task for this work order"""
        if self.fsm_task_id:
            return self.fsm_task_id
        
        if not project_id and self.coordinator_id:
            project_id = self.coordinator_id.fsm_project_id.id
        
        if not project_id:
            # Create default FSM project
            project = self.env['project.project'].create({
                'name': _("Records Management - %s", self.partner_id.name),
                'is_fsm': True,
                'partner_id': self.partner_id.id,
            })
            project_id = project.id
        
        task_vals = {
            'name': _("%s: %s", self._description, self.display_name or self.name),
            'project_id': project_id,
            'partner_id': self.partner_id.id,
            'planned_date_begin': self.scheduled_date or fields.Datetime.now(),
            'description': getattr(self, 'description', ''),
        }
        
        task = self.env['project.task'].create(task_vals)
        self.fsm_task_id = task.id
        
        return task

    def create_invoice_lines(self, invoice_id):
        """Create invoice lines for this work order"""
        lines = []
        
        # Get billing rates based on work order type
        if hasattr(self, '_get_billing_lines'):
            billing_lines = self._get_billing_lines()
            for line_vals in billing_lines:
                line_vals.update({
                    'move_id': invoice_id,
                    'work_order_id': self.id,
                })
                line = self.env['account.move.line'].create(line_vals)
                lines.append(line)
        
        return lines

    def _check_prerequisites(self):
        """Check if prerequisite work orders are completed"""
        for prereq in self.prerequisite_work_order_ids:
            if prereq.state not in ['completed', 'done', 'closed']:
                raise UserError(
                    _("Cannot start %s until prerequisite work order %s is completed", 
                      self.display_name, prereq.name)
                )

    def notify_customer_update(self):
        """Send customer notification about work order update"""
        if self.portal_visible and self.partner_id:
            # Send portal notification
            self.message_notify(
                partner_ids=self.partner_id.ids,
                subject=_("Update: %s", self.display_name),
                body=_('Your work order %s has been updated. Status: %s', 
                       self.display_name, self.state)
            )
