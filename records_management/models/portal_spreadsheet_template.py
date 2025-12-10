# -*- coding: utf-8 -*-
"""
Portal Spreadsheet Templates Model

Provides configurable import/export templates for the customer portal.
Templates can be created by administrators and made available to portal users
for data import/export operations.

Templates support:
- Containers import/export
- Files import/export
- Documents import/export
- Users import/export
- Custom data types
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import base64
import io
import logging

_logger = logging.getLogger(__name__)


class PortalSpreadsheetTemplate(models.Model):
    _name = 'portal.spreadsheet.template'
    _description = 'Portal Spreadsheet Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(
        string='Template Name',
        required=True,
        tracking=True,
        help='Descriptive name for this template'
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True, tracking=True)

    template_type = fields.Selection([
        ('containers', 'Containers'),
        ('files', 'File Folders'),
        ('documents', 'Documents'),
        ('users', 'Portal Users'),
        ('inventory', 'Inventory Items'),
        ('requests', 'Service Requests'),
        ('custom', 'Custom'),
    ], string='Template Type', required=True, default='containers', tracking=True)

    format = fields.Selection([
        ('xlsx', 'Excel (.xlsx)'),
        ('csv', 'CSV (.csv)'),
    ], string='File Format', required=True, default='xlsx')

    description = fields.Text(
        string='Description',
        help='Detailed description of what this template is for and how to use it'
    )

    # Template file storage
    template_file = fields.Binary(
        string='Template File',
        attachment=True,
        help='Pre-configured template file for download'
    )
    template_filename = fields.Char(string='Template Filename')

    # Column configuration (JSON stored)
    column_config = fields.Text(
        string='Column Configuration',
        help='JSON configuration for template columns'
    )

    # Access control
    portal_visible = fields.Boolean(
        string='Visible in Portal',
        default=True,
        help='Make this template available for download in the customer portal'
    )

    requires_admin = fields.Boolean(
        string='Requires Admin',
        default=False,
        help='Only company administrators can use this template'
    )

    # Related partner (for customer-specific templates)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        help='If set, this template is only available to this customer'
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    # Usage tracking
    download_count = fields.Integer(
        string='Downloads',
        default=0,
        readonly=True,
        help='Number of times this template has been downloaded'
    )

    last_download_date = fields.Datetime(
        string='Last Downloaded',
        readonly=True
    )

    # Import statistics
    import_count = fields.Integer(
        string='Imports',
        default=0,
        readonly=True,
        help='Number of times data has been imported using this template'
    )

    last_import_date = fields.Datetime(
        string='Last Import',
        readonly=True
    )

    # Column definitions
    column_ids = fields.One2many(
        comodel_name='portal.spreadsheet.template.column',
        inverse_name='template_id',
        string='Columns'
    )

    # Instructions
    instructions = fields.Html(
        string='Instructions',
        help='HTML instructions displayed to users when downloading this template'
    )

    @api.constrains('column_config')
    def _check_column_config(self):
        """Validate JSON column configuration"""
        import json
        for record in self:
            if record.column_config:
                try:
                    json.loads(record.column_config)
                except (json.JSONDecodeError, TypeError) as e:
                    raise ValidationError(_("Invalid column configuration JSON: %s") % str(e))

    def action_generate_template(self):
        """Generate template file based on column configuration"""
        self.ensure_one()

        if self.format == 'xlsx':
            file_data, filename = self._generate_xlsx_template()
        else:
            file_data, filename = self._generate_csv_template()

        self.write({
            'template_file': file_data,
            'template_filename': filename,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Template Generated'),
                'message': _("Template '%s' has been generated successfully.") % self.name,
                'type': 'success',
                'sticky': False,
            }
        }

    def _generate_xlsx_template(self):
        """Generate Excel template file"""
        from odoo.tools.misc import xlsxwriter

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(self.template_type.title())

        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1,
            'text_wrap': True,
            'valign': 'vcenter'
        })

        instruction_format = workbook.add_format({
            'italic': True,
            'font_color': '#666666',
            'text_wrap': True,
            'valign': 'top'
        })

        required_format = workbook.add_format({
            'bg_color': '#FFF2CC',
            'border': 1
        })

        # Get columns - either from column_ids or default config
        columns = self._get_template_columns()

        # Write headers and instructions
        for col_idx, col_def in enumerate(columns):
            header = col_def['name']
            if col_def.get('required'):
                header += '*'

            worksheet.write(0, col_idx, header, header_format)
            worksheet.write(1, col_idx, col_def.get('instruction', ''), instruction_format)
            worksheet.set_column(col_idx, col_idx, col_def.get('width', 20))

            # Add sample data if provided
            if col_def.get('sample'):
                worksheet.write(2, col_idx, col_def['sample'])

        # Set row heights
        worksheet.set_row(0, 25)  # Header row
        worksheet.set_row(1, 40)  # Instruction row

        # Freeze header rows
        worksheet.freeze_panes(2, 0)

        workbook.close()
        output.seek(0)

        filename = '%s_template.xlsx' % self.template_type
        return base64.b64encode(output.read()), filename

    def _generate_csv_template(self):
        """Generate CSV template file"""
        import csv

        output = io.StringIO()
        writer = csv.writer(output)

        # Get columns
        columns = self._get_template_columns()

        # Write headers
        headers = []
        for col_def in columns:
            header = col_def['name']
            if col_def.get('required'):
                header += '*'
            headers.append(header)
        writer.writerow(headers)

        # Write instructions row
        instructions = [col_def.get('instruction', '') for col_def in columns]
        writer.writerow(instructions)

        # Write sample row if available
        samples = [col_def.get('sample', '') for col_def in columns]
        if any(samples):
            writer.writerow(samples)

        filename = '%s_template.csv' % self.template_type
        return base64.b64encode(output.getvalue().encode('utf-8')), filename

    def _get_template_columns(self):
        """Get column definitions for this template"""
        # First check if custom columns are defined
        if self.column_ids:
            return [{
                'name': col.name,
                'field_name': col.field_name,
                'required': col.required,
                'instruction': col.instruction,
                'sample': col.sample_value,
                'width': col.width,
            } for col in self.column_ids.sorted(key=lambda c: c.sequence)]

        # Otherwise return default columns based on template type
        return self._get_default_columns()

    def _get_default_columns(self):
        """Get default column configuration based on template type"""
        from datetime import datetime, timedelta
        current_year = datetime.now().strftime('%Y')
        retention_year = (datetime.now() + timedelta(days=7*365)).strftime('%Y')

        defaults = {
            'containers': [
                {'name': 'Container Number', 'field_name': 'name', 'required': True,
                 'instruction': 'Required. Unique identifier (e.g., BOX-2024-001)',
                 'sample': 'BOX-%s-001' % current_year, 'width': 20},
                {'name': 'Description', 'field_name': 'description', 'required': False,
                 'instruction': 'Optional. Brief description of contents',
                 'sample': 'HR Personnel Files %s' % current_year, 'width': 30},
                {'name': 'Department', 'field_name': 'department_id', 'required': False,
                 'instruction': 'Optional. Department name - must match existing department',
                 'sample': 'Human Resources', 'width': 20},
                {'name': 'Retention Policy', 'field_name': 'retention_policy_id', 'required': False,
                 'instruction': 'Optional. Retention policy name - must match existing policy',
                 'sample': '7 Years', 'width': 20},
                {'name': 'Destruction Due Date', 'field_name': 'destruction_due_date', 'required': False,
                 'instruction': 'Optional. Format: YYYY-MM-DD',
                 'sample': '%s-12-31' % retention_year, 'width': 18},
                {'name': 'Notes', 'field_name': 'notes', 'required': False,
                 'instruction': 'Optional. Additional notes',
                 'sample': 'Confidential', 'width': 25},
            ],
            'files': [
                {'name': 'File Name/Number', 'field_name': 'name', 'required': True,
                 'instruction': 'Required. Name or number for the file',
                 'sample': 'John Smith Personnel File', 'width': 25},
                {'name': 'Container Number', 'field_name': 'container_id', 'required': False,
                 'instruction': 'Optional. Container this file belongs to',
                 'sample': 'BOX-%s-001' % current_year, 'width': 20},
                {'name': 'Description', 'field_name': 'description', 'required': False,
                 'instruction': 'Optional. Brief description',
                 'sample': 'Employee personnel records', 'width': 30},
                {'name': 'Department', 'field_name': 'department_id', 'required': False,
                 'instruction': 'Optional. Department name',
                 'sample': 'Human Resources', 'width': 20},
                {'name': 'Notes', 'field_name': 'notes', 'required': False,
                 'instruction': 'Optional. Additional notes',
                 'sample': '', 'width': 25},
            ],
            'documents': [
                {'name': 'Document Name', 'field_name': 'name', 'required': True,
                 'instruction': 'Required. Document title or name',
                 'sample': 'Q4 Financial Report', 'width': 25},
                {'name': 'Document Type', 'field_name': 'document_type_id', 'required': False,
                 'instruction': 'Optional. Type of document',
                 'sample': 'Financial', 'width': 18},
                {'name': 'File Name', 'field_name': 'file_id', 'required': False,
                 'instruction': 'Optional. Associated file folder',
                 'sample': 'John Smith Personnel File', 'width': 25},
                {'name': 'Container Number', 'field_name': 'container_id', 'required': False,
                 'instruction': 'Optional. Associated container',
                 'sample': 'BOX-%s-001' % current_year, 'width': 20},
                {'name': 'Description', 'field_name': 'description', 'required': False,
                 'instruction': 'Optional. Document description',
                 'sample': 'Q4 financial statements', 'width': 30},
            ],
            'users': [
                {'name': 'Name', 'field_name': 'name', 'required': True,
                 'instruction': 'Required. Full name of the user',
                 'sample': 'Jane Doe', 'width': 22},
                {'name': 'Email', 'field_name': 'email', 'required': True,
                 'instruction': 'Required. Email address (used as login)',
                 'sample': 'jane.doe@example.com', 'width': 28},
                {'name': 'Department', 'field_name': 'department_id', 'required': True,
                 'instruction': 'Required. Department name - must match existing department',
                 'sample': 'Human Resources', 'width': 20},
                {'name': 'Phone', 'field_name': 'phone', 'required': False,
                 'instruction': 'Optional. Phone number',
                 'sample': '555-123-4567', 'width': 15},
                {'name': 'Job Title', 'field_name': 'function', 'required': False,
                 'instruction': 'Optional. Job title or position',
                 'sample': 'HR Manager', 'width': 20},
            ],
            'inventory': [
                {'name': 'Item Name', 'field_name': 'name', 'required': True,
                 'instruction': 'Required. Inventory item name',
                 'sample': 'Personnel Records Box', 'width': 25},
                {'name': 'Barcode', 'field_name': 'barcode', 'required': False,
                 'instruction': 'Optional. Item barcode if known',
                 'sample': '', 'width': 18},
                {'name': 'Location', 'field_name': 'location_id', 'required': False,
                 'instruction': 'Optional. Storage location name',
                 'sample': 'Warehouse A - Row 5', 'width': 22},
                {'name': 'Quantity', 'field_name': 'quantity', 'required': False,
                 'instruction': 'Optional. Item quantity (default: 1)',
                 'sample': '1', 'width': 12},
                {'name': 'Description', 'field_name': 'description', 'required': False,
                 'instruction': 'Optional. Item description',
                 'sample': 'HR department files', 'width': 30},
            ],
            'requests': [
                {'name': 'Request Type', 'field_name': 'request_type', 'required': True,
                 'instruction': 'Required. Type: retrieval, destruction, pickup, service',
                 'sample': 'retrieval', 'width': 18},
                {'name': 'Container/File', 'field_name': 'item_reference', 'required': True,
                 'instruction': 'Required. Container or file number to request',
                 'sample': 'BOX-%s-001' % current_year, 'width': 22},
                {'name': 'Priority', 'field_name': 'priority', 'required': False,
                 'instruction': 'Optional. Priority: low, normal, high, urgent',
                 'sample': 'normal', 'width': 12},
                {'name': 'Description', 'field_name': 'description', 'required': False,
                 'instruction': 'Optional. Request details',
                 'sample': 'Need for audit', 'width': 30},
                {'name': 'Requested Date', 'field_name': 'requested_date', 'required': False,
                 'instruction': 'Optional. Preferred date (YYYY-MM-DD)',
                 'sample': '', 'width': 15},
            ],
            'custom': [
                {'name': 'Field 1', 'field_name': 'field_1', 'required': True,
                 'instruction': 'Configure columns in template settings',
                 'sample': '', 'width': 20},
                {'name': 'Field 2', 'field_name': 'field_2', 'required': False,
                 'instruction': '',
                 'sample': '', 'width': 20},
                {'name': 'Field 3', 'field_name': 'field_3', 'required': False,
                 'instruction': '',
                 'sample': '', 'width': 20},
            ],
        }

        return defaults.get(self.template_type, defaults['custom'])

    def action_download(self):
        """Download the template file"""
        self.ensure_one()

        # Generate template if not already generated
        if not self.template_file:
            self.action_generate_template()

        # Track download
        self.sudo().write({
            'download_count': self.download_count + 1,
            'last_download_date': fields.Datetime.now(),
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/template_file/%s?download=true' % (
                self._name, self.id, self.template_filename or 'template.xlsx'
            ),
            'target': 'self',
        }

    def increment_import_count(self):
        """Track successful import using this template"""
        self.sudo().write({
            'import_count': self.import_count + 1,
            'last_import_date': fields.Datetime.now(),
        })
