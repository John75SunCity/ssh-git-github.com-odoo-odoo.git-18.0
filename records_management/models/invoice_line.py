from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class InvoiceLine(models.Model):
    _name = 'invoice.line'
    _description = 'Invoice Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    sequence = fields.Integer()
    invoice_id = fields.Many2one()
    product_id = fields.Many2one()
    quantity = fields.Float()
    unit_price = fields.Float()
    subtotal = fields.Float()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_subtotal(self):
            """Calculate line subtotal"""
            for record in self:
                record.subtotal = record.quantity * record.unit_price
