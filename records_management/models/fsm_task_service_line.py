# -*- coding: utf-8 -*-
"""
FSM Task Service Line Model

Service line items for FSM tasks with detailed service breakdowns.
"""

import math

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FSMTaskServiceLine(models.Model):
    """FSM Task Service Line"""

    _name = "fsm.task.service.line"
    _description = "FSM Task Service Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "task_id, sequence, service_type"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Service Description",
        required=True,
        tracking=True,
        help="Description of the service performed"
    )

    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        help="Display name for the service line"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this service line"
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Sequence for line ordering"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    task_id = fields.Many2one(
        "fsm.task",
        string="FSM Task",
        required=True,
        ondelete="cascade",
        index=True,
        help="Parent FSM task"
    )

    product_id = fields.Many2one(
        "product.product",
        string="Service Product",
        domain="[('type', '=', 'service')]",
        help="Service product for this line"
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Technician",
        help="Employee who performed the service"
    )

    # ============================================================================
    # SERVICE DETAILS
    # ============================================================================
    service_type = fields.Selection([
        ('pickup', 'Container Pickup'),
        ('delivery', 'Container Delivery'),
        ('retrieval', 'Document Retrieval'),
        ('destruction', 'On-site Destruction'),
        ('scanning', 'Document Scanning'),
        ('indexing', 'Document Indexing'),
        ('consultation', 'Consultation'),
        ('maintenance', 'Equipment Maintenance'),
        ('travel', 'Travel Time'),
        ('other', 'Other Service')
    ], string='Service Type', required=True, tracking=True)

    service_date = fields.Datetime(
        string="Service Date",
        default=fields.Datetime.now,
        required=True,
        help="Date and time service was performed"
    )

    duration_hours = fields.Float(
        string="Duration (Hours)",
        default=1.0,
        help="Time spent on this service"
    )

    # ============================================================================
    # QUANTITY AND UNITS
    # ============================================================================
    quantity = fields.Float(
        string="Quantity",
        default=1.0,
        required=True,
        help="Quantity of service units"
    )

    unit_of_measure = fields.Selection([
        ('hour', 'Hours'),
        ('container', 'Containers'),
        ('document', 'Documents'),
        ('cubic_foot', 'Cubic Feet'),
        ('pickup', 'Pickups'),
        ('scan', 'Scans'),
        ('consultation', 'Consultations'),
        ('other', 'Other')
    ], string='Unit of Measure', default='hour', required=True)

    # ============================================================================
    # PRICING
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True
    )

    unit_price = fields.Monetary(
        string="Unit Price",
        currency_field="currency_id",
        help="Price per unit"
    )

    total_price = fields.Monetary(
        string="Total Price",
        currency_field="currency_id",
        compute='_compute_total_price',
        store=True,
        help="Total line price"
    )

    # ============================================================================
    # LOCATION AND EQUIPMENT
    # ============================================================================
    location_id = fields.Many2one(
        "records.location",
        string="Service Location",
        help="Location where service was performed"
    )

    equipment_used = fields.Text(
        string="Equipment Used",
        help="Equipment or tools used for the service"
    )

    # ============================================================================
    # QUALITY AND COMPLETION
    # ============================================================================
    status = fields.Selection([
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('billed', 'Billed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='planned', required=True, tracking=True)

    completion_percentage = fields.Float(
        string="Completion %",
        default=0.0,
        help="Percentage of service completed"
    )

    quality_rating = fields.Selection([
        ('1', 'Poor'),
        ('2', 'Fair'),
        ('3', 'Good'),
        ('4', 'Very Good'),
        ('5', 'Excellent')
    ], string='Quality Rating')

    # ============================================================================
    # NOTES AND OBSERVATIONS
    # ============================================================================
    service_notes = fields.Text(
        string="Service Notes",
        help="Detailed notes about the service performed"
    )

    customer_feedback = fields.Text(
        string="Customer Feedback",
        help="Customer feedback on the service"
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'service_type', 'quantity', 'unit_of_measure')
    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            parts = [record.name]
            if record.quantity and record.unit_of_measure:
                uom_dict = dict(record._fields['unit_of_measure'].selection)
                uom_label = uom_dict.get(record.unit_of_measure, record.unit_of_measure)
                parts.append(f"({record.quantity} {uom_label})")
            
            record.display_name = " ".join(parts)

    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        """Calculate total price"""
        for record in self:
            record.total_price = record.quantity * record.unit_price

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_service(self):
        """Start the service"""
        self.ensure_one()
        if self.status != 'planned':
            raise UserError(_('Can only start planned services'))
        
        self.write({
            'status': 'in_progress',
            'service_date': fields.Datetime.now()
        })
        self.message_post(body=_('Service started'))

    def action_complete_service(self):
        """Complete the service"""
        self.ensure_one()
        if self.status != 'in_progress':
            raise UserError(_('Can only complete services in progress'))
        
        self.write({
            'status': 'completed',
            'completion_percentage': 100.0
        })
        self.message_post(body=_('Service completed'))

    def action_verify_service(self):
        """Verify service completion"""
        self.ensure_one()
        if self.status != 'completed':
            raise UserError(_('Can only verify completed services'))
        
        self.write({'status': 'verified'})
        self.message_post(body=_('Service verified'))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('quantity', 'unit_price')
    def _check_positive_values(self):
        """Validate positive values"""
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than 0'))
            if record.unit_price < 0:
                raise ValidationError(_('Unit price cannot be negative'))

    @api.constrains('duration_hours')
    def _check_duration(self):
        """Validate duration"""
        for record in self:
            if record.duration_hours < 0:
                raise ValidationError(_('Duration cannot be negative'))

    @api.constrains('completion_percentage')
    def _check_completion_percentage(self):
        """Validate completion percentage"""
        for record in self:
            if not (0 <= record.completion_percentage <= 100):
                raise ValidationError(_('Completion percentage must be between 0 and 100'))
