from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsTag(models.Model):
    _name = 'records.tag'
    _description = 'Records Tag'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(string='Tag Name', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    color = fields.Integer(string='Color Index', help="A color index used in the web client for visual identification.")

    # ============================================================================
    # CATEGORIZATION & RELATIONSHIPS
    # ============================================================================
    category_id = fields.Many2one('records.tag.category', string="Category", tracking=True, ondelete='restrict')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('name_uniq', 'unique (name, company_id)', "A tag with this name already exists in this company."),
    ]

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Ensure tag names are properly formatted on creation."""
        for vals in vals_list:
            if 'name' in vals:
                vals['name'] = vals['name'].strip()
        return super().create(vals_list)

    def write(self, vals):
        """Ensure tag names are properly formatted on update."""
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super().write(vals)


class RecordsTagCategory(models.Model):
    _name = 'records.tag.category'
    _description = 'Records Tag Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    tag_ids = fields.One2many('records.tag', 'category_id', string='Tags')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name, company_id)', "A tag category with this name already exists in this company."),
    ]

