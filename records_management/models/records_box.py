from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsBox(models.Model):
    _name = 'records.box'
    _description = 'Document Storage Box'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char('Box Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('destroyed', 'Destroyed')
    ], string='Status', default='draft', tracking=True)

    # Box details
    product_id = fields.Many2one(
        'product.product', string='Box Product',
        default=lambda self: self.env.ref(
            'records_management.product_box', False))
    location_id = fields.Many2one(
        'records.location', string='Storage Location',
        tracking=True, index=True)
    capacity = fields.Integer('Capacity (documents)', default=100)
    used_capacity = fields.Float(
        'Used Capacity (%)', compute='_compute_used_capacity')
    barcode = fields.Char('Barcode', copy=False)

    # Document management
    document_ids = fields.One2many(
        'records.document', 'box_id', string='Documents')
    document_count = fields.Integer(
        compute='_compute_document_count', string='Document Count',
        store=True)

    # Additional info
    notes = fields.Html('Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)
    user_id = fields.Many2one(
        'res.users', string='Responsible',
        default=lambda self: self.env.user, tracking=True)
    create_date = fields.Datetime('Created on', readonly=True)
    destruction_date = fields.Date('Destruction Date')
    color = fields.Integer('Color Index')
    tag_ids = fields.Many2many('records.tag', string='Tags')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('records.box') or
                    _('New'))
        return super().create(vals_list)

    @api.depends('document_ids')
    def _compute_document_count(self):
        for box in self:
            box.document_count = len(box.document_ids)

    @api.depends('document_ids', 'capacity')
    def _compute_used_capacity(self):
        for box in self:
            if box.capacity:
                box.used_capacity = (box.document_count / box.capacity) * 100
            else:
                box.used_capacity = 0

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('box_id', '=', self.id)],
            'context': {'default_box_id': self.id},
        }

    def action_set_active(self):
        self.write({'state': 'active'})

    def action_archive_box(self):
        self.write({'state': 'archived'})

    def action_destroy_box(self):
        self.write({
            'state': 'destroyed',
            'destruction_date': fields.Date.today()
        })

    @api.constrains('document_count', 'capacity')
    def _check_capacity(self):
        for box in self:
            if box.document_count > box.capacity:
                raise ValidationError(
                    _("Box %s is over capacity! Maximum is %s documents.") %
                    (box.name, box.capacity))
