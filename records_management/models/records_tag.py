from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsTag(models.Model):
    _name = 'records.tag.report'
    _description = 'Records Tag Analysis Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence')
    color = fields.Integer(string='Color')
    state = fields.Selection()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    date_created = fields.Datetime(string='Created Date')
    date_modified = fields.Datetime(string='Modified Date')
    active = fields.Boolean(string='Active')
    notes = fields.Text(string='Internal Notes')
    category = fields.Selection()
    priority = fields.Selection()
    auto_assign = fields.Boolean()
    icon = fields.Char()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    partner_id = fields.Many2one()
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    search_view_id = fields.Many2one('search.view')
    view_id = fields.Many2one('view')
    view_mode = fields.Char(string='View Mode')
    date_from = fields.Date()
    date_to = fields.Date()
    tag_ids = fields.Many2many()
    tag_usage_count = fields.Integer()
    most_used_tags = fields.Text()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name."""
            for record in self:
                record.display_name = record.name or _("New")


    def write(self, vals):
            """Override write to update modification date."""

    def action_activate(self):
            """Activate the record."""

            self.ensure_one()
            self.write({"state": "active"})


    def action_deactivate(self):
            """Deactivate the record."""

            self.ensure_one()
            self.write({"state": "inactive"})


    def action_archive(self):
            """Archive the record."""

            self.ensure_one()
            self.write({"state": "archived", "active": False})


    def create(self, vals_list):
            """Override create to set default values."""
            # Handle both single dict and list of dicts
            if not isinstance(vals_list, list):
                vals_list = [vals_list]

            for vals in vals_list:
                if not vals.get("name"):
                    vals["name"] = _("New Record")

            return super().create(vals_list)



    def _compute_tag_metrics(self):
            """Compute tag usage analytics"""
            for record in self:
                # Sample computation - adjust based on actual tag usage in your models
                domain = []
                    ('create_date', '>=', record.date_from),
                    ('create_date', '<=', record.date_to)

                if record.tag_ids:
                    # This would need to be adjusted based on which models actually use tags
                    record.tag_usage_count = len(record.tag_ids)
                    record.most_used_tags = ', '.join(record.tag_ids.mapped('name'))
                else:
                    record.tag_usage_count = 0
                    record.most_used_tags = ''


    def generate_report(self):
            """Generate the tag analysis report"""
            return {}
                'type': 'ir.actions.report',
                'report_name': 'records_management.tag_analysis_report',
                'report_type': 'qweb-pdf',
                'data': {'form_data': self.read()[0]},
                'context': self.env.context))))))

