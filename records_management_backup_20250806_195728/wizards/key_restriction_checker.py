# -*- coding: utf-8 -*-
"""
Key Restriction Checker Wizard
For technicians to quickly check if a customer can receive keys
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class KeyRestrictionChecker(models.TransientModel):
    """
    Quick checker for technicians to verify key issuance permissions
    """

    _name = 'key.restriction.checker'
    _description = 'Key Restriction Checker'

    # ==========================================
    # INPUT FIELDS
    # ==========================================

    customer_name = fields.Char(string='Customer Name', help='Start typing customer name')
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                domain=[('is_company', '=', True)])
    bin_identifier = fields.Char(string='Bin Identifier', help='Bin number or identifier')

    # ==========================================
    # RESULT FIELDS
    # ==========================================

    check_performed = fields.Boolean(string='Check Performed', default=False)
    key_allowed = fields.Boolean(string='Key Issuance Allowed')
    restriction_reason = fields.Selection([
        ('policy', 'Company Policy'),
        ('security', 'Security Requirements'),
        ('compliance', 'Compliance Requirements'),
        ('contract', 'Contract Terms'),
        ('risk', 'Risk Assessment'),
        ('other', 'Other')
    ], string='Restriction Reason', readonly=True)

    restriction_notes = fields.Text(string='Restriction Notes', readonly=True)
    restriction_date = fields.Date(string='Restriction Effective Date', readonly=True)

    # Display fields
    status_message = fields.Html(string='Status', readonly=True)
    action_required = fields.Html(string='Action Required', readonly=True)

    # ==========================================
    # ACTIONS
    # ==========================================

    def action_check_customer(self):
        """Check customer key restriction status"""
        self.ensure_one()

        if not self.customer_id:
            raise UserError(_('Please select a customer first'))

        # Get customer restriction info
        customer = self.customer_id

        # Update result fields
        self.write({
            'check_performed': True,
            'key_allowed': customer.key_issuance_allowed,
            'restriction_reason': customer.key_restriction_reason,
            'restriction_notes': customer.key_restriction_notes,
            'restriction_date': customer.key_restriction_date,
        })

        # Generate status message
        if customer.key_issuance_allowed:
            status_html = """
                <div class="alert alert-success" role="alert">
                    <i class="fa fa-check-circle"></i>
                    <strong>KEY ISSUANCE ALLOWED</strong>
                    <br/>Customer: <strong>%s</strong>
                    <br/>You may issue bin keys to this customer's authorized personnel.
                </div>
            """ % customer.name

            action_html = """
                <div class="alert alert-info">
                    <strong>Instructions:</strong>
                    <ul>
                        <li>Verify the person's identity and authorization</li>
                        <li>Record the key issuance in the system</li>
                        <li>Provide standard key handling instructions</li>
                    </ul>
                </div>
            """
        else:
            reason_text = dict(self._fields['restriction_reason'].selection).get(
                customer.key_restriction_reason, 'Not specified'
            )

            status_html = """
                <div class="alert alert-danger" role="alert">
                    <i class="fa fa-ban"></i>
                    <strong>KEY ISSUANCE RESTRICTED</strong>
                    <br/>Customer: <strong>%s</strong>
                    <br/>Restriction Reason: <strong>%s</strong>
                    <br/>Effective Date: %s
                </div>
            """ % (
                customer.name, 
                reason_text,
                customer.key_restriction_date.strftime('%B %d, %Y') if customer.key_restriction_date else 'Not specified'
            )

            action_html = """
                <div class="alert alert-warning">
                    <strong>Required Action:</strong>
                    <ul>
                        <li><strong>DO NOT</strong> issue keys to this customer</li>
                        <li>Create a bin unlock service request instead</li>
                        <li>Explain the restriction policy to the customer</li>
                        <li>Offer alternative service options</li>
                    </ul>
                </div>
            """

        self.write({
            'status_message': status_html,
            'action_required': action_html
        })

        # Return updated form view
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'key.restriction.checker',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context
        }

    def action_create_unlock_service(self):
        """Create bin unlock service for restricted customer"""
        self.ensure_one()

        if not self.customer_id:
            raise UserError(_('Please select a customer first'))

        if self.customer_id.key_issuance_allowed:
            raise UserError(_('Customer is not restricted from receiving keys'))

        if not self.bin_identifier:
            raise UserError(_('Please enter bin identifier'))

        # Create bin unlock service
        unlock_service = self.env['bin.unlock.service'].create({
            'customer_id': self.customer_id.id,
            'bin_identifier': self.bin_identifier,
            'unlock_reason_code': 'key_restriction',
            'reason': _('Customer is restricted from receiving keys. Service requested by technician.'),
            'urgency': 'normal',
            'approval_required': True,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Bin Unlock Service'),
            'res_model': 'bin.unlock.service',
            'res_id': unlock_service.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.onchange('customer_name')
    def _onchange_customer_name(self):
        """Auto-search customers by name"""
        if self.customer_name and len(self.customer_name) >= 3:
            customers = self.env['res.partner'].search([
                ('name', 'ilike', self.customer_name),
                ('is_company', '=', True)
            ], limit=10)

            if len(customers) == 1:
                self.customer_id = customers[0]

    def action_reset(self):
        """Reset the checker"""
        self.write({
            'customer_name': False,
            'customer_id': False,
            'bin_identifier': False,
            'check_performed': False,
            'key_allowed': False,
            'restriction_reason': False,
            'restriction_notes': False,
            'restriction_date': False,
            'status_message': False,
            'action_required': False,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'key.restriction.checker',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context
        }
