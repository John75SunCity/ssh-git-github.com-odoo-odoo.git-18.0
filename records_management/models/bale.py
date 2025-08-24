# -*- coding: utf-8 -*-
"""
Paper Bale Management Module

Manages shredded paper bales for recycling and waste management in the Records
Management system. Tracks bale creation, weight, recycling revenue, and
environmental compliance with full NAID AAA audit trails.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PaperBale(models.Model):
    """
    Paper Bale Management

    Manages the lifecycle of shredded paper bales from creation through
    recycling sale, including weight tracking, revenue calculation, and
    environmental compliance reporting.
    """
    _name = 'paper.bale'
    _description = 'Shredded Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'bale_date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string='Bale Reference',
        required=True,
        tracking=True,
        index=True,
        copy=False,
        default=lambda self: _('New')
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user,
        tracking=True
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Set to false to archive this bale record."
    )

    # ============================================================================
    # BUSINESS SPECIFIC FIELDS
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('sold', 'Sold'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    bale_date = fields.Date(
        string='Bale Date',
        default=fields.Date.today,
        required=True,
        tracking=True
    )
    completion_date = fields.Date(
        string='Completion Date',
        tracking=True
    )
    sale_date = fields.Date(
        string='Sale Date',
        tracking=True
    )

    # Weight and Volume Tracking
    target_weight_lbs = fields.Float(
        string='Target Weight (lbs)',
        default=1000.0,
        help="Target weight for this bale in pounds"
    )
    current_weight_lbs = fields.Float(
        string='Current Weight (lbs)',
        tracking=True,
        help="Current weight of shredded paper in this bale"
    )
    final_weight_lbs = fields.Float(
        string='Final Weight (lbs)',
        tracking=True,
        help="Final confirmed weight when bale is completed"
    )
    weight_variance = fields.Float(
        string='Weight Variance',
        compute='_compute_weight_variance',
        store=True,
        help="Difference between target and final weight"
    )

    # Financial Fields
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    price_per_lb = fields.Monetary(
        string='Price per Pound',
        currency_field='currency_id',
        help="Sale price per pound for recycled paper"
    )
    total_revenue = fields.Monetary(
        string='Total Revenue',
        currency_field='currency_id',
        compute='_compute_total_revenue',
        store=True,
        help="Total revenue from bale sale"
    )

    # ============================================================================
    # SHREDDING SERVICE INTEGRATION
    # ============================================================================
    shredding_service_ids = fields.Many2many(
        'shredding.service',
        'bale_shredding_rel',
        'bale_id',
        'shredding_id',
        string='Source Shredding Services',
        help="Shredding services that contributed to this bale"
    )
    destruction_item_ids = fields.One2many(
        'destruction.item',
        'bale_id',
        string='Destruction Items',
        help="Individual destruction items included in this bale"
    )

    # ============================================================================
    # RECYCLING AND BUYER INFORMATION
    # ============================================================================
    buyer_id = fields.Many2one(
        'res.partner',
        string='Buyer',
        domain=[('is_company', '=', True)],
        tracking=True,
        help="Company purchasing the recycled paper bale"
    )
    recycling_certificate_number = fields.Char(
        string='Recycling Certificate',
        help="Certificate number from recycling facility"
    )
    pickup_date = fields.Date(
        string='Buyer Pickup Date',
        tracking=True
    )
    transport_company_id = fields.Many2one(
        'res.partner',
        string='Transport Company',
        help="Company responsible for bale transportation"
    )

    # ============================================================================
    # ENVIRONMENTAL COMPLIANCE
    # ============================================================================
    environmental_compliance = fields.Boolean(
        string='Environmental Compliance',
        default=True,
        tracking=True,
        help="Confirms bale meets environmental standards"
    )
    contamination_level = fields.Selection([
        ('none', 'No Contamination'),
        ('minimal', 'Minimal (<1%)'),
        ('low', 'Low (1-3%)'),
        ('moderate', 'Moderate (3-5%)'),
        ('high', 'High (>5%)'),
    ], string='Contamination Level', default='none')

    carbon_offset_kg = fields.Float(
        string='Carbon Offset (kg CO2)',
        compute='_compute_carbon_offset',
        store=True,
        help="Estimated carbon offset from recycling this bale"
    )

    # ============================================================================
    # OPERATIONAL FIELDS
    # ============================================================================
    storage_location_id = fields.Many2one(
        'records.location',
        string='Storage Location',
        help="Location where bale is stored before pickup"
    )
    bale_operator_id = fields.Many2one(
        'hr.employee',
        string='Bale Operator',
        help="Employee responsible for creating the bale"
    )
    quality_check_passed = fields.Boolean(
        string='Quality Check Passed',
        default=False,
        tracking=True
    )
    quality_notes = fields.Text(
        string='Quality Notes',
        help="Notes from quality inspection"
    )

    # ============================================================================
    # NOTES AND DOCUMENTATION
    # ============================================================================
    description = fields.Text(
        string='Description',
        help="General description of the bale contents"
    )
    notes = fields.Text(
        string='Internal Notes',
        help="Internal notes about the bale"
    )
    special_instructions = fields.Text(
        string='Special Instructions',
        help="Special handling or processing instructions"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('target_weight_lbs', 'final_weight_lbs')
    def _compute_weight_variance(self):
        """Calculate variance between target and final weight"""
        for record in self:
            if record.target_weight_lbs and record.final_weight_lbs:
                record.weight_variance = record.final_weight_lbs - record.target_weight_lbs
            else:
                record.weight_variance = 0.0

    @api.depends('final_weight_lbs', 'price_per_lb')
    def _compute_total_revenue(self):
        """Calculate total revenue from bale sale"""
        for record in self:
            if record.final_weight_lbs and record.price_per_lb:
                record.total_revenue = record.final_weight_lbs * record.price_per_lb
            else:
                record.total_revenue = 0.0

    @api.depends('final_weight_lbs')
    def _compute_carbon_offset(self):
        """Calculate estimated carbon offset from recycling"""
        for record in self:
            if record.final_weight_lbs:
                # Estimate: 1 lb of recycled paper = 1.5 kg CO2 offset
                record.carbon_offset_kg = record.final_weight_lbs * 0.68  # Convert lbs to kg and apply factor
            else:
                record.carbon_offset_kg = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_bale(self):
        """Start the bale creation process"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft bales can be started."))

        self.write({'state': 'in_progress'})
        self.message_post(body=_("Bale creation started."))

    def action_complete_bale(self):
        """Complete the bale and finalize weight"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only in-progress bales can be completed."))

        if not self.current_weight_lbs:
            raise UserError(_("Please enter the current weight before completing the bale."))

        self.write({
            'state': 'completed',
            'completion_date': fields.Date.today(),
            'final_weight_lbs': self.current_weight_lbs,
        })
        self.message_post(body=_("Bale completed with final weight: %s lbs", self.final_weight_lbs))

    def action_quality_check(self):
        """Perform quality check on completed bale"""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("Only completed bales can undergo quality check."))

        # Open quality check wizard or form
        return {
            'type': 'ir.actions.act_window',
            'name': _('Quality Check'),
            'res_model': 'paper.bale.quality.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_bale_id': self.id},
        }

    def action_mark_sold(self):
        """Mark bale as sold"""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("Only completed bales can be marked as sold."))

        if not self.buyer_id:
            raise UserError(_("Please select a buyer before marking as sold."))

        if not self.price_per_lb:
            raise UserError(_("Please enter the sale price per pound."))

        self.write({
            'state': 'sold',
            'sale_date': fields.Date.today(),
        })
        self.message_post(body=_("Bale sold to %s for %s per pound", self.buyer_id.name, self.price_per_lb))

        # Create accounting entry if needed
        self._create_sale_accounting_entry()

    def action_cancel(self):
        """Cancel the bale"""
        self.ensure_one()
        if self.state == 'sold':
            raise UserError(_("Cannot cancel a sold bale."))

        self.write({'state': 'cancelled'})
        self.message_post(body=_("Bale cancelled."))

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def add_shredded_material(self, weight_lbs, source_service=None):
        """Add shredded material to the bale"""
        self.ensure_one()
        if self.state not in ['draft', 'in_progress']:
            raise UserError(_("Can only add material to draft or in-progress bales."))

        new_weight = self.current_weight_lbs + weight_lbs
        if new_weight > self.target_weight_lbs * 1.1:  # Allow 10% over target
            raise UserError(_("Adding this material would exceed the target weight by more than 10%%."))

        self.current_weight_lbs = new_weight

        # Link source service if provided
        if source_service and source_service not in self.shredding_service_ids:
            self.shredding_service_ids = [(4, source_service.id)]

        self.message_post(body=_("Added %s lbs of shredded material. Current weight: %s lbs",
                                weight_lbs, self.current_weight_lbs))

    def _create_sale_accounting_entry(self):
        """Create accounting entry for bale sale"""
        if not self.total_revenue:
            return

        # This would integrate with accounting module to create revenue entry
        # Implementation depends on specific accounting setup
        pass

    def get_environmental_impact_summary(self):
        """Get summary of environmental impact"""
        self.ensure_one()
        return {
            'carbon_offset_kg': self.carbon_offset_kg,
            'trees_saved': round(self.final_weight_lbs * 0.024, 1),  # Estimate: 24 trees per ton
            'landfill_diverted_kg': round(self.final_weight_lbs * 0.453592, 1),  # Convert to kg
            'energy_saved_kwh': round(self.final_weight_lbs * 2.5, 1),  # Estimate: 2.5 kWh per lb
        }

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Assign sequence number on creation"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('current_weight_lbs', 'final_weight_lbs')
    def _check_weight_values(self):
        """Validate weight values are positive"""
        for record in self:
            if record.current_weight_lbs < 0:
                raise ValidationError(_("Current weight cannot be negative."))
            if record.final_weight_lbs < 0:
                raise ValidationError(_("Final weight cannot be negative."))

    @api.constrains('price_per_lb')
    def _check_price_per_lb(self):
        """Validate price per pound is positive"""
        for record in self:
            if record.price_per_lb < 0:
                raise ValidationError(_("Price per pound cannot be negative."))

    @api.constrains('bale_date', 'completion_date', 'sale_date')
    def _check_date_sequence(self):
        """Validate date sequence is logical"""
        for record in self:
            if record.completion_date and record.bale_date and record.completion_date < record.bale_date:
                raise ValidationError(_("Completion date cannot be before bale date."))

            if record.sale_date and record.completion_date and record.sale_date < record.completion_date:
                raise ValidationError(_("Sale date cannot be before completion date."))

    @api.constrains('contamination_level', 'environmental_compliance')
    def _check_environmental_compliance(self):
        """Validate environmental compliance requirements"""
        for record in self:
            if record.contamination_level in ['moderate', 'high'] and record.environmental_compliance:
                raise ValidationError(_("Bales with moderate or high contamination cannot be environmentally compliant."))
