# -*- coding: utf-8 -*-
"""
Container Retrieval Work Order Module

Manages the process of retrieving stored containers and delivering them back
to the customer, tracking the entire workflow from request to completion.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ContainerRetrievalWorkOrder(models.Model):
    _name = 'container.retrieval.work.order'
    _description = 'Container Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_delivery_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE IDENTIFICATION & WORKFLOW
    # ============================================================================
    name = fields.Char(string='Work Order Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('scheduled', 'Scheduled'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    priority = fields.Selection([('0', 'Normal'), ('1', 'High'), ('2', 'Urgent')], string='Priority', default='0')

    # ============================================================================
    # CUSTOMER & CONTAINER DETAILS
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    container_ids = fields.Many2many(
        'records.container',
        relation='container_retrieval_work_order_container_rel',
        column1='work_order_id',
        column2='container_id',
        string='Containers for Retrieval',
        required=True
    )
    container_count = fields.Integer(string='Container Count', compute='_compute_container_metrics', store=True)
    total_volume = fields.Float(string='Total Volume (cubic ft)', compute='_compute_container_metrics', store=True)
    total_weight = fields.Float(string='Total Weight (lbs)', compute='_compute_container_metrics', store=True)

    # ============================================================================
    # SCHEDULING & DELIVERY
    # ============================================================================
    scheduled_delivery_date = fields.Datetime(string='Scheduled Delivery', tracking=True)
    delivery_method = fields.Selection([
        ('standard', 'Standard Delivery'),
        ('express', 'Express Delivery'),
        ('white_glove', 'White Glove Service'),
        ('customer_pickup', 'Customer Pickup')
    ], string='Delivery Method', default='standard', required=True, tracking=True,
        help="Method of delivery for the retrieved containers.")
    delivery_window_start = fields.Datetime(string='Delivery Window Start', compute='_compute_delivery_window', store=True)
    delivery_window_end = fields.Datetime(string='Delivery Window End', compute='_compute_delivery_window', store=True)
    actual_pickup_date = fields.Datetime(string='Actual Pickup Date', readonly=True)
    actual_delivery_date = fields.Datetime(string='Actual Delivery Date', readonly=True)
    delivery_address_id = fields.Many2one('res.partner', string='Delivery Address', help="Defaults to customer address if not set.")
    delivery_instructions = fields.Text(string='Delivery Instructions')
    access_requirements = fields.Text(string='Access Requirements')
    contact_person = fields.Char(string='Delivery Contact Person')
    contact_phone = fields.Char(string='Delivery Contact Phone')
    duration_hours = fields.Float(string='Duration (Hours)', compute='_compute_duration', store=True)
    is_overdue = fields.Boolean(string='Delivery Overdue', compute='_compute_overdue_status', store=True)
    days_until_delivery = fields.Integer(string='Days Until Delivery', compute='_compute_days_until_delivery')

    # ============================================================================
    # LOGISTICS
    # ============================================================================
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    driver_id = fields.Many2one('hr.employee', string='Driver')
    route_id = fields.Many2one('pickup.route', string='Pickup Route')
    equipment_needed = fields.Text(string='Special Equipment Needed')
    coordinator_id = fields.Many2one('work.order.coordinator', string="Coordinator")

    # ============================================================================
    # COMPLETION & FEEDBACK
    # ============================================================================
    delivery_receipt_signed = fields.Boolean(string='Delivery Receipt Signed', readonly=True)
    customer_signature = fields.Binary(string='Customer Signature', attachment=True)
    delivery_photo = fields.Binary(string='Delivery Photo', attachment=True)
    delivery_notes = fields.Text(string='Internal Delivery Notes')
    customer_satisfaction_rating = fields.Selection([
        ('1', 'Very Dissatisfied'), ('2', 'Dissatisfied'), ('3', 'Neutral'),
        ('4', 'Satisfied'), ('5', 'Very Satisfied')
    ], string='Customer Satisfaction')

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
                record.display_name = record.name or _("New Container Retrieval")

    @api.depends('container_ids', 'container_ids.container_type_id')
    def _compute_container_metrics(self):
        """Compute container metrics with safe dependency pattern"""
        for record in self:
            containers = record.container_ids
            record.container_count = len(containers)

            # Safe computation of volume
            total_volume = 0.0
            for container in containers:
                if hasattr(container, 'cubic_feet') and container.cubic_feet:
                    total_volume += container.cubic_feet
            record.total_volume = total_volume

            # Safe computation of estimated weight using container type definitions
            estimated_weight = 0.0
            for container in containers:
                if (hasattr(container, 'container_type_id') and
                    container.container_type_id and
                    hasattr(container.container_type_id, 'average_weight_lbs') and
                    container.container_type_id.average_weight_lbs):
                    estimated_weight += container.container_type_id.average_weight_lbs
            record.total_weight = estimated_weight

    @api.depends('scheduled_delivery_date')
    def _compute_delivery_window(self):
        for record in self:
            if record.scheduled_delivery_date:
                record.delivery_window_start = record.scheduled_delivery_date - timedelta(hours=1)
                record.delivery_window_end = record.scheduled_delivery_date + timedelta(hours=1)
            else:
                record.delivery_window_start = False
                record.delivery_window_end = False

    @api.depends('actual_pickup_date', 'actual_delivery_date')
    def _compute_duration(self):
        for record in self:
            if record.actual_pickup_date and record.actual_delivery_date:
                delta = record.actual_delivery_date - record.actual_pickup_date
                record.duration_hours = delta.total_seconds() / 3600.0
            else:
                record.duration_hours = 0.0

    @api.depends('scheduled_delivery_date', 'state')
    def _compute_overdue_status(self):
        for record in self:
            record.is_overdue = (
                record.scheduled_delivery_date and
                record.scheduled_delivery_date < datetime.now() and
                record.state not in ['delivered', 'completed', 'cancelled']
            )

    @api.depends('scheduled_delivery_date')
    def _compute_days_until_delivery(self):
        for record in self:
            if record.scheduled_delivery_date:
                delta = record.scheduled_delivery_date.date() - datetime.now().date()
                record.days_until_delivery = delta.days
            else:
                record.days_until_delivery = 0

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('scheduled_delivery_date')
    def _check_delivery_date(self):
        for record in self:
            if record.scheduled_delivery_date and record.scheduled_delivery_date <= datetime.now():
                raise ValidationError(_("Scheduled delivery date must be in the future."))

    @api.constrains('actual_pickup_date', 'actual_delivery_date')
    def _check_delivery_sequence(self):
        for record in self:
            if record.actual_pickup_date and record.actual_delivery_date and record.actual_pickup_date > record.actual_delivery_date:
                raise ValidationError(_("Pickup date cannot be after delivery date."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be confirmed."))
        if not self.container_ids:
            raise UserError(_("At least one container must be selected for retrieval."))
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Container retrieval work order confirmed for %s.", self.partner_id.name))

    def action_schedule(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed work orders can be scheduled."))
        if not self.vehicle_id or not self.driver_id:
            raise UserError(_("Vehicle and driver must be assigned before scheduling."))
        self.write({'state': 'scheduled'})
        self.message_post(body=_("Work order scheduled for delivery on %s.", self.scheduled_delivery_date.strftime('%Y-%m-%d')))

    def action_start_transit(self):
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_("Only scheduled work orders can be started."))
        self.write({'state': 'in_transit', 'actual_pickup_date': fields.Datetime.now()})
        self.container_ids.write({'location_status': 'in_transit'})
        self.message_post(body=_("Containers picked up and in transit to %s.", self.partner_id.name))

    def action_confirm_delivery(self):
        self.ensure_one()
        if self.state != 'in_transit':
            raise UserError(_("Only work orders in transit can be marked as delivered."))
        self.write({'state': 'delivered', 'actual_delivery_date': fields.Datetime.now()})
        self.container_ids.write({'location_status': 'at_customer'})
        self.message_post(body=_("Containers successfully delivered to %s.", self.partner_id.name))

    def action_complete(self):
        self.ensure_one()
        if self.state != 'delivered':
            raise UserError(_("Only delivered work orders can be completed."))
        if not self.delivery_receipt_signed:
            raise UserError(_("Delivery receipt must be signed before completion."))
        self.write({'state': 'completed'})
        self.message_post(body=_("Container retrieval work order completed successfully."))

    def action_cancel(self):
        self.ensure_one()
        if self.state in ['delivered', 'completed']:
            raise UserError(_("Delivered or completed work orders cannot be cancelled."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Container retrieval work order cancelled."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('container.retrieval.work.order') or _('New')
        return super().create(vals_list)

