# -*- coding: utf-8 -*-
"""
Records Destruction Model

This module provides comprehensive destruction record management for the Records
Management System. It tracks destruction operations with full NAID AAA compliance
and chain of custody documentation.

Key Features:
- Destruction operation tracking and management
- NAID AAA compliance integration
- Chain of custody documentation
- Multi-item destruction batching
- Certificate generation and management

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsDestruction(models.Model):
    """
    Records Destruction Management
    
    Manages destruction operations for document containers and records
    with full NAID AAA compliance tracking.
    """

    _name = "records.destruction"
    _description = "Records Destruction"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'destruction_date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Destruction Reference",
        required=True,
        tracking=True,
        index=True,
        copy=False,
        default=lambda self: _('New'),
        help="Unique reference for this destruction operation"
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help="Company performing the destruction"
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this destruction record"
    )

    # ============================================================================
    # DESTRUCTION OPERATION FIELDS
    # ============================================================================
    destruction_date = fields.Datetime(
        string="Destruction Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        help="Date and time when destruction was performed"
    )

    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('pulping', 'Pulping'),
        ('incineration', 'Incineration'),
        ('degaussing', 'Degaussing'),
        ('other', 'Other')
    ], string='Destruction Method', required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    destruction_item_ids = fields.One2many(
        "destruction.item",
        "records_destruction_id",
        string="Destruction Items",
        help="Individual items being destroyed in this operation"
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        help="Customer whose records are being destroyed"
    )

    responsible_user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this destruction operation"
    )

    compliance_id = fields.Many2one(
        'naid.compliance',
        string='NAID Compliance Record',
        tracking=True,
        help="Associated NAID compliance record"
    )

    # ============================================================================
    # COMPLIANCE FIELDS
    # ============================================================================
    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=True,
        tracking=True,
        help="Whether this destruction meets NAID AAA standards"
    )

    certificate_generated = fields.Boolean(
        string="Certificate Generated",
        default=False,
        tracking=True,
        help="Whether destruction certificate has been generated"
    )

    notes = fields.Text(
        string="Destruction Notes",
        help="Additional notes and observations about the destruction"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    item_count = fields.Integer(
        string="Item Count",
        compute='_compute_item_count',
        store=True,
        help="Number of items being destroyed"
    )

    total_weight = fields.Float(
        string="Total Weight (lbs)",
        compute='_compute_total_weight',
        store=True,
        help="Total weight of all destroyed items"
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('destruction_item_ids')
    def _compute_item_count(self):
        """Compute the total number of destruction items"""
        for record in self:
            record.item_count = len(record.destruction_item_ids)

    @api.depends('destruction_item_ids', 'destruction_item_ids.weight')
    def _compute_total_weight(self):
        """Compute the total weight of all destruction items"""
        for record in self:
            record.total_weight = sum(record.destruction_item_ids.mapped('weight'))

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model
    def create(self, vals):
        """Override create to generate sequence number"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('records.destruction') or _('New')
        return super().create(vals)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_schedule(self):
        """Schedule destruction operation"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Can only schedule draft destructions'))
        self.write({'state': 'scheduled'})

    def action_start(self):
        """Start destruction operation"""
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_('Can only start scheduled destructions'))
        self.write({'state': 'in_progress'})

    def action_complete(self):
        """Complete destruction operation"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_('Can only complete in-progress destructions'))
        self.write({
            'state': 'completed',
            'destruction_date': fields.Datetime.now()
        })

    def action_cancel(self):
        """Cancel destruction operation"""
        self.ensure_one()
        if self.state == 'completed':
            raise UserError(_('Cannot cancel completed destructions'))
        self.write({'state': 'cancelled'})

    def action_generate_certificate(self):
        """Generate destruction certificate"""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_('Can only generate certificates for completed destructions'))
        
        # Create NAID certificate if not exists
        if not self.certificate_generated:
            certificate_vals = {
                'name': _('Destruction Certificate - %s', self.name),
                'partner_id': self.partner_id.id,
                'destruction_date': self.destruction_date,
                'destruction_method': self.destruction_method,
                'total_weight': self.total_weight,
            }
            
            certificate = self.env['naid.certificate'].create(certificate_vals)
            self.write({'certificate_generated': True})
            
            return {
                'type': 'ir.actions.act_window',
                'name': _('Destruction Certificate'),
                'res_model': 'naid.certificate',
                'res_id': certificate.id,
                'view_mode': 'form',
                'target': 'current',
            }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('destruction_date')
    def _check_destruction_date(self):
        """Validate destruction date"""
        for record in self:
            if record.destruction_date and record.destruction_date > fields.Datetime.now():
                raise ValidationError(_('Destruction date cannot be in the future'))

    @api.constrains('destruction_item_ids')
    def _check_destruction_items(self):
        """Validate destruction items"""
        for record in self:
            if record.state in ['in_progress', 'completed'] and not record.destruction_item_ids:
                raise ValidationError(_('Destruction must have at least one item to process'))
