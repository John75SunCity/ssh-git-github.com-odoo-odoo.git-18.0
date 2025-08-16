# -*- coding: utf-8 -*-
from odoo import models, fields, api, _



class RecordsTag(models.Model):
    _name = "records.tag"
    _description = "Records Tag"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

        # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True),
    description = fields.Text(string="Description"),
    sequence = fields.Integer(string="Sequence", default=10),
    color = fields.Integer(string="Color", help="Color index for tag display"):
        # State Management
    state = fields.Selection(
        []
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        
        string="Status",
        default="draft",
        tracking=True,
    

        # Company and User
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    
    user_id = fields.Many2one(
        "res.users", string="Responsible User", default=lambda self: self.env.user
    

        # Timestamps
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now),
    date_modified = fields.Datetime(string="Modified Date")

        # Control Fields
    active = fields.Boolean(string="Active", default=True),
    notes = fields.Text(string="Internal Notes")

        # Category and Priority
    category = fields.Selection(
        []
            ("general", "General"),
            ("legal", "Legal"),
            ("financial", "Financial"),
            ("hr", "HR"),
        
        string="Category",
    
    priority = fields.Selection(
        [("low", "Low"), ("normal", "Normal"), ("high", "High")], string="Priority",
        default="normal",
    
    auto_assign = fields.Boolean("Auto Assign", default=False),
    icon = fields.Char("Icon")

        # Computed Fields    # Mail Thread Framework Fields (inherited from mail.thread)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities"),
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    def write(self, vals):
        """Override write to update modification date."""
    vals["date_modified"] = fields.Datetime.now()
        return super().write(vals)

    def action_activate(self):
        """Activate the record."""

        self.ensure_one()
        self.write({"state": "active"})

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record":
            pass
    
    help = fields.Char(string='Help'),
    res_model = fields.Char(string='Res Model'),
    search_view_id = fields.Many2one('search.view', string='Search View Id'),
    view_id = fields.Many2one('view', string='View Id'),
    view_mode = fields.Char(string='View Mode')

    def action_deactivate(self):
        """Deactivate the record."""

        self.ensure_one()
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""

        self.ensure_one()
        self.write({"state": "archived", "active": False})

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values."""
        # Handle both single dict and list of dicts
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _("New Record")

        return super().create(vals_list)


class RecordsTagReport(models.TransientModel):
    """Records Tag Analysis Report"""
    
    _name = 'records.tag.report'
    _description = 'Records Tag Analysis Report'

        # Report date range
    date_from = fields.Date(
        string='Date From', 
        required=True, 
        default=fields.Date.today
    
    date_to = fields.Date(
        string='Date To', 
        required=True, 
        default=fields.Date.today
    
    
        # Tag filters
    tag_ids = fields.Many2many(
        'records.tag', 
        string='Tags'
    
    
        # Report results
    tag_usage_count = fields.Integer(
        string='Usage Count', 
        compute='_compute_tag_metrics'
    
    most_used_tags = fields.Text(
        string='Most Used Tags', 
        compute='_compute_tag_metrics'
    
    
    @api.depends('date_from', 'date_to', 'tag_ids')
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
            'context': self.env.context,
        
