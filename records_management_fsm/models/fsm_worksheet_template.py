# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class FSMWorksheetTemplate(models.Model):
    """Templates for FSM service worksheets/checklists"""
    _name = 'fsm.worksheet.template'
    _description = 'FSM Worksheet Template'
    _order = 'sequence, name'

    name = fields.Char(string='Template Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)
    service_type = fields.Selection([
        ('retrieval', 'Container Retrieval'),
        ('pickup', 'Container Pickup/Delivery'),
        ('shredding_onsite', 'On-Site Shredding'),
        ('shredding_offsite', 'Off-Site Shredding'),
        ('destruction', 'Container Destruction'),
        ('access', 'Container Access Request'),
        ('media_destruction', 'Media Destruction'),
        ('hard_drive', 'Hard Drive Destruction'),
    ], string='Service Type', required=True)

    description = fields.Text(string='Instructions')
    checklist_line_ids = fields.One2many(
        'fsm.worksheet.checklist.line',
        'template_id',
        string='Checklist Items'
    )
    requires_signature = fields.Boolean(string='Requires Customer Signature', default=True)
    requires_photos = fields.Boolean(string='Requires Photo Documentation', default=False)
    requires_weight = fields.Boolean(string='Requires Weight Recording', default=False)
    generates_certificate = fields.Boolean(string='Generates Certificate', default=False)


class FSMWorksheetChecklistLine(models.Model):
    """Checklist items for worksheet templates"""
    _name = 'fsm.worksheet.checklist.line'
    _description = 'FSM Worksheet Checklist Line'
    _order = 'sequence, id'

    template_id = fields.Many2one('fsm.worksheet.template', string='Template', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Checklist Item', required=True)
    description = fields.Text(string='Instructions')
    is_mandatory = fields.Boolean(string='Mandatory', default=True)
    field_type = fields.Selection([
        ('checkbox', 'Checkbox'),
        ('text', 'Text Field'),
        ('number', 'Number'),
        ('photo', 'Photo'),
        ('signature', 'Signature'),
    ], string='Field Type', default='checkbox', required=True)


class FSMWorksheetInstance(models.Model):
    """Actual worksheet instance for a specific FSM task"""
    _name = 'fsm.worksheet.instance'
    _description = 'FSM Worksheet Instance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Worksheet', compute='_compute_name', store=True)
    task_id = fields.Many2one('project.task', string='FSM Task', required=True, ondelete='cascade')
    template_id = fields.Many2one('fsm.worksheet.template', string='Template', required=True)
    partner_id = fields.Many2one('res.partner', related='task_id.partner_id', store=True)

    checklist_ids = fields.One2many(
        'fsm.worksheet.checklist.item',
        'worksheet_id',
        string='Checklist'
    )
    completion_percentage = fields.Float(
        string='Completion %',
        compute='_compute_completion_percentage',
        store=True
    )
    is_complete = fields.Boolean(
        string='Complete',
        compute='_compute_is_complete',
        store=True
    )

    customer_signature = fields.Binary(string='Customer Signature')
    customer_signature_date = fields.Datetime(string='Signature Date')
    technician_notes = fields.Text(string='Technician Notes', tracking=True)
    weight_recorded = fields.Float(string='Weight Recorded (kg)')
    photo_ids = fields.Many2many('ir.attachment', string='Photos')

    @api.depends('template_id', 'task_id')
    def _compute_name(self):
        for record in self:
            if record.template_id and record.task_id:
                record.name = f"{record.template_id.name} - {record.task_id.name}"
            else:
                record.name = "Worksheet"

    @api.depends('checklist_ids.is_complete')
    def _compute_completion_percentage(self):
        for record in self:
            total = len(record.checklist_ids)
            if total:
                completed = len(record.checklist_ids.filtered('is_complete'))
                record.completion_percentage = (completed / total) * 100.0
            else:
                record.completion_percentage = 0.0

    @api.depends('completion_percentage', 'template_id')
    def _compute_is_complete(self):
        for record in self:
            mandatory_items = record.checklist_ids.filtered('is_mandatory')
            if mandatory_items:
                record.is_complete = all(item.is_complete for item in mandatory_items)
            else:
                record.is_complete = record.completion_percentage == 100.0

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-create checklist items from template"""
        instances = super().create(vals_list)
        for instance in instances:
            if instance.template_id:
                checklist_vals = []
                for line in instance.template_id.checklist_line_ids:
                    checklist_vals.append({
                        'worksheet_id': instance.id,
                        'name': line.name,
                        'description': line.description,
                        'is_mandatory': line.is_mandatory,
                        'field_type': line.field_type,
                        'sequence': line.sequence,
                    })
                if checklist_vals:
                    self.env['fsm.worksheet.checklist.item'].create(checklist_vals)
        return instances


class FSMWorksheetChecklistItem(models.Model):
    """Actual checklist items for worksheet instance"""
    _name = 'fsm.worksheet.checklist.item'
    _description = 'FSM Worksheet Checklist Item'
    _order = 'sequence, id'

    worksheet_id = fields.Many2one('fsm.worksheet.instance', string='Worksheet', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Item', required=True)
    description = fields.Text(string='Instructions')
    is_mandatory = fields.Boolean(string='Mandatory', default=True)
    field_type = fields.Selection([
        ('checkbox', 'Checkbox'),
        ('text', 'Text Field'),
        ('number', 'Number'),
        ('photo', 'Photo'),
        ('signature', 'Signature'),
    ], string='Field Type', default='checkbox', required=True)

    is_complete = fields.Boolean(string='Complete', default=False)
    text_value = fields.Text(string='Text Value')
    number_value = fields.Float(string='Number Value')
    photo_id = fields.Many2one('ir.attachment', string='Photo')
    signature_data = fields.Binary(string='Signature')
