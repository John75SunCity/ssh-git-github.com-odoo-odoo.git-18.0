# -*- coding: utf-8 -*-
"""
Unified Work Order View

A virtual model that aggregates all work order types into a single
consolidated view for the dispatch center. This allows staff to see
all work orders regardless of type in one place.

Author: Records Management System
Version: 18.0.1.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class UnifiedWorkOrder(models.Model):
    """
    Virtual model that provides a consolidated view of all work order types.
    Uses SQL views to aggregate data from multiple work order models.
    """
    _name = 'unified.work.order'
    _description = 'Unified Work Order View'
    _auto = False  # This is a database view, not a regular table
    _order = 'scheduled_date desc, priority desc'
    _rec_name = 'display_name'

    # ============================================================================
    # IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Work Order #", readonly=True)
    display_name = fields.Char(string="Display Name", readonly=True)

    # The actual record reference
    source_model = fields.Char(string="Source Model", readonly=True)
    source_id = fields.Integer(string="Source ID", readonly=True)

    # Work order type categorization
    work_order_type = fields.Selection([
        # Storage Services
        ('retrieval', 'Retrieval'),
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
        ('container_access', 'Container Access'),
        # Destruction Services
        ('shredding', 'Shredding Service'),
        # Other
        ('other', 'Other'),
    ], string="Type", readonly=True)

    service_category = fields.Selection([
        ('storage', 'Storage Services'),
        ('destruction', 'Destruction Services'),
    ], string="Category", readonly=True)

    # ============================================================================
    # STATUS & PRIORITY
    # ============================================================================
    # Simplified workflow: Scheduled → In Progress → Completed → Invoiced
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    ], string="Status", readonly=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent'),
    ], string="Priority", readonly=True)

    # Color for kanban
    color = fields.Integer(string="Color", compute='_compute_color')

    # ============================================================================
    # CUSTOMER & DATES
    # ============================================================================
    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer", readonly=True)
    scheduled_date = fields.Datetime(string="Scheduled Date", readonly=True)
    completion_date = fields.Datetime(string="Completion Date", readonly=True)

    # ============================================================================
    # PORTAL & SOURCE
    # ============================================================================
    portal_request_id = fields.Many2one(comodel_name='portal.request', string="Portal Request", readonly=True)
    is_portal_order = fields.Boolean(string="From Portal", readonly=True)
    portal_visible = fields.Boolean(string="Visible in Portal", readonly=True)

    # ============================================================================
    # ASSIGNMENT
    # ============================================================================
    user_id = fields.Many2one(comodel_name='res.users', string="Assigned To", readonly=True)

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('work_order_type', 'state')
    def _compute_color(self):
        """Compute color based on type and status for kanban view."""
        type_colors = {
            'retrieval': 4,      # Light blue
            'delivery': 10,     # Green
            'pickup': 3,        # Yellow
            'container_access': 9,  # Purple
            'shredding': 2,     # Orange
        }
        for record in self:
            if record.state == 'cancelled':
                record.color = 0  # Grey
            elif record.state in ('completed', 'certified', 'invoiced'):
                record.color = 10  # Green
            elif record.state == 'in_progress':
                record.color = 3  # Yellow
            elif record.priority == '2':
                record.color = 1  # Red (urgent)
            else:
                record.color = type_colors.get(record.work_order_type, 0)

    # ============================================================================
    # DATABASE VIEW CREATION
    # ============================================================================
    def init(self):
        """Create the SQL view that unions all work order types."""
        # Drop the view if it exists
        self.env.cr.execute("DROP VIEW IF EXISTS unified_work_order CASCADE")

        # Create the unified view
        # Use numeric IDs: type_offset + source_id
        # Offsets: retrieval=1000000, shredding=2000000, destruction=3000000, access=4000000
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW unified_work_order AS (
                -- Retrieval Work Orders (IDs: 1,000,001 - 1,999,999)
                SELECT 
                    (1000000 + wo.id)::bigint AS id,
                    wo.name,
                    COALESCE(wo.name, 'Retrieval #' || wo.id::text) AS display_name,
                    'work.order.retrieval' AS source_model,
                    wo.id AS source_id,
                    'retrieval' AS work_order_type,
                    'storage' AS service_category,
                    wo.state,
                    COALESCE(wo.priority, '0') AS priority,
                    wo.partner_id,
                    wo.scheduled_date,
                    wo.completion_date,
                    wo.portal_request_id,
                    CASE WHEN wo.portal_request_id IS NOT NULL THEN true ELSE false END AS is_portal_order,
                    COALESCE(wo.portal_visible, true) AS portal_visible,
                    wo.user_id
                FROM work_order_retrieval wo
                WHERE wo.active = true OR wo.active IS NULL
                
                UNION ALL
                
                -- Shredding Work Orders (IDs: 2,000,001 - 2,999,999)
                SELECT 
                    (2000000 + wo.id)::bigint AS id,
                    wo.name,
                    COALESCE(wo.display_name, wo.name, 'Shredding #' || wo.id::text) AS display_name,
                    'work.order.shredding' AS source_model,
                    wo.id AS source_id,
                    'shredding' AS work_order_type,
                    'destruction' AS service_category,
                    wo.state,
                    COALESCE(wo.priority, '0') AS priority,
                    wo.partner_id,
                    wo.scheduled_date,
                    wo.completion_date,
                    wo.portal_request_id,
                    CASE WHEN wo.portal_request_id IS NOT NULL THEN true ELSE false END AS is_portal_order,
                    COALESCE(wo.portal_visible, true) AS portal_visible,
                    NULL::integer AS user_id
                FROM work_order_shredding wo
                WHERE wo.active = true OR wo.active IS NULL
                
                UNION ALL
                
                -- Container Access Work Orders (IDs: 4,000,001 - 4,999,999)
                SELECT 
                    (4000000 + wo.id)::bigint AS id,
                    wo.name,
                    COALESCE(wo.name, 'Access #' || wo.id::text) AS display_name,
                    'container.access.work.order' AS source_model,
                    wo.id AS source_id,
                    'container_access' AS work_order_type,
                    'storage' AS service_category,
                    wo.state,
                    COALESCE(wo.priority, '0') AS priority,
                    wo.partner_id,
                    wo.scheduled_access_date AS scheduled_date,
                    wo.actual_end_time AS completion_date,
                    wo.portal_request_id,
                    CASE WHEN wo.portal_request_id IS NOT NULL THEN true ELSE false END AS is_portal_order,
                    COALESCE(wo.portal_visible, true) AS portal_visible,
                    wo.user_id
                FROM container_access_work_order wo
                WHERE wo.active = true OR wo.active IS NULL
            )
        """)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_open_source_record(self):
        """Open the actual work order record in its native form view."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.source_model,
            'res_id': self.source_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_portal_request(self):
        """View the linked portal request if any."""
        self.ensure_one()
        if not self.portal_request_id:
            raise UserError(_("This work order was not created from a portal request."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'portal.request',
            'res_id': self.portal_request_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
