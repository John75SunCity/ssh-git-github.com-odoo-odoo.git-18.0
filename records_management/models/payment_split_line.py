from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaymentSplitLine(models.Model):
    _name = 'payment.split.line'
    _description = 'Payment Split Line'
    _order = 'split_id, sequence, id'

    # ============================================================================
    # FIELDS
    # ============================================================================
    split_id = fields.Many2one('payment.split', string='Payment Split', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)

    name = fields.Char(string='Description', required=True)
    amount = fields.Monetary(string='Amount', required=True, currency_field='currency_id')
    currency_id = fields.Many2one(
        "res.currency", related="split_id.currency_id", string="Currency", readonly=True, store=True
    )

    partner_id = fields.Many2one('res.partner', string='Destination Partner')
    invoice_id = fields.Many2one(
        "account.move",
        string="Destination Invoice",
        domain="[('move_type', '=', 'out_invoice'), ('partner_id', '=', partner_id), ('payment_state', '!=', 'paid')]",
    )

    processed = fields.Boolean(string='Processed', readonly=True, default=False, copy=False)
    processing_date = fields.Datetime(string='Processing Date', readonly=True, copy=False)

    notes = fields.Text(string='Notes')

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('amount')
    def _check_amount(self):
        for line in self:
            if line.amount <= 0:
                raise ValidationError(_("Split amount must be a positive value."))

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        """
        When an invoice is selected, automatically populate the partner,
        description, and the remaining amount to be paid on that invoice.
        """
        if self.invoice_id:
            self.partner_id = self.invoice_id.partner_id
            self.name = self.invoice_id.name
            self.amount = self.invoice_id.amount_residual
        else:
            self.name = False
            self.amount = 0.0
