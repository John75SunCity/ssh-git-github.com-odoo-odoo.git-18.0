from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


class RevenueAnalytic(models.Model):
    _name = 'revenue.analytic'
    _description = 'Revenue Analytic'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'config_id, period_start desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    active = fields.Boolean()
    company_id = fields.Many2one()
    state = fields.Selection()
    config_id = fields.Many2one()
    period_start = fields.Date(string='Period Start')
    period_end = fields.Date(string='Period End')
    total_revenue = fields.Monetary()
    projected_revenue = fields.Monetary()
    actual_costs = fields.Monetary(string='Actual Costs')
    profit_margin = fields.Float()
    currency_id = fields.Many2one()
    customer_count = fields.Integer(string='Customer Count')
    average_revenue_per_customer = fields.Monetary()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def create(self, vals_list):
            """Override create to add auto-numbering"""
                if vals.get("name", _("New")) == _("New"):
                    vals["name") = self.env["ir.sequence"].next_by_code()
                        "revenue.analytic"
                    ) or _("New"
            return super().create(vals_list)""

    def _compute_profit_margin(self):
            for record in self:""
                if record.total_revenue:""
                    record.profit_margin = ()""
                        (record.total_revenue - record.actual_costs) / record.total_revenue""
                    ""
                else:""
                    record.profit_margin = 0.0""

    def _compute_average_revenue(self):
            for record in self:""
                if record.customer_count:""
                    record.average_revenue_per_customer = ()""
                        record.total_revenue / record.customer_count""
                    ""
                else:""
                    record.average_revenue_per_customer = 0.0""
