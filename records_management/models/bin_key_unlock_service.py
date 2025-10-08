# -*- coding: utf-8 -*-
"""
Bin Key Unlock Service Module

Manages requests for unlocking secure bins, typically performed by a technician.
This model tracks the service from request to completion, including billing.

Author: Records Management System
Version: 19.0.0.1
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BinKeyUnlockService(models.Model):
    _name = 'bin.key.unlock.service'
    _description = 'Bin Key Unlock Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_date desc, id desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION & WORKFLOW
    # ============================================================================
    name = fields.Char(
        string='Service Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('billed', 'Billed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    # ============================================================================
    # SERVICE DETAILS
    # ============================================================================
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, tracking=True)
    technician_id = fields.Many2one(comodel_name='res.users', string='Technician', tracking=True)
    service_date = fields.Datetime(string='Service Date', default=fields.Datetime.now, tracking=True)
    completion_date = fields.Datetime(string='Completion Date', readonly=True)
    unlock_reason = fields.Selection([
        ('lost_key', 'Lost Key'),
        ('forgotten_code', 'Forgotten Code'),
        ('malfunction', 'Bin/Lock Malfunction'),
        ('emergency_access', 'Emergency Access'),
        ('other', 'Other')
    ], string='Reason for Unlock', required=True, tracking=True)
    unlock_reason_description = fields.Text(string='Reason Description')
    items_retrieved = fields.Text(string='Items Retrieved/Inspected')
    service_notes = fields.Text(string='Service Notes')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True)

    # ============================================================================
    # LOCATION & ASSET
    # ============================================================================
    shred_bin_id = fields.Many2one(comodel_name='shred.bin', string='Associated Bin')
    bin_key_id = fields.Many2one(comodel_name='bin.key', string='Associated Key')
    unlock_bin_location = fields.Char(string='Bin Location Description', help="Physical location of the bin, e.g., 'Office 201, 2nd Floor'.")

    # ============================================================================
    # FINANCIALS
    # ============================================================================
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency')
    unlock_charge = fields.Monetary(string='Service Charge', tracking=True, currency_field='currency_id')
    billable = fields.Boolean(string='Billable Service', default=True)
    invoice_id = fields.Many2one(comodel_name='account.move', string='Invoice', readonly=True, copy=False)

    # ============================================================================
    # ATTACHMENTS & VERIFICATION
    # ============================================================================
    photo_ids = fields.Many2many(
        'ir.attachment',
        'bin_unlock_service_attachment_rel',
        'service_id', 'attachment_id',
        string='Verification Photos'
    )
    identity_verified = fields.Boolean(string='Identity Verified', help="Check if the technician verified the identity of the person requesting access.")
    witness_id = fields.Many2one(comodel_name='res.partner', string='Witness')

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        self.ensure_one()
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Service request confirmed."))

    def action_start_service(self):
        self.ensure_one()
        self.write({'state': 'in_progress', 'technician_id': self.env.user.id})
        self.message_post(body=_("Service is now in progress."))

    def action_complete_service(self):
        self.ensure_one()
        self.write({'state': 'done', 'completion_date': fields.Datetime.now()})
        self.message_post(body=_("Service has been completed."))

    def action_create_invoice(self):
        self.ensure_one()
        if not self.billable:
            raise UserError(_("This service is not marked as billable."))
        if self.invoice_id:
            raise UserError(_("An invoice already exists for this service."))
        if self.state != 'done':
            raise UserError(_("Service must be completed before invoicing."))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': _("Bin Unlock Service: %s", self.name),
                'quantity': 1,
                'price_unit': self.unlock_charge,
            })],
        })
        self.write({'invoice_id': invoice.id, 'state': 'billed'})
        self.message_post(body=_('Invoice created: %s') % invoice.name)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Service request cancelled."))

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
        self.message_post(body=_("Service reset to draft."))

    # ------------------------------------------------------------------
    # VIEW SUPPORT PLACEHOLDERS (Referenced by XML buttons)
    # ------------------------------------------------------------------
    def action_view_access_history(self):
        """Placeholder action for viewing access history related to this service.

        Adjust res_model / domain if a dedicated access history model exists.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Unlock Service'),
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def action_view_service_history(self):
        """Placeholder action for viewing service history records.

    (Legacy unlock.service.history model fully merged; historical reference removed.)
        if/when implemented.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Unlock Services'),
            'res_model': self._name,
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_partner_id': self.partner_id.id}
        }
    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Generate a sequence number for new service requests."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('bin.key.unlock.service') or 'New'
        return super().create(vals_list)
