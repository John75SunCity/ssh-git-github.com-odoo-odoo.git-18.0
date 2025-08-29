from odoo import models, fields

class MediaType(models.Model):
    _name = 'media.type'
    _description = 'Media Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Media Type Name', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    description = fields.Text(string='Description')
    category = fields.Selection([
        ('document', 'Document'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('image', 'Image'),
        ('digital', 'Digital Media'),
        ('magnetic', 'Magnetic Media'),
        ('optical', 'Optical Media'),
        ('other', 'Other')
    ], string='Category', required=True, default='document', tracking=True)

    # Storage requirements
    storage_requirements = fields.Text(string='Storage Requirements')
    retention_period = fields.Integer(string='Default Retention Period (Years)', default=7)
    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('incineration', 'Incineration'),
        ('degaussing', 'Degaussing'),
        ('physical', 'Physical Destruction'),
        ('data_wipe', 'Data Wiping'),
        ('other', 'Other')
    ], string='Recommended Destruction Method', default='shredding')

    # Properties
    is_electronic = fields.Boolean(string='Electronic Media', default=False)
    requires_special_handling = fields.Boolean(string='Requires Special Handling', default=False)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
