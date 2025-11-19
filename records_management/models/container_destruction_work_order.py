# -*- coding: utf-8 -*-
"""
Container Destruction Work Order Module

Manages the entire lifecycle of destroying records containers, from initial
request and authorization to final certification, ensuring a compliant
and auditable process.

Author: Records Management System
Version: 18.0.0.2.29
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ContainerDestructionWorkOrder(models.Model):
    _name = 'container.destruction.work.order'
    _description = 'Container Destruction Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_destruction_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE IDENTIFICATION & WORKFLOW
    # ============================================================================
    name = fields.Char(
        string='Work Order Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: "New"
    )
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one(comodel_name='res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('authorized', 'Authorized'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('destroyed', 'Destroyed'),
        ('certified', 'Certified'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent')
    ], string='Priority', default='0')

    # ------------------------------------------------------------------
    # PORTAL VISIBILITY
    # ------------------------------------------------------------------
    portal_visible = fields.Boolean(
        string='Portal Visible',
        default=True,
        help='Controls whether this destruction work order is visible in the customer portal.\n'
             'Used by unified work order portal controller domain filtering. Disable to hide sensitive or internal-only orders.'
    )

    # ============================================================================
    # CUSTOMER & AUTHORIZATION
    # ============================================================================
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, tracking=True)
    portal_request_id = fields.Many2one(comodel_name='portal.request', string='Portal Request', ondelete='set null')
    destruction_reason = fields.Text(string='Reason for Destruction')
    customer_authorized = fields.Boolean(string='Customer Authorized', readonly=True)
    customer_authorization_date = fields.Datetime(string='Authorization Date', readonly=True)
    authorized_by = fields.Char(string='Authorized By', tracking=True)
    authorization_document = fields.Binary(string='Authorization Document', attachment=True)

    # ============================================================================
    # CONTAINER & INVENTORY DETAILS
    # ============================================================================
    container_ids = fields.Many2many(
        'records.container',
        relation='container_destruction_work_order_container_rel',
        column1='work_order_id',
        column2='container_id',
        string='Containers for Destruction',
        required=True
    )
    container_count = fields.Integer(string='Container Count', compute='_compute_container_metrics', store=True)
    total_cubic_feet = fields.Float(string='Total Cubic Feet', compute='_compute_container_metrics', store=True)
    estimated_weight_lbs = fields.Float(string='Estimated Weight (lbs)', compute='_compute_container_metrics', store=True)
    inventory_completed = fields.Boolean(string='Inventory Completed', readonly=True)
    inventory_date = fields.Datetime(string='Inventory Date', readonly=True)
    inventory_user_id = fields.Many2one(comodel_name='res.users', string='Inventoried By', readonly=True)

    # ============================================================================
    # SCHEDULING & EXECUTION
    # ============================================================================
    scheduled_destruction_date = fields.Datetime(string='Scheduled Destruction Date', tracking=True)
    pickup_date = fields.Datetime(string='Pickup Date', readonly=True)
    actual_destruction_date = fields.Datetime(string='Actual Destruction Date', readonly=True)
    estimated_duration_hours = fields.Float(string='Estimated Duration (Hours)', compute='_compute_estimated_duration')
    destruction_facility_id = fields.Many2one(comodel_name='stock.location', string='Destruction Facility', domain="[('is_destruction_facility', '=', True)]")
    shredding_equipment_id = fields.Many2one(comodel_name='maintenance.equipment', string='Shredding Equipment')
    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('pulping', 'Pulping'),
        ('incineration', 'Incineration'),
        ('disintegration', 'Disintegration')
    ], string='Destruction Method', default='shredding', required=True)
    naid_compliant = fields.Boolean(string='NAID Compliant', default=True)

    # ============================================================================
    # WITNESS & VERIFICATION
    # ============================================================================
    witness_required = fields.Boolean(string='Witness Required')
    customer_witness_name = fields.Char(string='Customer Witness')
    internal_witness_id = fields.Many2one(comodel_name='res.users', string='Internal Witness')
    destruction_verified = fields.Boolean(string='Destruction Verified', readonly=True)
    verification_date = fields.Datetime(string='Verification Date', readonly=True)
    verification_notes = fields.Text(string='Verification Notes')

    # ============================================================================
    # CHAIN OF CUSTODY
    # ============================================================================
    custody_transfer_ids = fields.One2many('custody.transfer.event', 'destruction_work_order_id', string='Chain of Custody')
    custody_complete = fields.Boolean(string='Custody Complete', compute='_compute_custody_complete')
    transport_vehicle_id = fields.Many2one(comodel_name='fleet.vehicle', string='Transport Vehicle')
    driver_id = fields.Many2one(comodel_name='hr.employee', string='Driver')

    # ============================================================================
    # POST-DESTRUCTION & CERTIFICATION
    # ============================================================================
    actual_weight_destroyed_lbs = fields.Float(string='Actual Weight Destroyed (lbs)')
    destruction_start_time = fields.Datetime(string='Destruction Start Time', readonly=True)
    destruction_end_time = fields.Datetime(string='Destruction End Time', readonly=True)
    destruction_duration_minutes = fields.Integer(string='Destruction Duration (Minutes)', compute='_compute_destruction_duration')
    certificate_id = fields.Many2one(comodel_name='shredding.certificate', string='Certificate of Destruction', readonly=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id.name', 'container_count')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id and record.container_count:
                record.display_name = _("%s - %s (%s containers)", record.name, record.partner_id.name, record.container_count)
            elif record.partner_id:
                record.display_name = _("%s - %s", record.name, record.partner_id.name)
            else:
                record.display_name = record.name or _("New Container Destruction")

    @api.depends('container_ids', 'container_ids.container_type_id')
    def _compute_container_metrics(self):
        """Compute container metrics with safe dependency pattern"""
        for record in self:
            containers = record.container_ids
            record.container_count = len(containers)

            # Safe computation of cubic feet
            total_cubic_feet = 0.0
            for container in containers:
                if hasattr(container, 'cubic_feet') and container.cubic_feet:
                    total_cubic_feet += container.cubic_feet
            record.total_cubic_feet = total_cubic_feet

            # Safe computation of estimated weight using container type definitions
            estimated_weight = 0.0
            for container in containers:
                if (hasattr(container, 'container_type_id') and
                    container.container_type_id and
                    hasattr(container.container_type_id, 'average_weight_lbs') and
                    container.container_type_id.average_weight_lbs):
                    estimated_weight += container.container_type_id.average_weight_lbs
            record.estimated_weight_lbs = estimated_weight

    @api.depends('container_count', 'destruction_method')
    def _compute_estimated_duration(self):
        for record in self:
            if record.container_count:
                base_minutes = {'shredding': 15, 'pulping': 20, 'incineration': 30, 'disintegration': 25}
                method_time = base_minutes.get(record.destruction_method, 15)
                total_minutes = (record.container_count * method_time) + 60  # Add 1hr for setup
                record.estimated_duration_hours = total_minutes / 60.0
            else:
                record.estimated_duration_hours = 0.0

    @api.depends('custody_transfer_ids.transfer_type')
    def _compute_custody_complete(self):
        for record in self:
            required_events = ['pickup', 'destruction']
            documented_events = record.custody_transfer_ids.mapped('transfer_type')
            record.custody_complete = all(event in documented_events for event in required_events)

    @api.depends('destruction_start_time', 'destruction_end_time')
    def _compute_destruction_duration(self):
        for record in self:
            if record.destruction_start_time and record.destruction_end_time:
                duration = record.destruction_end_time - record.destruction_start_time
                record.destruction_duration_minutes = int(duration.total_seconds() / 60)
            else:
                record.destruction_duration_minutes = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be confirmed."))
        if not self.container_ids:
            raise UserError(_("Please select containers for destruction."))
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Work order confirmed."))

    def action_authorize(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Can only authorize confirmed work orders."))
        self.write({
            'state': 'authorized',
            'customer_authorized': True,
            'customer_authorization_date': fields.Datetime.now()
        })
        self.message_post(body=_("Customer authorization received."))

    def action_schedule(self):
        self.ensure_one()
        if self.state != 'authorized':
            raise UserError(_("Can only schedule authorized work orders."))
        if not self.scheduled_destruction_date:
            raise UserError(_("Please set a scheduled destruction date."))
        self.write({'state': 'scheduled'})
        self.message_post(body=_("Destruction scheduled for %s", self.scheduled_destruction_date.strftime('%Y-%m-%d')))

    def action_start_destruction(self):
        self.ensure_one()
        if self.state not in ['scheduled', 'in_progress']:
            raise UserError(_("Can only start destruction from a scheduled or in-progress state."))
        self.write({
            'state': 'in_progress',
            'destruction_start_time': fields.Datetime.now()
        })
        self.message_post(body=_("Destruction process started."))

    def action_complete_destruction(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Can only complete destruction from an in-progress state."))
        self.write({
            'state': 'destroyed',
            'destruction_end_time': fields.Datetime.now(),
            'actual_destruction_date': fields.Datetime.now().date()
        })
        self.container_ids.write({'state': 'destroyed'})
        self.message_post(body=_("Destruction process completed."))

    def action_mark_all_destroyed(self):
        """
        Mark all containers as destroyed by simulating barcode scan to destruction location.
        
        This action:
        1. Changes container state from 'in_storage' to 'destroyed'
        2. Updates destruction date for billing purposes
        3. Creates audit trail entries
        4. Marks containers for billing (destruction charges apply)
        
        Returns:
            bool: True on success
        """
        self.ensure_one()
        
        if self.state not in ['in_progress', 'scheduled']:
            raise UserError(_("Can only mark containers as destroyed when work order is scheduled or in progress."))
        
        if not self.container_ids:
            raise UserError(_("No containers selected for destruction."))
        
        destruction_date = fields.Datetime.now()
        destroyed_count = 0
        
        for container in self.container_ids:
            # Skip already destroyed containers
            if container.state == 'destroyed':
                continue
            
            # Update container state and destruction metadata
            container.sudo().write({
                'state': 'destroyed',
                'destruction_date': destruction_date.date(),
            })
            
            # Create audit log entry (simulates barcode scan)
            self.env['naid.audit.log'].sudo().create({
                'action_type': 'container_destroyed',
                'container_id': container.id,
                'user_id': self.env.user.id,
                'work_order_id': self.id if hasattr(self.env['naid.audit.log'], 'work_order_id') else False,
                'description': _('Container %s marked as destroyed via work order %s (simulated destruction location scan)') % (
                    container.name, self.name
                ),
                'timestamp': destruction_date,
            })
            
            destroyed_count += 1
        
        # Update work order state
        if destroyed_count > 0:
            self.write({
                'state': 'destroyed',
                'actual_destruction_date': destruction_date.date(),
                'destruction_end_time': destruction_date,
            })
            
            self.message_post(
                body=_("✅ Marked %d container(s) as destroyed. Containers are now billable for destruction charges.") % destroyed_count
            )
        else:
            raise UserError(_("All selected containers are already destroyed."))
        
        return True

    def action_generate_certificate(self):
        self.ensure_one()
        if self.state != 'destroyed':
            raise UserError(_("Can only generate a certificate after destruction is complete."))
        if self.certificate_id:
            raise UserError(_("A certificate has already been generated for this work order."))

        certificate = self.env['shredding.certificate'].create({
            'work_order_id': self.id,
            'partner_id': self.partner_id.id,
            'destruction_date': self.actual_destruction_date,
            'destruction_method': self.destruction_method,
        })
        self.write({'certificate_id': certificate.id, 'state': 'certified'})
        self.message_post(body=_("Certificate of Destruction %s generated.", certificate.name))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Certificate of Destruction'),
            'res_model': 'shredding.certificate',
            'res_id': certificate.id,
            'view_mode': 'form',
        }

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Work order cancelled."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('container.destruction.work.order') or _('New')
        return super().create(vals_list)
