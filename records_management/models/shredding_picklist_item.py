# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ShreddingPicklistItem(models.Model):
    _name = 'shredding.picklist.item'
    _description = 'Shredding Picklist Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'picklist_id, sequence, id'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Reference", required=True, copy=False, default=lambda self: _('New'))
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    # Linkage
    picklist_id = fields.Many2one('shredding.picklist', string="Picklist", required=True, ondelete='cascade')
    batch_id = fields.Many2one('shredding.batch', string="Shredding Batch")
    container_id = fields.Many2one('records.container', string="Container", required=True)
    partner_id = fields.Many2one(related='picklist_id.partner_id', string="Customer", store=True)
    location_id = fields.Many2one(related='container_id.location_id', string="Location", store=True)

    # Container Details
    container_type = fields.Selection(related='container_id.container_type_id.name', string="Container Type")
    container_barcode = fields.Char(related='container_id.barcode', string="Barcode")
    container_volume_cf = fields.Float(related='container_id.volume_cubic_ft', string="Volume (cu ft)")
    quantity = fields.Float(string="Quantity", default=1.0)
    weight_kg = fields.Float(string="Weight (kg)")
    weight_lbs = fields.Float(string="Weight (lbs)", compute='_compute_weight_lbs', store=True)
    estimated_shred_time = fields.Float(string="Est. Shred Time (min)")

    # Status & Lifecycle
    status = fields.Selection([
        ('pending', 'Pending'),
        ('collected', 'Collected'),
        ('in_queue', 'In Queue'),
        ('shredding', 'Shredding'),
        ('shredded', 'Shredded'),
        ('certified', 'Certified'),
        ('exception', 'Exception'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='pending', tracking=True)

    # Timestamps & Personnel
    collection_date = fields.Datetime(string="Collection Date", readonly=True)
    shred_start_time = fields.Datetime(string="Shred Start Time", readonly=True)
    shred_completion_time = fields.Datetime(string="Shred Completion Time", readonly=True)
    certification_date = fields.Datetime(string="Certification Date", readonly=True)
    collected_by_id = fields.Many2one('res.users', string="Collected By", readonly=True)
    shredded_by_id = fields.Many2one('res.users', string="Shredded By", readonly=True)
    witness_employee_id = fields.Many2one('hr.employee', string="Witness")

    # Destruction Details
    shredding_equipment_id = fields.Many2one('maintenance.equipment', string="Shredding Equipment")
    shred_method = fields.Selection([
        ('on_site', 'On-Site Shredding'),
        ('off_site', 'Off-Site Shredding'),
        ('disintegration', 'Disintegration')
    ], string="Shred Method")
    security_level = fields.Selection([
        ('p3', 'P-3'), ('p4', 'P-4'), ('p5', 'P-5'), ('p6', 'P-6'), ('p7', 'P-7')
    ], string="Security Level")
    destruction_certificate_id = fields.Many2one('destruction.certificate', string="Certificate", readonly=True)
    naid_compliant = fields.Boolean(string="NAID Compliant", default=True)

    # Auditing & Exceptions
    audit_trail_ids = fields.One2many('naid.audit.log', 'shred_item_id', string="Audit Trail")
    exception_reason = fields.Text(string="Exception Reason")
    resolution_notes = fields.Text(string="Resolution Notes")
    exception_resolved = fields.Boolean(string="Exception Resolved")
    collection_notes = fields.Text(string="Collection Notes")
    shredding_notes = fields.Text(string="Shredding Notes")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'container_id.name', 'container_id.barcode')
    def _compute_display_name(self):
        for item in self:
            parts = []
            if item.container_id:
                parts.append(item.container_id.name or item.container_barcode or _("Unnamed Container"))
            else:
                parts.append(item.name or _("New Item"))
            item.display_name = " - ".join(parts)

    @api.depends('weight_kg')
    def _compute_weight_lbs(self):
        for item in self:
            item.weight_lbs = item.weight_kg * 2.20462

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('container_id')
    def _onchange_container_id(self):
        if self.container_id:
            self.weight_kg = self.container_id.weight_pounds * 0.453592 if self.container_id.weight_pounds else 0.0
            if hasattr(self.container_id, 'security_level'):
                self.security_level = self.container_id.security_level

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_collect_item(self):
        self.ensure_one()
        if self.status != 'pending':
            raise UserError(_("Only 'Pending' items can be collected."))
        self.write({
            'status': 'collected',
            'collection_date': fields.Datetime.now(),
            'collected_by_id': self.env.user.id
        })
        self._create_audit_log('item_collected', _("Item collected by %s.", self.env.user.name))

    def action_start_shredding(self):
        self.ensure_one()
        if self.status not in ['collected', 'in_queue']:
            raise UserError(_("Only 'Collected' or 'In Queue' items can be shredded."))
        self.write({
            'status': 'shredding',
            'shred_start_time': fields.Datetime.now(),
            'shredded_by_id': self.env.user.id
        })
        self._create_audit_log('shredding_started', _("Shredding started by %s.", self.env.user.name))

    def action_complete_shredding(self):
        self.ensure_one()
        if self.status != 'shredding':
            raise UserError(_("Only items being shredded can be completed."))
        if not self.shredding_equipment_id or not self.shred_method:
            raise UserError(_("Shredding equipment and method must be specified before completion."))
        self.write({
            'status': 'shredded',
            'shred_completion_time': fields.Datetime.now()
        })
        self._update_container_status()
        self._create_audit_log('shredding_completed', _("Shredding completed successfully."))

    # ============================================================================
    # BUSINESS LOGIC
    # ============================================================================
    def _create_audit_log(self, action_type, notes):
        self.ensure_one()
        self.env['naid.audit.log'].create({
            'action_type': action_type,
            'user_id': self.env.user.id,
            'shred_item_id': self.id,
            'description': notes,
            'naid_compliant': self.naid_compliant,
        })

    def _update_container_status(self):
        self.ensure_one()
        if self.container_id and self.container_id.state != 'destroyed':
            self.container_id.write({
                'state': 'destroyed',
                'destruction_date': fields.Date.today()
            })

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('shredding.picklist.item') or _('New')
        items = super().create(vals_list)
        for item in items:
            item._create_audit_log('created', _("Picklist item created for container %s.", item.container_id.name))
        return items

    def write(self, vals):
        res = super().write(vals)
        if 'status' in vals:
            for item in self:
                status_label = dict(item._fields['status'].selection).get(item.status, item.status)
                item.message_post(body=_("Status changed to: %s") % status_label)
        return res

    def name_get(self):
        """Custom name display"""
        result = []
        for item in self:
            item_name = item.display_name or item.name
            if item.status != 'pending' and item.status and item._fields.get('status'):
                status_label = dict(item._fields['status'].selection).get(item.status, '')
                item_name = _('%s [%s]', item_name, status_label)
            result.append((item.id, item_name))
        return result

    # ============================================================================
    # INTEGRATION METHODS
    # ============================================================================

    def action_print_label(self):
        """Generate and print a label for the shred item"""
        self.ensure_one()
        return self.env.ref('records_management.shred_item_label_report').report_action(self)

