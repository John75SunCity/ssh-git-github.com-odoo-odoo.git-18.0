# -*- coding: utf-8 -*-
"""
Rate Change Confirmation Wizard
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RateChangeConfirmationWizard(models.TransientModel):
    """
    Rate Change Confirmation Wizard
    Confirms and applies rate changes from revenue forecasting
    """

    _name = 'rate.change.confirmation.wizard'
    _description = 'Rate Change Confirmation Wizard'

    # Reference to forecast
    forecast_id = fields.Many2one('revenue.forecaster', string='Forecast Reference', required=True)
    
    # Summary information
    revenue_impact = fields.Float(string='Annual Revenue Impact ($)', readonly=True)
    customer_count = fields.Integer(string='Customers Affected', readonly=True)
    
    # Confirmation details
    effective_date = fields.Date(string='Effective Date', default=fields.Date.today, required=True)
    notification_required = fields.Boolean(string='Send Customer Notifications', default=True)
    advance_notice_days = fields.Integer(string='Advance Notice (Days)', default=30)
    
    # Implementation options
    implementation_method = fields.Selection([
        ('immediate', 'Immediate Implementation'),
        ('phased', 'Phased Implementation'),
        ('gradual', 'Gradual Increase Over Time')
    ], string='Implementation Method', default='immediate', required=True)
    
    phase_duration_months = fields.Integer(string='Phase Duration (Months)', default=3)
    
    # Approval requirements
    requires_approval = fields.Boolean(string='Requires Management Approval', default=True)
    approved_by = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Date(string='Approval Date')
    approval_notes = fields.Text(string='Approval Notes')
    
    # Risk mitigation
    risk_mitigation_plan = fields.Text(string='Risk Mitigation Plan')
    rollback_plan = fields.Text(string='Rollback Plan')
    
    # Customer communication
    communication_template = fields.Text(string='Customer Communication Template',
                                        default=lambda self: self._get_default_communication_template())

    def _get_default_communication_template(self):
        """Get default customer communication template"""
        return """
Dear [CUSTOMER_NAME],

We are writing to inform you of upcoming changes to our service rates, effective [EFFECTIVE_DATE].

Rate Changes:
[RATE_DETAILS]

These adjustments reflect our continued commitment to providing exceptional service while managing operational costs.

If you have any questions or concerns, please contact us at [CONTACT_INFO].

Thank you for your continued business.

