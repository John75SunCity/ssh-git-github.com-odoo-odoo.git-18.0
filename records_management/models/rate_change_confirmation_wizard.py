# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RateChangeConfirmationWizard(models.TransientModel):
    """Wizard for approving and implementing rate changes"""
    _name = 'rate.change.confirmation.wizard'
    _description = 'Rate Change Confirmation Wizard'

    # Wizard fields
    current_rate = fields.Float(string="Current Rate", readonly=True)
    new_rate = fields.Float(string="New Rate", required=True)
    effective_date = fields.Date(string="Effective Date", required=True, default=fields.Date.today)
    reason = fields.Text(string="Reason for Change", required=True)

    # Related billing configuration
    billing_config_id = fields.Many2one('records.billing.config', string="Billing Configuration", required=True)
    partner_id = fields.Many2one(related='billing_config_id.partner_id', string="Customer", readonly=True)

    # Approval tracking
    approved_by_id = fields.Many2one('res.users', string="Approved By", readonly=True)
    approved_date = fields.Datetime(string="Approval Date", readonly=True)
    is_approved = fields.Boolean(string="Approved", default=False)

    def action_approve_changes(self):
        """Approve the rate changes"""
        self.ensure_one()
        self.write({
            'is_approved': True,
            'approved_by_id': self.env.user.id,
            'approved_date': fields.Datetime.now(),
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Rate Change Approved'),
                'message': _('Rate change has been approved. You can now implement the changes.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_implement_changes(self):
        """Implement the approved rate changes"""
        self.ensure_one()

        if not self.is_approved:
            raise UserError(_("Rate changes must be approved before implementation."))

        # Update the billing configuration with new rate
        self.billing_config_id.write({
            'storage_fee_rate': self.new_rate,
        })

        # Log the change in audit trail
        self.env['naid.audit.log'].create({
            'action_type': 'rate_change',
            'model_name': 'records.billing.config',
            'record_id': self.billing_config_id.id,
            'user_id': self.env.user.id,
            'description': _('Rate changed from %s to %s. Reason: %s') % (self.current_rate, self.new_rate, self.reason),
            'partner_id': self.partner_id.id,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Rate Change Implemented'),
                'message': _('New rate of %s has been successfully implemented.') % self.new_rate,
                'type': 'success',
                'sticky': False,
            }
        }
