from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RevenueAnalytic(models.Model):
    _name = 'revenue.analytic'
    _description = 'Revenue Analytic Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_end desc, id desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Analytic Period", compute='_compute_name', store=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', readonly=True, comodel_name='res.currency')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('locked', 'Locked'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # PERIOD & CONFIGURATION
    # ============================================================================
    period = fields.Char(string="Period", compute="_compute_period", store=True)
    period_start = fields.Date(string='Period Start', required=True, tracking=True)
    period_end = fields.Date(string='Period End', required=True, tracking=True)
    service_category = fields.Selection(
        [
            ("storage", "Storage"),
            ("retrieval", "Retrieval"),
            ("destruction", "Destruction"),
            ("digital", "Digital Services"),
            ("all", "All Services"),
        ],
        string="Service Category",
        default="all",
        tracking=True,
    )

    # ============================================================================
    # FINANCIAL METRICS
    # ============================================================================
    total_revenue = fields.Monetary(string="Total Revenue", currency_field='currency_id', tracking=True)
    projected_revenue = fields.Monetary(string="Projected Revenue", currency_field='currency_id', tracking=True)
    actual_costs = fields.Monetary(string='Actual Costs', currency_field='currency_id', tracking=True)
    profit_margin = fields.Float(string="Profit Margin (%)", compute='_compute_profit_margin', store=True, aggregator="avg")

    # ============================================================================
    # CUSTOMER METRICS
    # ============================================================================
    customer_count = fields.Integer(string='Active Customer Count', tracking=True)
    average_revenue_per_customer = fields.Monetary(string="Avg Revenue/Customer", compute='_compute_average_revenue', store=True)

    # ============================================================================
    # RELATIONSHIPS & CONTEXT
    # ============================================================================
    config_id = fields.Many2one(
        "records.billing.config",
        string="Billing Configuration",
        ondelete="cascade",
        help="The billing configuration this analytic record belongs to.",
    )
    partner_id = fields.Many2one("res.partner", string="Customer", tracking=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('period_start', 'period_end')
    def _compute_period(self):
        for record in self:
            if record.period_start and record.period_end:
                record.period = f"{record.period_start.strftime('%b %Y')} - {record.period_end.strftime('%b %Y')}"
            else:
                record.period = "Unknown Period"

    @api.depends('total_revenue', 'actual_costs')
    def _compute_profit_margin(self):
        for record in self:
            if record.total_revenue > 0:
                record.profit_margin = ((record.total_revenue - record.actual_costs) / record.total_revenue) * 100
            else:
                record.profit_margin = 0.0

    @api.depends('total_revenue', 'customer_count')
    def _compute_average_revenue(self):
        for record in self:
            if record.customer_count > 0:
                record.average_revenue_per_customer = record.total_revenue / record.customer_count
            else:
                record.average_revenue_per_customer = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_calculate_analytics(self):
        """Placeholder method to trigger the calculation of analytics."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Analytics can only be calculated from a draft state."))

        # In a real implementation, this would query account.move.line, usage records, etc.
        # to populate total_revenue, actual_costs, and customer_count.
        # For demonstration, we'll just update the state.

        self.write({'state': 'calculated'})
        self.message_post(body=_("Revenue analytics calculated."))

    def action_lock(self):
        """Lock the record to prevent further changes."""
        self.ensure_one()
        self.write({'state': 'locked'})
        self.message_post(body=_("Analytic record has been locked."))

    def action_reset_to_draft(self):
        """Reset the record back to draft state for recalculation."""
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_("Analytic record reset to draft."))
