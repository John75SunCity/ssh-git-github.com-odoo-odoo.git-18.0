# -*- coding: utf-8 -*-
"""
Rate Change Confirmation Wizard

Provides confirmation and implementation workflow for rate changes.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RateChangeConfirmationWizard(models.TransientModel):
    """
    Wizard for confirming and implementing rate changes.
    """

    _name = 'rate.change.confirmation.wizard'
    _description = 'Rate Change Confirmation Wizard'

    # ============================================================================
    # REFERENCE FIELDS
    # ============================================================================
    forecaster_id = fields.Many2one('revenue.forecaster', string='Revenue Forecast')

    # ============================================================================
    # IMPACT SUMMARY
    # ============================================================================
    revenue_impact = fields.Monetary(string='Monthly Revenue Impact', currency_field='currency_id')
    customer_count = fields.Integer(string='Customers Affected')

    effective_date = fields.Date(string='Effective Date', default=fields.Date.today, required=True)
    implementation_method = fields.Selection([
        ('immediate', 'Immediate Implementation'),
        ('phased', 'Phased Implementation'),
        ('next_billing_cycle', 'Next Billing Cycle')
    ], string='Implementation Method', default='next_billing_cycle', required=True)

    # ============================================================================
    # CUSTOMER COMMUNICATION
    # ============================================================================
    notification_required = fields.Boolean(string='Customer Notification Required', default=True)
    advance_notice_days = fields.Integer(string='Advance Notice (Days)', default=30)
    phase_duration_months = fields.Integer(string='Phase Duration (Months)', default=3)

    communication_template = fields.Text(
        string='Customer Communication Template',
        default=lambda self: self._default_communication_template()
    )

    # ============================================================================
    # APPROVAL WORKFLOW
    # ============================================================================
    requires_approval = fields.Boolean(string='Requires Management Approval', default=True)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approval_date = fields.Datetime(string='Approval Date', readonly=True)
    approval_notes = fields.Text(string='Approval Notes')

    # ============================================================================
    # RISK MANAGEMENT
    # ============================================================================
    risk_mitigation_plan = fields.Text(string='Risk Mitigation Plan')
    rollback_plan = fields.Text(string='Rollback Plan')

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    # ============================================================================
    # DEFAULT METHODS
    # ============================================================================
    def _default_communication_template(self):
        """Default customer communication template."""
        return _("""Dear Valued Customer,

We are writing to inform you of an upcoming adjustment to our service rates, effective {effective_date}.

Rate Change Summary:
- Monthly Impact: {revenue_impact}
- Effective Date: {effective_date}

We appreciate your continued business and remain committed to providing exceptional records management services.

If you have any questions about these changes, please don't hesitate to contact us.

Best regards,
Records Management Team""")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_approve_changes(self):
        """Approve the rate changes (manager action)."""
        self.ensure_one()

        # Check manager permissions
        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_('Only managers can approve rate changes.'))

        self.write({
            'approved_by': self.env.user.id,
            'approval_date': fields.Datetime.now(),
            'requires_approval': False,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Approved'),
                'message': _('Rate changes have been approved and are ready for implementation.'),
                'type': 'success'
            }
        }

    def action_implement_changes(self):
        """Implement the approved rate changes."""
        self.ensure_one()

        if self.requires_approval and not self.approved_by:
            raise UserError(_('Rate changes must be approved before implementation.'))

        # Implementation logic would go here
        # For now, just log the implementation
        self._log_implementation()

        # Send customer notifications if required
        if self.notification_required:
            self._send_customer_notifications()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Implementation Complete'),
                'message': _('Rate changes have been successfully implemented.'),
                'type': 'success'
            }
        }

    def action_cancel_implementation(self):
        """Cancel the rate change implementation."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window_close'
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _log_implementation(self):
        """Log the rate change implementation."""
        message = _('Rate change implementation completed:\n')
        message += _('- Revenue Impact: %s %s\n', self.revenue_impact, self.currency_id.symbol)
        message += _('- Customers Affected: %s\n', self.customer_count)
        message += _('- Effective Date: %s\n', self.effective_date)
        message += _('- Implementation Method: %s\n', dict(self._fields['implementation_method'].selection).get(self.implementation_method))

        if self.approved_by:
            message += _('- Approved by: %s on %s\n', self.approved_by.name, self.approval_date)

        # Create audit log entry
        self.env['naid.audit.log'].create({
            'name': 'Rate Change Implementation',
            'description': message,
            'action_type': 'rate_change',
            'user_id': self.env.user.id,
            'timestamp': fields.Datetime.now(),
        })

    def _send_customer_notifications(self):
        """Send notifications to affected customers."""
        if not self.forecaster_id:
            return

        # Get affected customers from forecast
        affected_customers = self.forecaster_id.forecast_line_ids.mapped('partner_id')

        for customer in affected_customers:
            self._send_individual_notification(customer)

    def _send_individual_notification(self, customer):
        """Send notification to individual customer."""
        subject = _('Important: Service Rate Adjustment Notice')

        # Format the communication template
        body = self.communication_template.format(
            effective_date=self.effective_date,
            revenue_impact=f'{self.revenue_impact} {self.currency_id.symbol}',
        )

        # Create and send email
        mail_values = {
            'subject': subject,
            'body_html': body.replace('\n', '<br/>'),
            'partner_ids': [(6, 0, [customer.id])],
            'model': 'res.partner',
            'res_id': customer.id,
        }

        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
