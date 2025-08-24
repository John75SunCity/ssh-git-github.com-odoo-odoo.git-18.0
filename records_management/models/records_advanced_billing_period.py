from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class RecordsAdvancedBillingPeriod(models.Model):
    _name = 'records.advanced.billing.period'
    _description = 'Records Advanced Billing Period'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Period Name", compute='_compute_name', store=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)

    # ============================================================================
    # BILLING PERIOD DETAILS
    # ============================================================================
    start_date = fields.Date(string="Start Date", required=True, readonly=True, states={'draft': [('readonly', False)]})
    end_date = fields.Date(string="End Date", required=True, readonly=True, states={'draft': [('readonly', False)]})
    period_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('manual', 'Manual'),
    ], string="Period Type", default='monthly', required=True, readonly=True, states={'draft': [('readonly', False)]})

    # ============================================================================
    # FINANCIAL & STATE FIELDS
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    invoice_ids = fields.One2many('account.move', 'billing_period_id', string="Generated Invoices", readonly=True)
    invoice_count = fields.Integer(string="Invoice Count", compute='_compute_financials', store=True)
    total_invoiced_amount = fields.Monetary(string="Total Invoiced", compute='_compute_financials', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", readonly=True)

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('start_date', 'end_date')
    def _compute_name(self):
        for period in self:
            if period.start_date and period.end_date:
                period.name = _("Billing Period: %s to %s", period.start_date.strftime('%Y-%m-%d'), period.end_date.strftime('%Y-%m-%d'))
            else:
                period.name = _("New Billing Period")

    @api.depends('invoice_ids', 'invoice_ids.amount_total', 'invoice_ids.state')
    def _compute_financials(self):
        for period in self:
            posted_invoices = period.invoice_ids.filtered(lambda inv: inv.state == 'posted')
            period.invoice_count = len(posted_invoices)
            period.total_invoiced_amount = sum(posted_invoices.mapped('amount_total'))

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date >= record.end_date:
                raise ValidationError(_("The start date must be strictly before the end date."))

            # Check for overlapping periods
            overlapping_periods = self.search([
                ('id', '!=', record.id),
                ('start_date', '<=', record.end_date),
                ('end_date', '>=', record.start_date),
                ('state', '!=', 'cancel'),
            ])
            if overlapping_periods:
                raise ValidationError(_("This billing period overlaps with another existing period: %s", overlapping_periods[0].name))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_open_period(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft periods can be opened."))
        self.write({'state': 'open'})
        self.message_post(body=_("Billing period opened by %s.", self.env.user.name))

    def action_generate_invoices(self):
        self.ensure_one()
        if self.state not in ['open', 'in_progress']:
            raise UserError(_("Invoices can only be generated for open or in-progress periods."))

        self.write({'state': 'in_progress'})
        # Placeholder for the complex logic to find billable partners and create invoices.
        # This would typically call a wizard or a background job.
        self.message_post(body=_("Invoice generation process started by %s.", self.env.user.name))
        # In a real scenario, you would return an action to a wizard.
        return True

    def action_close_period(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only in-progress periods can be closed."))
        self.write({'state': 'done'})
        self.message_post(body=_("Billing period closed by %s.", self.env.user.name))

    def action_cancel_period(self):
        self.ensure_one()
        if self.invoice_ids:
            raise UserError(_("Cannot cancel a period that has associated invoices. Please cancel the invoices first."))
        self.write({'state': 'cancel'})
        self.message_post(body=_("Billing period cancelled by %s.", self.env.user.name))

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': _('Generated Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'default_move_type': 'out_invoice'},
            'target': 'current',
        }
