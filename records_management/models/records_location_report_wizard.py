from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class GeneratedModel(models.Model):
    _name = 'records.location.report.wizard'
    _description = 'Records Location Report Wizard'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    location_id = fields.Many2one()
    include_child_locations = fields.Boolean()
    specific_location_ids = fields.Many2many()
    report_date = fields.Date()
    include_date_range = fields.Boolean()
    date_from = fields.Date()
    date_to = fields.Date()
    customer_filter = fields.Selection()
    specific_customer_ids = fields.Many2many()
    department_id = fields.Many2one()
    include_container_details = fields.Boolean()
    include_utilization_stats = fields.Boolean()
    include_financial_summary = fields.Boolean()
    include_charts = fields.Boolean()
    output_format = fields.Selection()
    email_report = fields.Boolean()
    email_recipients = fields.Char()
    location_name = fields.Char()
    total_capacity = fields.Float()
    current_utilization = fields.Float()
    container_count = fields.Integer()
    customer_count = fields.Integer()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_location_summary(self):
            """Compute location summary statistics"""
            for wizard in self:
                if not wizard.location_id:
                    wizard.total_capacity = 0.0
                    wizard.current_utilization = 0.0
                    wizard.container_count = 0
                    wizard.customer_count = 0
                    continue

                # Build location domain
                location_domain = [('id', '=', wizard.location_id.id)]
                if wizard.include_child_locations and wizard.location_id.child_ids:
                    child_ids = wizard.location_id.child_ids.ids
                    location_domain = [('id', 'in', [wizard.location_id.id] + child_ids)]

                # Get containers for these locations:
                containers = self.env['records.container'].search([)]
                    ('location_id', 'in', [loc.id for loc in self.env['records.location'].search(location_domain)]),:
                    ('active', '=', True)


                # Calculate statistics
                wizard.total_capacity = sum(containers.mapped('volume') or [0.0])
                wizard.container_count = len(containers)
                wizard.customer_count = len(containers.mapped('partner_id'))

                # Calculate utilization (containers vs location capacity)
                if wizard.location_id.capacity_cubic_feet > 0:
                    wizard.current_utilization = (wizard.total_capacity / wizard.location_id.capacity_cubic_feet) * 100
                else:
                    wizard.current_utilization = 0.0

        # ============================================================================
            # CONSTRAINT VALIDATIONS
        # ============================================================================

    def _check_date_range(self):
            """Validate date range configuration"""
            for wizard in self:
                if wizard.include_date_range:
                    if not wizard.date_from or not wizard.date_to:
                        raise ValidationError(_('Both From Date and To Date are required for date range analysis')):
                    if wizard.date_from > wizard.date_to:
                        raise ValidationError(_('From Date must be earlier than To Date'))


    def _check_customers(self):
            """Validate customer selection"""
            for wizard in self:
                if wizard.customer_filter == 'specific' and not wizard.specific_customer_ids:
                    raise ValidationError(_('Please select at least one customer for specific customer filter')):

    def _check_email(self):
            """Validate email configuration"""
            for wizard in self:
                if wizard.email_report and not wizard.email_recipients:
                    raise ValidationError(_('Email recipients are required when email report is enabled'))

        # ============================================================================
            # ONCHANGE METHODS
        # ============================================================================

    def _onchange_customer_filter(self):
            """Clear customer selections when filter changes"""
            if self.customer_filter != 'specific':
                self.specific_customer_ids = [(5, 0, 0)]
            if self.customer_filter != 'department':
                self.department_id = False

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_generate_report(self):
            """Generate and return the location report"""
            self.ensure_one()
            self._validate_report_parameters()

            # Generate the report data
            report_data = self._prepare_report_data()

            if self.output_format == 'pdf':
                return self._generate_pdf_report(report_data)
            elif self.output_format == 'excel':
                return self._generate_excel_report(report_data)
            elif self.output_format == 'html':
                return self._generate_html_report(report_data)
            else:  # both
                # Generate both formats and email them
                pdf_report = self._generate_pdf_report(report_data)
                excel_report = self._generate_excel_report(report_data)

                if self.email_report:
                    self._email_reports([pdf_report, excel_report])

                return pdf_report


    def _validate_report_parameters(self):
            """Validate all report parameters before generation"""
            if not self.location_id:
                raise ValidationError(_('Location is required for report generation')):
            if self.customer_filter == 'specific' and not self.specific_customer_ids:
                raise ValidationError(_('Please select specific customers'))


    def _prepare_report_data(self):
            """Prepare comprehensive report data"""
            return {}
                'wizard': self,
                'location_data': self._get_location_data(),
                'container_data': self._get_container_data(),
                'customer_data': self._get_customer_data(),
                'utilization_data': self._get_utilization_data(),
                'financial_data': self._get_financial_data() if self.include_financial_summary else {},:
                'generated_date': fields.Datetime.now(),
                'report_parameters': self._get_report_parameters()



    def _get_location_data(self):
            """Get location-specific data"""
            locations = [self.location_id]
            if self.include_child_locations:
                locations.extend(self.location_id.child_ids)

            return [{]}
                'location': loc,
                'containers': self.env['records.container'].search([('location_id', '=', loc.id)]),
                'capacity': loc.capacity_cubic_feet,
                'utilization': loc.utilization_percentage


    def _get_container_data(self):
            """Get container inventory data"""
            # Implementation would include container details, types, conditions, etc.
            return {}


    def _get_customer_data(self):
            """Get customer distribution data"""
            # Implementation would include customer analytics
            return {}


    def _get_utilization_data(self):
            """Get utilization statistics"""
            # Implementation would include detailed utilization analysis
            return {}


    def _get_financial_data(self):
            """Get financial summary data"""
            # Implementation would include revenue, billing, costs
            return {}


    def _get_report_parameters(self):
            """Get formatted report parameters"""
            return {}
                'report_name': self.name,
                'report_date': self.report_date,
                'location': self.location_id.name,
                'customer_filter': dict(self._fields['customer_filter'].selection)[self.customer_filter],
                'include_children': self.include_child_locations,
                'output_format': dict(self._fields['output_format'].selection)[self.output_format]



    def _generate_pdf_report(self, report_data):
            """Generate PDF report"""
            return self.env.ref('records_management.location_report_pdf').report_action()
                self, data=report_data



    def _generate_excel_report(self, report_data):
            """Generate Excel report"""
            # Implementation for Excel generation:
            return {}
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {}
                    'message': _('Excel report generation feature coming soon'),
                    'type': 'info'




    def _generate_html_report(self, report_data):
            """Generate HTML report"""
            # Implementation for HTML generation:
            return {}
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {}
                    'message': _('HTML report generation feature coming soon'),
                    'type': 'info'




    def _email_reports(self, reports):
            """Email reports to specified recipients"""
            if not self.email_recipients:
                return False

            # Basic email implementation
            mail_template = self.env.ref('records_management.location_report_email_template', raise_if_not_found=False)
            if mail_template:
                mail_template.send_mail(self.id, force_send=True)
            return True

