from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare


class PaymentSplit(models.Model):
    _name = 'payment.split'
    _description = 'Payment Split'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payment_date desc, id desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True, states={'draft': [('readonly', False)]})

    payment_id = fields.Many2one('account.payment', string='Source Payment', readonly=True, states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', related='journal_id.currency_id', string='Currency', readonly=True)

    total_amount = fields.Monetary(string='Total Amount to Split', required=True, readonly=True, states={'draft': [('readonly', False)]})
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', readonly=True, tracking=True)

    split_line_ids = fields.One2many('payment.split.line', 'split_id', string='Split Lines')

    split_total = fields.Monetary(string='Split Total', compute='_compute_split_total', store=True)
    remaining_balance = fields.Monetary(string='Remaining Balance', compute='_compute_split_total', store=True)

    # ============================================================================
    # METHODS
    # ============================================================================
    @api.depends('split_line_ids.amount', 'total_amount')
    def _compute_split_total(self):
        for split in self:
            split_total = sum(line.amount for line in split.split_line_ids)
            split.split_total = split_total
            split.remaining_balance = split.total_amount - split_total

    @api.constrains('total_amount', 'split_total')
    def _check_amounts(self):
        for split in self:
            if float_compare(split.split_total, split.total_amount, precision_rounding=split.currency_id.rounding) > 0:
                raise ValidationError(_("The total of the split lines cannot exceed the total amount to split."))

    def action_confirm(self):
        self.ensure_one()
        if not self.split_line_ids:
            raise UserError(_("You cannot confirm a split without any split lines."))
        if float_compare(self.split_total, self.total_amount, precision_rounding=self.currency_id.rounding) != 0:
            raise UserError(_("The total of the split lines must equal the total amount to split before confirming."))
        self.write({'state': 'confirmed'})

    def action_process(self):
        self.write({'state': 'processing'})
        # Placeholder for processing logic (e.g., creating payments or journal entries)
        self.split_line_ids.write({'processed': True, 'processing_date': fields.Datetime.now()})
        self.write({'state': 'done'})
        self.message_post(body=_("Payment split processed successfully."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('payment.split') or _('New')
        return super().create(vals_list)
