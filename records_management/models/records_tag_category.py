from odoo import models, fields


class RecordsTagCategory(models.Model):
    _name = 'records.tag.category'
    _description = 'Records Tag Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True, translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    tag_ids = fields.One2many('records.tag', 'category_id', string='Tags')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name, company_id)', "A tag category with this name already exists in this company."),
    ]
