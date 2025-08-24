from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsTag(models.Model):
    """Tag for records management with category, color, and key-value support."""
    _name = 'records.tag'
    _description = 'Records Tag'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # Main fields
    name = fields.Char(
        string='Tag Name',
        required=True,
        tracking=True,
        index=True,
        help="Short, unique tag name."
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Lower numbers appear first."
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help="If unchecked, tag is hidden from selection."
    )
    color = fields.Integer(
        string='Color Index',
        help="A color index used in the web client for visual identification."
    )
    category_id = fields.Many2one(
        'records.tag.category',
        string="Category",
        tracking=True,
        ondelete='restrict',
        help="Tag category for grouping."
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        readonly=True,
        ondelete='cascade',
        help="Company this tag belongs to."
    )

    # Optional metadata fields
    description = fields.Char(
        string='Description',
        help="Optional description for this tag."
    )
    key = fields.Char(
        string='Key',
        help="Optional key for advanced filtering or integration."
    )
    value = fields.Char(
        string='Value',
        help="Optional value for advanced filtering or integration."
    )

    # Computed display name for better UX in many2one fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    _sql_constraints = [
        ('name_uniq', 'unique (name, company_id)', "A tag with this name already exists in this company."),
    ]

    @api.depends('name', 'category_id')
    def _compute_display_name(self):
        for rec in self:
            if rec.category_id:
                rec.display_name = "[%s] %s" % (rec.category_id.name, rec.name)
            else:
                rec.display_name = rec.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' in vals and vals['name']:
                vals['name'] = vals['name'].strip()
        return super().create(vals_list)

    def write(self, vals):
        if 'name' in vals and vals['name']:
            vals['name'] = vals['name'].strip()
        return super().write(vals)

    @api.constrains('name')
    def _check_name_trimmed(self):
        for rec in self:
            if rec.name and rec.name != rec.name.strip():
                raise ValidationError(_("Tag Name cannot start or end with whitespace."))
