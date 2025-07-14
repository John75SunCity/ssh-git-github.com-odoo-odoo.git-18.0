# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsBox(models.Model):
    """Model for document storage boxes with enhanced fields."""
    _name = 'records.box'
    _description = 'Document Storage Box'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Box Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    alternate_code = fields.Char(string='Alternate Code', copy=False)
    description = fields.Char(string='Description', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('destroyed', 'Destroyed')
    ], string='Status', default='draft', tracking=True)
    item_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('permanent_out', 'Permanent Out'),
        ('destroyed', 'Destroyed'),
        ('archived', 'Archived')
    ], string='Item Status', default='active', tracking=True)
    status_date = fields.Datetime(
        string='Status Date',
        default=fields.Datetime.now,
        tracking=True
    )
    add_date = fields.Datetime(
        string='Add Date',
        default=fields.Datetime.now,
        readonly=True
    )
    destroy_date = fields.Date(string='Destroy Date')
    access_count = fields.Integer(string='Access Count', default=0)
    perm_flag = fields.Boolean(string='Permanent Flag', default=False)
    product_id = fields.Many2one('product.product', string='Box Product')
    location_id = fields.Many2one(
        'records.location',
        string='Storage Location',
        tracking=True,
        index=True
    )
    location_code = fields.Char(
        related='location_id.code',
        string='Location Code',
        readonly=True
    )
    container_type = fields.Selection([
        ('standard', 'Standard Box'),
        ('map_box', 'Map Box'),
        ('specialty', 'Specialty Box'),
        ('pallet', 'Pallet'),
        ('other', 'Other')
    ], string='Container Type', default='standard', tracking=True)
    security_code = fields.Char(string='Security Code')
    category_code = fields.Char(string='Category Code')
    record_series = fields.Char(string='Record Series')
    object_code = fields.Char(string='Object Code')
    account_level1 = fields.Char(string='Account Level 1')
    account_level2 = fields.Char(string='Account Level 2')
    account_level3 = fields.Char(string='Account Level 3')
    sequence_from = fields.Integer(string='Sequence From')
    sequence_to = fields.Integer(string='Sequence To')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    user_field1 = fields.Char(string='User Field 1')
    user_field2 = fields.Char(string='User Field 2')
    user_field3 = fields.Char(string='User Field 3')
    user_field4 = fields.Char(string='User Field 4')
    custom_date = fields.Date(string='Custom Date')
    charge_for_storage = fields.Boolean(
        string='Charge for Storage',
        default=True
    )
    charge_for_add = fields.Boolean(string='Charge for Add', default=True)
    capacity = fields.Integer(string='Capacity (documents)', default=100)
    used_capacity = fields.Float(
        string='Used Capacity (%)',
        compute='_compute_used_capacity',
        store=False
    )
    barcode = fields.Char(string='Barcode', copy=False)
    barcode_length = fields.Integer(string='Barcode Length', default=12)
    barcode_type = fields.Selection([
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('upc', 'UPC'),
        ('ean13', 'EAN-13'),
        ('qr', 'QR Code'),
        ('other', 'Other')
    ], string='Barcode Type', default='code128')
    document_ids = fields.One2many(
        'records.document',
        'box_id',
        string='Documents'
    )
    document_count = fields.Integer(
        compute='_compute_document_count',
        string='Document Count',
        store=True
    )
    notes = fields.Html(string='Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain="[('is_company', '=', True)]",
        tracking=True,
        index=True
    )
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        tracking=True,
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user,
        tracking=True
    )
    create_date = fields.Datetime(string='Created on', readonly=True)
    destruction_date = fields.Date(string='Destruction Date')
    color = fields.Integer(string='Color Index')
    tag_ids = fields.Many2many('records.tag', string='Tags')

    @api.model_create_multi
    def create(self, vals_list: List[dict]) -> 'RecordsBox':
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                sequence = self.env['ir.sequence'].next_by_code('records.box')
                vals['name'] = sequence or _('New')
        return super().create(vals_list)

    @api.depends('document_ids')
    def _compute_document_count(self) -> None:
        for box in self:
            box.document_count = len(box.document_ids)

    @api.depends('document_count', 'capacity')
    def _compute_used_capacity(self) -> None:
        for box in self:
            if box.capacity:
                percentage = (box.document_count / box.capacity * 100)
                box.used_capacity = percentage
            else:
                box.used_capacity = 0

    def action_view_documents(self) -> dict:
        self.ensure_one()
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('box_id', '=', self.id)],
            'context': {'default_box_id': self.id},
        }

    def action_set_active(self) -> bool:
        return self.write({'state': 'active'})

    def action_archive_box(self) -> bool:
        return self.write({'state': 'archived'})

    def action_destroy_box(self) -> bool:
        return self.write({
            'state': 'destroyed',
            'item_status': 'destroyed',
            'destroy_date': fields.Date.today(),
            'status_date': fields.Datetime.now()
        })

    def action_increment_access(self) -> bool:
        return self.write({'access_count': self.access_count + 1})

    def action_permanent_out(self) -> bool:
        return self.write({
            'item_status': 'permanent_out',
            'state': 'archived',
            'status_date': fields.Datetime.now()
        })

    @api.constrains('barcode', 'barcode_length')
    def _check_barcode_length(self) -> None:
        for box in self:
            if (box.barcode and box.barcode_length and
                    len(box.barcode) != box.barcode_length):
                error_msg = _(
                    "Barcode length mismatch for box %s. "
                    "Expected %s digits, got %s."
                )
                raise ValidationError(
                    error_msg % (
                        box.name, box.barcode_length, len(box.barcode)
                    )
                )

    @api.constrains('sequence_from', 'sequence_to')
    def _check_sequence_range(self) -> None:
        for box in self:
            if (box.sequence_from and box.sequence_to and
                    box.sequence_from > box.sequence_to):
                error_msg = _(
                    "Invalid sequence range for box %s. "
                    "From (%s) cannot be greater than To (%s)."
                )
                raise ValidationError(
                    error_msg % (box.name, box.sequence_from, box.sequence_to)
                )

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self) -> None:
        for box in self:
            if (box.date_from and box.date_to and
                    box.date_from > box.date_to):
                error_msg = _(
                    "Invalid date range for box %s. "
                    "From (%s) cannot be greater than To (%s)."
                )
                raise ValidationError(
                    error_msg % (box.name, box.date_from, box.date_to)
                )

    @api.constrains('document_count', 'capacity')
    def _check_capacity(self) -> None:
        for box in self:
            if box.document_count > box.capacity:
                error_msg = _(
                    "Box %s is over capacity! Maximum is %s documents."
                )
                raise ValidationError(error_msg % (box.name, box.capacity))

    def write(self, vals: dict) -> bool:
        res = super().write(vals)
        if 'customer_id' in vals or 'department_id' in vals:
            for box in self:
                customer_id = box.customer_id.id if box.customer_id else False
                department_id = (box.department_id.id if box.department_id
                                 else False)
                box.document_ids.write({
                    'customer_id': customer_id,
                    'department_id': department_id,
                })
        return res

    @api.onchange('container_type')
    def _onchange_container_type(self) -> None:
        """Update capacity based on container type for better UX."""
        if self.container_type == 'standard':
            self.capacity = 100
        elif self.container_type == 'map_box':
            self.capacity = 50
        elif self.container_type == 'pallet':
            self.capacity = 500
