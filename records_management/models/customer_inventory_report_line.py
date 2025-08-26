# -*- coding: utf-8 -*-
"""
Customer Inventory Report Line Module

Represents a single line item within a customer inventory report, detailing
a specific container and its contents.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from datetime import datetime as py_datetime
from odoo.exceptions import ValidationError, UserError


class CustomerInventoryReportLine(models.Model):
    _name = 'customer.inventory.report.line'
    _description = 'Customer Inventory Report Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'report_id, container_id'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & RELATIONSHIPS
    # ============================================================================
    name = fields.Char(string="Line Reference", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    # Explicit comodel_name per project convention
    report_id = fields.Many2one(comodel_name='customer.inventory.report', string='Inventory Report', required=True, ondelete='cascade')
    partner_id = fields.Many2one(related='report_id.partner_id', string='Customer', store=True)
    report_date = fields.Date(related='report_id.report_date', string='Report Date', store=True)

    # ============================================================================
    # CONTAINER & DOCUMENT DETAILS
    # ============================================================================
    container_id = fields.Many2one('records.container', string='Container', required=True)
    location_id = fields.Many2one(related='container_id.location_id', string='Location', store=True)
    # Use a Char related to the container type name (the target is Char)
    container_type = fields.Char(related='container_id.container_type_id.name', string='Container Type', store=True)
    container_barcode = fields.Char(related='container_id.barcode', string='Barcode')
    container_volume_cf = fields.Float(related='container_id.cubic_feet', string='Volume (cf)')
    container_weight_lbs = fields.Float(related='container_id.weight', string='Weight (lbs)')
    document_type_id = fields.Many2one('records.document.type', string='Document Type')
    document_type = fields.Char(string="Document Type Name", related='document_type_id.name')
    document_count = fields.Integer(string='Document Count')
    # create_date on comodel is Datetime; related field type must match
    storage_date = fields.Datetime(string='Storage Start Date', related='container_id.create_date', store=True, readonly=True)
    last_access_date = fields.Date(string='Last Access', related='container_id.last_access_date')
    # Align to container model field name
    retention_date = fields.Date(string='Retention/Destruction Due Date', related='container_id.destruction_due_date', store=True)

    # ============================================================================
    # VERIFICATION & STATUS
    # ============================================================================
    document_count_verified = fields.Boolean(string='Count Verified')
    verification_date = fields.Date(string='Verification Date', readonly=True)
    verified_by_id = fields.Many2one('res.users', string='Verified By', readonly=True)
    line_status = fields.Selection([('ok', 'OK'), ('discrepancy', 'Discrepancy'), ('new', 'New')], string='Line Status', default='ok')
    billing_status = fields.Selection([('billed', 'Billed'), ('pending', 'Pending'), ('not_applicable', 'N/A')], string='Billing Status', default='pending')

    # ============================================================================
    # FINANCIALS
    # ============================================================================
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency')
    monthly_storage_cost = fields.Monetary(string='Monthly Storage Cost')
    total_storage_cost = fields.Monetary(string='Total Storage Cost', compute='_compute_total_storage_cost', store=True)
    storage_months = fields.Integer(string='Months in Storage', compute='_compute_storage_months', store=True)

    # ============================================================================
    # NOTES
    # ============================================================================
    description = fields.Text(string='Description')
    notes = fields.Text(string='Internal Notes')
    special_instructions = fields.Text(string='Special Instructions')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('container_id.name', 'container_id.barcode', 'document_count', 'document_type')
    def _compute_display_name(self):
        """Compute display name with container and document info"""
        for line in self:
            parts = []
            if line.container_id:
                parts.append(line.container_id.name or line.container_id.barcode or _('Unknown Container'))
            if line.document_count:
                parts.append(_("(%s docs)", line.document_count))
            if line.document_type:
                parts.append(line.document_type)
            line.display_name = " - ".join(filter(None, parts)) or _("New Line")

    @api.depends('storage_date', 'report_date')
    def _compute_storage_months(self):
        """Calculate number of months in storage"""
        for line in self:
            if line.storage_date and line.report_date:
                # storage_date is Datetime; compare by calendar month using date part
                sd_year = (line.storage_date.date().year if isinstance(line.storage_date, py_datetime) else line.storage_date.year)
                sd_month = (line.storage_date.date().month if isinstance(line.storage_date, py_datetime) else line.storage_date.month)
                years = line.report_date.year - sd_year
                months = line.report_date.month - sd_month
                total_months = years * 12 + months
                line.storage_months = max(total_months, 0)
            else:
                line.storage_months = 0

    @api.depends('monthly_storage_cost', 'storage_months')
    def _compute_total_storage_cost(self):
        """Calculate total storage cost based on months stored"""
        for line in self:
            line.total_storage_cost = line.monthly_storage_cost * line.storage_months

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('container_id')
    def _onchange_container_id(self):
        """Update fields when container changes"""
        if self.container_id:
            self.name = _("Inventory Line: %s") % (self.container_id.name or self.container_id.barcode)
            # Align with container's computed count
            self.document_count = self.container_id.document_count
            if self.container_id.document_ids:
                first_doc = self.container_id.document_ids[0]
                if first_doc.document_type_id:
                    self.document_type_id = first_doc.document_type_id

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        """Update document type field when type record changes"""
        if self.document_type_id:
            self.document_type = self.document_type_id.name
        else:
            self.document_type = False

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_verify_document_count(self):
        """Mark document count as verified"""
        self.ensure_one()
        self.write({
            'document_count_verified': True,
            'verification_date': fields.Date.today(),
            'verified_by_id': self.env.user.id
        })
    # Log verification in chatter
    self.message_post(body=_("Document count verified: %s documents.") % self.document_count)

    def action_update_from_container(self):
        """Update line data from current container state"""
        self.ensure_one()
        if not self.container_id:
            raise UserError(_("No container linked to update from."))
        actual_count = self.container_id.document_count
        if actual_count != self.document_count:
            old_count = self.document_count
            self.document_count = actual_count
            self.document_count_verified = False
            self.message_post(body=_("Document count updated from %s to %s (requires verification).") % (old_count, actual_count))

    def action_view_container(self):
        """View the related container"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Container Details'),
            'res_model': 'records.container',
            'res_id': self.container_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_documents(self):
        """View documents in the container"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Container Documents'),
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('container_id', '=', self.container_id.id)],
            'context': {'default_container_id': self.container_id.id},
        }

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('document_count')
    def _check_document_count(self):
        """Validate document count is non-negative"""
        for line in self:
            if line.document_count < 0:
                raise ValidationError(_("Document count cannot be negative."))

    @api.constrains('monthly_storage_cost')
    def _check_monthly_cost(self):
        """Validate monthly cost is non-negative"""
        for line in self:
            if line.monthly_storage_cost < 0:
                raise ValidationError(_("Monthly storage cost cannot be negative."))

    @api.constrains('storage_date', 'report_date')
    def _check_date_sequence(self):
        """Validate storage date is before report date"""
        for line in self:
            if line.storage_date and line.report_date:
                # Convert datetime to date for safe comparison with Date field
                sd = line.storage_date.date() if isinstance(line.storage_date, py_datetime) else line.storage_date
                if sd > line.report_date:
                    raise ValidationError(_("Storage date cannot be after report date."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default name"""
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                sequence = self.env['ir.sequence'].next_by_code('customer.inventory.report.line')
                vals['name'] = sequence or _('New Line')
        return super().create(vals_list)

    def write(self, vals):
        """Override write for tracking important changes"""
        res = super().write(vals)
        if 'document_count' in vals:
            for line in self:
                if not line.document_count_verified:
                    line.message_post(body=_("Document count changed to %s (verification required).") % line.document_count)
        return res

    def name_get(self):
        """Custom name display"""
        result = []
        for line in self:
            name = line.display_name
            result.append((line.id, name))
        return result


