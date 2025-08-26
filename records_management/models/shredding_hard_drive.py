# -*- coding: utf-8 -*-
import hashlib

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ShreddingHardDrive(models.Model):
    _name = 'shredding.hard_drive'
    _description = 'Hard Drive for Destruction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'destruction_date desc, name'
    _rec_name = 'serial_number'

    name = fields.Char(
        string="Reference",
        required=True,
        index=True,
        copy=False,
        default=lambda self: _('New')
    )
    serial_number = fields.Char(string="Serial Number", required=True, copy=False, index=True)

    fsm_task_id = fields.Many2one(
        'project.task',
        string="FSM Task",
        help="The Field Service task this hard drive is associated with."
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Customer",
        related='fsm_task_id.partner_id',
        store=True,
        readonly=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('scanned', 'Scanned'),
        ('destroyed', 'Destroyed'),
        ('certified', 'Certified'),
        ('error', 'Error'),
    ], string='Status', default='scanned', tracking=True)

    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('degaussing', 'Degaussing'),
        ('disintegration', 'Disintegration')
    ], string="Destruction Method", required=True)

    destruction_date = fields.Datetime(string="Destruction Date", readonly=True)
    destruction_technician_id = fields.Many2one('res.users', string="Technician", readonly=True)

    certificate_id = fields.Many2one(
        'shredding.certificate',
        string="Destruction Certificate",
        readonly=True
    )

    hashed_serial = fields.Char(
        string="Hashed Serial",
        compute='_compute_hashed_serial',
        store=True,
        readonly=True
    )

    @api.depends('serial_number')
    def _compute_hashed_serial(self):
        for record in self:
            if record.serial_number:
                record.hashed_serial = hashlib.sha256(record.serial_number.encode()).hexdigest()
            else:
                record.hashed_serial = False

    @api.constrains('serial_number', 'fsm_task_id')
    def _check_serial_number_unique_per_task(self):
        for record in self:
            if not record.serial_number or not record.fsm_task_id:
                continue
            domain = [
                ('serial_number', '=', record.serial_number),
                ('fsm_task_id', '=', record.fsm_task_id.id),
                ('id', '!=', record.id)
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_('The serial number has already been scanned for this task: %s') % record.serial_number)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('shredding.hard_drive') or _('New')
        return super().create(vals_list)

