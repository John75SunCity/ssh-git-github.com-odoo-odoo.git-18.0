from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsBillingConfig(models.Model):
    _name = 'records.billing.config'
    _description = 'Records Billing Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Configuration Name', required=True, tracking=True, help="e.g., Standard Box Storage, Rush Retrieval Fee")
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)

    # ============================================================================
    # BILLING DETAILS
    # ============================================================================
    product_id = fields.Many2one('product.product', string="Service Product", required=True, domain="[('detailed_type', '=', 'service')]")
    billing_type = fields.Selection([
        ('recurring', 'Recurring'),
        ('one_time', 'One-Time'),
        ('usage', 'Usage-Based')
    ], string="Billing Type", required=True, default='recurring', tracking=True)

    unit_price = fields.Monetary(string="Unit Price", tracking=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", readonly=True)

    # ============================================================================
    # RECURRING CONFIGURATION
    # ============================================================================
    recurring_interval = fields.Integer(string="Repeat Every", default=1, help="The interval number (e.g., 1 for every month).")
    recurring_period = fields.Selection([
        ('day', 'Days'),
        ('week', 'Weeks'),
        ('month', 'Months'),
        ('year', 'Years'),
    ], string="Interval Unit", default='month', help="The unit of the interval (e.g., month).")

    # ============================================================================
    # STATE & WORKFLOW
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate the billing configuration."""
        self.ensure_one()
        if not self.product_id:
            raise ValidationError(_("A service product must be set before activating."))
        self.write({'state': 'active'})
        self.message_post(body=_("Configuration activated by %s.", self.env.user.name))

    def action_archive(self):
        """Archive the billing configuration."""
        for record in self:
            record.write({'state': 'archived', 'active': False})
            record.message_post(body=_("Configuration archived by %s.", self.env.user.name))

    def action_reset_to_draft(self):
        """Reset the configuration to draft state."""
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_("Configuration reset to draft by %s.", self.env.user.name))

    # ============================================================================
    # ONCHANGE & CONSTRAINTS
    # ============================================================================
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update unit price when product changes."""
        if self.product_id:
            self.unit_price = self.product_id.lst_price

    @api.constrains('recurring_interval', 'recurring_period', 'billing_type')
    def _check_recurring_config(self):
        for record in self:
            if record.billing_type == 'recurring':
                if record.recurring_interval <= 0:
                    raise ValidationError(_("The recurring interval must be a positive number."))
                if not record.recurring_period:
                    raise ValidationError(_("The recurring period must be set for recurring billing."))
            else:
                # Optional: Clear recurring fields if not recurring
                if record.recurring_interval or record.recurring_period:
                    record.recurring_interval = False
                    record.recurring_period = False
