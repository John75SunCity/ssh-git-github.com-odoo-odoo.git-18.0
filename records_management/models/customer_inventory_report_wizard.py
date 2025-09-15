from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class CustomerInventoryReportWizard(models.TransientModel):
    """
    Wizard for generating customer inventory reports.
    
    This wizard allows users to generate various types of inventory reports
    for customers, including container summaries, document counts, and billing reports.
    """
    
    _name = 'customer.inventory.report.wizard'
    _description = 'Customer Inventory Report Wizard'

    # Report Parameters
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
        domain=[('is_company', '=', True)],
        help='Select the customer for the inventory report'
    )
    
    report_type = fields.Selection([
        ('summary', 'Inventory Summary'),
        ('detailed', 'Detailed Inventory'),
        ('containers', 'Container Report'),
        ('documents', 'Document Report'),
        ('billing', 'Billing Report'),
        ('movement', 'Movement History'),
        ('compliance', 'Compliance Report')
    ], string='Report Type', required=True, default='summary')
    
    # Date Range
    date_from = fields.Date(
        string='From Date',
        default=lambda self: fields.Date.today() - timedelta(days=30),
        required=True
    )
    
    date_to = fields.Date(
        string='To Date',
        default=fields.Date.today,
        required=True
    )
    
    # Filters
    department_ids = fields.Many2many(
        comodel_name='records.department',
        string='Departments',
        help='Filter by specific departments (leave empty for all)'
    )
    
    location_ids = fields.Many2many(
        comodel_name='records.location',
        string='Locations',
        help='Filter by specific locations (leave empty for all)'
    )
    
    container_types = fields.Many2many(
        comodel_name='records.container.type',
        string='Container Types',
        help='Filter by container types (leave empty for all)'
    )
    
    # Report Options
    include_inactive = fields.Boolean(
        string='Include Inactive Records',
        default=False,
        help='Include inactive containers and documents'
    )
    
    include_images = fields.Boolean(
        string='Include Images',
        default=False,
        help='Include container and document images in the report'
    )
    
    group_by_department = fields.Boolean(
        string='Group by Department',
        default=True,
        help='Group results by department'
    )
    
    group_by_location = fields.Boolean(
        string='Group by Location',
        default=False,
        help='Group results by location'
    )
    
    # Output Options
    output_format = fields.Selection([
        ('pdf', 'PDF'),
        ('xlsx', 'Excel Spreadsheet'),
        ('csv', 'CSV File')
    ], string='Output Format', default='pdf', required=True)
    
    email_report = fields.Boolean(
        string='Email Report',
        default=False,
        help='Email the report to customer contact'
    )
    
    email_to = fields.Char(
        string='Email To',
        help='Email address to send report (defaults to customer email)'
    )
    
    # Computed Fields
    total_containers = fields.Integer(
        string='Total Containers',
        compute='_compute_totals',
        help='Total number of containers for this customer'
    )
    
    total_documents = fields.Integer(
        string='Total Documents',
        compute='_compute_totals',
        help='Total number of documents for this customer'
    )
    
    estimated_report_size = fields.Char(
        string='Estimated Report Size',
        compute='_compute_estimated_size',
        help='Estimated size of the generated report'
    )

    @api.depends('partner_id', 'date_from', 'date_to', 'department_ids', 'location_ids')
    def _compute_totals(self):
        """Compute total containers and documents"""
        for wizard in self:
            if not wizard.partner_id:
                wizard.total_containers = 0
                wizard.total_documents = 0
                continue
            
            # Build domain for containers
            container_domain = [('partner_id', '=', wizard.partner_id.id)]
            if wizard.department_ids:
                container_domain.append(('department_id', 'in', wizard.department_ids.ids))
            if wizard.location_ids:
                container_domain.append(('location_id', 'in', wizard.location_ids.ids))
            if not wizard.include_inactive:
                container_domain.append(('active', '=', True))
            
            # Count containers
            wizard.total_containers = self.env['records.container'].search_count(container_domain)
            
            # Build domain for documents
            document_domain = [('partner_id', '=', wizard.partner_id.id)]
            if wizard.date_from:
                document_domain.append(('create_date', '>=', wizard.date_from))
            if wizard.date_to:
                document_domain.append(('create_date', '<=', wizard.date_to))
            if not wizard.include_inactive:
                document_domain.append(('active', '=', True))
            
            # Count documents
            wizard.total_documents = self.env['records.document'].search_count(document_domain)
    
    @api.depends('total_containers', 'total_documents', 'include_images', 'output_format')
    def _compute_estimated_size(self):
        """Estimate the size of the generated report"""
        for wizard in self:
            base_size = wizard.total_containers * 0.5 + wizard.total_documents * 0.2  # KB
            
            if wizard.include_images:
                base_size += wizard.total_containers * 50  # Add 50KB per container for images
            
            if wizard.output_format == 'pdf':
                base_size *= 1.5  # PDF overhead
            elif wizard.output_format == 'xlsx':
                base_size *= 1.2  # Excel overhead
            
            if base_size < 1024:
                wizard.estimated_report_size = f"{int(base_size)} KB"
            else:
                wizard.estimated_report_size = f"{base_size/1024:.1f} MB"

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update email_to when partner changes"""
        if self.partner_id and self.partner_id.email:
            self.email_to = self.partner_id.email

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Validate date range"""
        for wizard in self:
            if wizard.date_from > wizard.date_to:
                raise ValidationError(_("From Date cannot be later than To Date."))
            
            # Check for reasonable date range (not more than 2 years)
            if (wizard.date_to - wizard.date_from).days > 730:
                raise ValidationError(_("Date range cannot exceed 2 years."))

    def action_generate_report(self):
        """Generate the inventory report"""
        self.ensure_one()
        
        # Validate requirements
        if not self.partner_id:
            raise ValidationError(_("Please select a customer."))
        
        if self.total_containers == 0 and self.total_documents == 0:
            raise UserError(_("No data found for the selected criteria."))
        
        # Generate report based on type
        if self.report_type == 'summary':
            return self._generate_summary_report()
        elif self.report_type == 'detailed':
            return self._generate_detailed_report()
        elif self.report_type == 'containers':
            return self._generate_container_report()
        elif self.report_type == 'documents':
            return self._generate_document_report()
        elif self.report_type == 'billing':
            return self._generate_billing_report()
        elif self.report_type == 'movement':
            return self._generate_movement_report()
        elif self.report_type == 'compliance':
            return self._generate_compliance_report()
        else:
            return self._generate_summary_report()
    
    def _generate_summary_report(self):
        """Generate summary inventory report"""
        # Prepare data
        data = {
            'partner_id': self.partner_id.id,
            'partner_name': self.partner_id.name,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'report_type': self.report_type,
            'output_format': self.output_format,
            'include_inactive': self.include_inactive,
            'department_ids': self.department_ids.ids,
            'location_ids': self.location_ids.ids,
            'total_containers': self.total_containers,
            'total_documents': self.total_documents
        }
        
        if self.output_format == 'pdf':
            return self.env.ref('records_management.report_customer_inventory_summary').report_action(self, data=data)
        elif self.output_format == 'xlsx':
            return self._generate_excel_report(data)
        else:  # CSV
            return self._generate_csv_report(data)
    
    def _generate_detailed_report(self):
        """Generate detailed inventory report"""
        # Similar to summary but with more detail
        return self._generate_summary_report()
    
    def _generate_container_report(self):
        """Generate container-focused report"""
        return self._generate_summary_report()
    
    def _generate_document_report(self):
        """Generate document-focused report"""
        return self._generate_summary_report()
    
    def _generate_billing_report(self):
        """Generate billing report"""
        return self._generate_summary_report()
    
    def _generate_movement_report(self):
        """Generate movement history report"""
        return self._generate_summary_report()
    
    def _generate_compliance_report(self):
        """Generate compliance report"""
        return self._generate_summary_report()
    
    def _generate_excel_report(self, data):
        """Generate Excel report"""
        # This would use xlsxwriter or similar to create Excel file
        # For now, return PDF fallback
        return self.env.ref('records_management.report_customer_inventory_summary').report_action(self, data=data)
    
    def _generate_csv_report(self, data):
        """Generate CSV report"""
        # This would generate CSV data
        # For now, return PDF fallback
        return self.env.ref('records_management.report_customer_inventory_summary').report_action(self, data=data)