Sincerely,
[COMPANY_NAME]
        """.strip()

    def action_approve_changes(self):
        """Approve the rate changes"""
        self.ensure_one()
        
        if not self.env.user.has_group('records_management.group_records_manager'):
            raise ValidationError(_('Only managers can approve rate changes'))
        
        self.write({
            'approved_by': self.env.user.id,
            'approval_date': fields.Date.today()
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Rate changes approved successfully'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_implement_changes(self):
        """Implement the approved rate changes"""
        self.ensure_one()
        
        if self.requires_approval and not self.approved_by:
            raise ValidationError(_('Rate changes must be approved before implementation'))
        
        # Implement based on the forecast scenario
        forecast = self.forecast_id
        
        if forecast.scenario_type == 'global_increase':
            self._implement_global_changes(forecast)
        elif forecast.scenario_type == 'category_specific':
            self._implement_category_changes(forecast)
        elif forecast.scenario_type == 'customer_specific':
            self._implement_customer_changes(forecast)
        
        # Send notifications if required
        if self.notification_required:
            self._send_customer_notifications()
        
        # Log the implementation
        self._log_rate_change_implementation()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Rate changes implemented successfully'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _implement_global_changes(self, forecast):
        """Implement global rate changes"""
        # Update base rates
        base_rates = self.env['base.rates'].search([('state', '=', 'active')])
        
        for rate in base_rates:
            if forecast.global_adjustment_type == 'percentage':
                new_rate = rate.base_rate * (1 + forecast.global_adjustment_value / 100)
            else:
                new_rate = rate.base_rate + forecast.global_adjustment_value
            
            # Create new rate version
            rate.copy({
                'base_rate': new_rate,
                'effective_date': self.effective_date,
                'state': 'draft'
            }).action_activate()

    def _implement_category_changes(self, forecast):
        """Implement category-specific rate changes"""
        if not forecast.service_category:
            return
        
        # Update rates for specific category
        category_rates = self.env['base.rates'].search([
            ('service_category', '=', forecast.service_category),
            ('state', '=', 'active')
        ])
        
        for rate in category_rates:
            new_rate = rate.base_rate * (1 + forecast.category_adjustment_value / 100)
            
            rate.copy({
                'base_rate': new_rate,
                'effective_date': self.effective_date,
                'state': 'draft'
            }).action_activate()

    def _implement_customer_changes(self, forecast):
        """Implement customer-specific rate changes"""
        # Create or update customer rate profiles
        for customer in forecast.specific_customer_ids:
            # This would create negotiated rates for specific customers
            pass

    def _send_customer_notifications(self):
        """Send notifications to affected customers"""
        # Get affected customers
        customers = self._get_affected_customers()
        
        for customer in customers:
            # Prepare email content
            email_content = self._prepare_customer_email(customer)
            
            # Send email (this would integrate with Odoo's email system)
            self._send_customer_email(customer, email_content)

    def _get_affected_customers(self):
        """Get customers affected by rate changes"""
        return self.forecast_id._get_target_customers()

    def _prepare_customer_email(self, customer):
        """Prepare personalized email content for customer"""
        template = self.communication_template
        
        # Replace placeholders
        content = template.replace('[CUSTOMER_NAME]', customer.name)
        content = content.replace('[EFFECTIVE_DATE]', str(self.effective_date))
        content = content.replace('[CONTACT_INFO]', 'support@company.com')
        content = content.replace('[COMPANY_NAME]', self.env.company.name)
        
        return content

    def _send_customer_email(self, customer, content):
        """Send email to customer"""
        # This would use Odoo's mail system
        mail_values = {
            'subject': 'Important: Service Rate Update',
            'body_html': content.replace('\n', '<br>'),
            'email_to': customer.email,
            'email_from': self.env.company.email,
        }
        
        # Create and send mail
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

    def _log_rate_change_implementation(self):
        """Log the rate change implementation"""
        log_message = f"""
Rate Change Implementation:
- Forecast: {self.forecast_id.name}
- Revenue Impact: ${self.revenue_impact:,.2f}
- Customers Affected: {self.customer_count}
- Effective Date: {self.effective_date}
- Approved By: {self.approved_by.name if self.approved_by else 'N/A'}
- Implementation Method: {self.implementation_method}
        """.strip()
        
        # Log to system or create audit record
        self.env['mail.thread'].message_post(
            body=log_message,
            subject='Rate Change Implementation'
        )

    def action_generate_implementation_report(self):
        """Generate detailed implementation report"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.report',
            'report_name': 'records_management.rate_change_implementation_report',
            'report_type': 'qweb-pdf',
            'data': {
                'wizard_id': self.id,
                'forecast_data': self.forecast_id.read()[0]
            },
            'context': self.env.context,
        }

    def action_cancel_implementation(self):
        """Cancel the rate change implementation"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Rate change implementation cancelled'),
                'type': 'warning',
                'sticky': False,
            }
        }

    @api.constrains('effective_date')
    def _check_effective_date(self):
        """Validate effective date"""
        for record in self:
            if record.effective_date < fields.Date.today():
                raise ValidationError(_('Effective date cannot be in the past'))
            
            if record.notification_required:
                notice_date = fields.Date.today() + fields.timedelta(days=record.advance_notice_days)
                if record.effective_date < notice_date:
                    raise ValidationError(_('Effective date must allow for adequate customer notice period'))
