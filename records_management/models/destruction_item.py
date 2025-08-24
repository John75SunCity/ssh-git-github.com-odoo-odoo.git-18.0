# -*- coding: utf-8 -*-
"""
Destruction Item Module

Manages individual items slated for destruction as part of a larger
destruction order or service, tracking their status from creation to
verified destruction.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class DestructionItem(models.Model):
    _name = 'destruction.item'
    _description = 'Destruction Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE & RELATIONSHIPS
    # ============================================================================
    name = fields.Char(string='Name', compute='_compute_name', store=True, readonly=False)
    item_description = fields.Char(string="Description", required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    partner_id = fields.Many2one(related='records_destruction_id.partner_id', string='Customer', store=True)

    # Link to the parent destruction order
    records_destruction_id = fields.Many2one('naid.destruction.record', string='Destruction Record', ondelete='cascade', required=True)
    destruction_record_id = fields.Many2one('naid.destruction.record', string="Destruction Record")
    bale_id = fields.Many2one('paper.bale', string="Paper Bale")
    destruction_id = fields.Many2one('records.destruction', string="Destruction Order")

    # Link to the generated certificate
    naid_certificate_id = fields.Many2one(related='records_destruction_id.certificate_id', string='NAID Certificate', store=True)

    # ============================================================================
    # ITEM DETAILS
    # ============================================================================
    quantity = fields.Float(string='Quantity', default=1.0, required=True, tracking=True)
    weight = fields.Float(string='Weight (lbs)', tracking=True)
    container_type_id = fields.Many2one('records.container.type', string='Container Type')

    # ============================================================================
    # WORKFLOW & STATUS
    # ============================================================================
    state = fields.Selection([
        ('pending', 'Pending'),
        ('destroyed', 'Destroyed'),
        ('verified', 'Verified'),
        ('error', 'Error')
    ], string='Status', default='pending', required=True, tracking=True)
    date_destroyed = fields.Datetime(string='Destruction Date', readonly=True, copy=False)
    date_verified = fields.Datetime(string='Verification Date', readonly=True, copy=False)
    verified_by_id = fields.Many2one('res.users', string='Verified By', readonly=True, copy=False)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('item_description', 'sequence')
    def _compute_name(self):
        """Compute name from description and sequence."""
        for record in self:
            if record.item_description:
                record.name = record.item_description
            else:
                record.name = _("Item #%s", record.id or 0)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_destroyed(self):
        """Mark item as destroyed with a timestamp."""
        for record in self:
            if record.state in ['destroyed', 'verified']:
                raise UserError(_("Item '%s' is already marked as destroyed or verified.", record.name))
            record.write({
                'state': 'destroyed',
                'date_destroyed': fields.Datetime.now(),
            })
            record.message_post(body=_("Item marked as destroyed."))

    def action_verify_destruction(self):
        """Verify destruction completion."""
        for record in self:
            if record.state != 'destroyed':
                raise UserError(_("Can only verify items that are in the 'Destroyed' state. Item '%s' is in state '%s'.", record.name, record.state))
            record.write({
                'state': 'verified',
                'date_verified': fields.Datetime.now(),
                'verified_by_id': self.env.user.id,
            })
            record.message_post(body=_("Destruction verified by %s.", self.env.user.name))

    # ============================================================================
    # OVERRIDE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle sequence generation."""
        for vals in vals_list:
            if 'sequence' not in vals or vals['sequence'] == 0:
                vals['sequence'] = self.env['ir.sequence'].next_by_code('destruction.item') or 10
        return super().create(vals_list)

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('quantity', 'weight')
    def _check_positive_values(self):
        """Validate positive values for quantity and weight."""
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero."))
            if record.weight < 0:
                raise ValidationError(_("Weight cannot be negative."))

    @api.constrains('date_destroyed', 'date_verified')
    def _check_destruction_dates(self):
        """Validate destruction and verification dates."""
        for record in self:
            if record.date_verified and not record.date_destroyed:
                raise ValidationError(_("An item cannot be verified before it has been destroyed."))
            if record.date_verified and record.date_destroyed > record.date_verified:
                raise ValidationError(_("Verification date cannot be earlier than the destruction date."))

