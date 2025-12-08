# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ContainerQuickAddWizard(models.TransientModel):
    """
    Container Quick Add Wizard - Streamlined container creation with industry templates
    Pre-fills common fields and guides users through adding containers and their contents
    """
    _name = 'container.quick.add.wizard'
    _description = 'Container Quick Add Wizard'

    # Step 1: Container Basics
    container_number = fields.Char(
        string='Box/Container Number',
        required=True,
        help="4-digit minimum container identifier (e.g., 0001, B-1234)"
    )

    # Auto-filled from user context
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        default=lambda self: self._default_partner(),
        help="Customer/Company (auto-filled from your login)"
    )

    department_id = fields.Many2one(
        'records.department',
        string='Department',
        required=True,
        default=lambda self: self._default_department(),
        help="Department (auto-filled from your login)"
    )

    stock_owner_id = fields.Many2one(
        'res.partner',
        string='Stock Owner',
        default=lambda self: self._default_partner(),
        help="Stock ownership (defaults to Customer, can override for multi-company)"
    )

    # Industry Template Selection
    industry_template = fields.Selection([
        ('legal', 'Legal - Case Files'),
        ('medical', 'Medical - Patient Records'),
        ('financial', 'Financial - Account Files'),
        ('hr', 'Human Resources - Employee Files'),
        ('government', 'Government - Public Records'),
        ('retail', 'Retail - Business Records'),
        ('custom', 'Custom - Manual Entry'),
    ], string='Industry Template', required=True, default='legal',
       help="Select industry template for pre-configured fields")

    # Container Contents Description
    contents_type = fields.Selection([
        ('alphabetical', 'Alphabetical Range (A-Z)'),
        ('numerical', 'Numerical Range (001-999)'),
        ('date_range', 'Date Range'),
        ('case_files', 'Case File Numbers'),
        ('patient_ids', 'Patient ID Range'),
        ('employee_ids', 'Employee ID Range'),
        ('custom', 'Custom Description'),
    ], string='Contents Type', default='alphabetical',
       help="How are files organized in this container?")

    # Range Fields (shown based on contents_type)
    range_start = fields.Char(string='Start', help="Starting value (e.g., 'A', '001', or a date)")
    range_end = fields.Char(string='End', help="Ending value (e.g., 'Z', '999', or a date)")

    # Custom description
    contents_description = fields.Text(
        string='Contents Description',
        help="Detailed description of what's in this container"
    )

    # Retention
    retention_period = fields.Selection([
        ('3', '3 Years'),
        ('5', '5 Years'),
        ('7', '7 Years'),
        ('10', '10 Years'),
        ('permanent', 'Permanent'),
        ('custom', 'Custom Period'),
    ], string='Retention Period', required=True, default='7',
       help="How long must these records be retained?")

    custom_retention_years = fields.Integer(
        string='Custom Years',
        help="Specify custom retention period in years"
    )

    destruction_date = fields.Date(
        string='Eligible for Destruction',
        compute='_compute_destruction_date',
        store=True,
        help="Calculated destruction date based on retention period"
    )

    # Location
    location_id = fields.Many2one(
        'stock.location',
        string='Storage Location',
        help="Where will this container be stored?"
    )

    # Step 2: Add Files (optional)
    add_files_now = fields.Boolean(
        string='Add Files to Container Now',
        default=False,
        help="Check this to add file inventory after creating the container"
    )

    # Calculated Fields
    container_label = fields.Char(
        string='Container Label Preview',
        compute='_compute_container_label',
        help="Preview of how the container label will look"
    )

    @api.model
    def _default_partner(self):
        """Auto-fill customer from user's context or portal user"""
        user = self.env.user
        if user.partner_id:
            # For portal users, use their own partner
            if user.has_group('base.group_portal'):
                return user.partner_id
            # For internal users, try to get from context or recent containers
            partner_id = self.env.context.get('default_partner_id')
            if partner_id:
                return partner_id
        return False

    @api.model
    def _default_department(self):
        """Auto-fill department from user's context"""
        dept_id = self.env.context.get('default_department_id')
        if dept_id:
            return dept_id
        # Try to get user's default department
        user = self.env.user
        if user.partner_id:
            # Look for department linked to this user
            dept = self.env['records.department'].search([
                ('partner_id', '=', user.partner_id.id)
            ], limit=1)
            if dept:
                return dept
        return False

    @api.depends('retention_period', 'custom_retention_years')
    def _compute_destruction_date(self):
        """Calculate destruction date based on retention period"""
        for wizard in self:
            if wizard.retention_period == 'permanent':
                wizard.destruction_date = False
            elif wizard.retention_period == 'custom' and wizard.custom_retention_years:
                wizard.destruction_date = fields.Date.add(
                    fields.Date.today(),
                    years=wizard.custom_retention_years
                )
            elif wizard.retention_period != 'custom':
                years = int(wizard.retention_period)
                wizard.destruction_date = fields.Date.add(
                    fields.Date.today(),
                    years=years
                )
            else:
                wizard.destruction_date = False

    @api.depends('container_number', 'contents_type', 'range_start', 'range_end', 'industry_template')
    def _compute_container_label(self):
        """Generate preview of container label"""
        for wizard in self:
            label_parts = []
            if wizard.container_number:
                label_parts.append("Box " + wizard.container_number)

            if wizard.contents_type and wizard.range_start and wizard.range_end:
                if wizard.contents_type == 'alphabetical':
                    label_parts.append(f"Files {wizard.range_start}-{wizard.range_end}")
                elif wizard.contents_type == 'case_files':
                    label_parts.append(f"Cases {wizard.range_start}-{wizard.range_end}")
                elif wizard.contents_type == 'date_range':
                    label_parts.append(f"Dates {wizard.range_start} to {wizard.range_end}")
                elif wizard.contents_type == 'numerical':
                    label_parts.append(f"Files {wizard.range_start}-{wizard.range_end}")

            wizard.container_label = " | ".join(label_parts) if label_parts else "Preview will appear here"

    @api.constrains('container_number')
    def _check_container_number(self):
        """Validate container number is at least 4 characters"""
        for wizard in self:
            if wizard.container_number and len(wizard.container_number) < 4:
                raise ValidationError(_("Container number must be at least 4 characters long"))

    @api.onchange('partner_id', 'department_id')
    def _onchange_partner_department(self):
        """
        Auto-set stock_owner_id based on customer and department selection.
        
        Logic:
        - If department selected: stock_owner = department's partner
        - If only customer selected: stock_owner = customer
        - Filter available options to customer and its child departments
        """
        if self.department_id:
            # Department selected - use department's partner as stock owner
            self.stock_owner_id = self.department_id.partner_id
        elif self.partner_id:
            # Only customer selected - use customer as stock owner
            self.stock_owner_id = self.partner_id

        # Build domain to filter stock_owner_id options
        if self.partner_id:
            # Show customer + all its child contacts (departments)
            return {
                'domain': {
                    'stock_owner_id': [
                        '|',
                        ('id', '=', self.partner_id.id),
                        ('parent_id', '=', self.partner_id.id)
                    ]
                }
            }
        return {'domain': {'stock_owner_id': []}}

    def action_create_container(self):
        """Create the container with all entered data"""
        self.ensure_one()

        # Build container description from template
        description = self._build_description()

        # Create container
        container_vals = {
            'name': self.container_number,
            'partner_id': self.partner_id.id,
            'department_id': self.department_id.id,
            'stock_owner_id': self.stock_owner_id.id if self.stock_owner_id else self.partner_id.id,
            'description': description,
            'location_id': self.location_id.id if self.location_id else False,
        }

        # Add alpha range if provided
        if self.range_start:
            container_vals['alpha_range_start'] = self.range_start
        if self.range_end:
            container_vals['alpha_range_end'] = self.range_end

        # Add retention info
        if self.retention_period == 'permanent':
            container_vals['permanent_retention'] = True
        elif self.retention_period == 'custom' and self.custom_retention_years:
            # For custom retention, set the destruction due date directly
            container_vals['destruction_due_date'] = self.destruction_date
        else:
            # For standard retention periods, set the destruction due date
            container_vals['destruction_due_date'] = self.destruction_date

        # Generate temp barcode for tracking (customer-created containers)
        # Format: TEMP-{PARTNER_ABBR}-{YYYYMMDD}-{SEQUENCE}
        temp_barcode = self._generate_temp_barcode()
        if temp_barcode:
            container_vals['temp_barcode'] = temp_barcode

        container = self.env['records.container'].create(container_vals)

        # If user wants to add files now, open the file wizard
        if self.add_files_now:
            return {
                'name': _('Add Files to Container'),
                'type': 'ir.actions.act_window',
                'res_model': 'records.document',
                'view_mode': 'list,form',
                'context': {
                    'default_container_id': container.id,
                    'default_partner_id': self.partner_id.id,
                    'default_department_id': self.department_id.id,
                },
                'domain': [('container_id', 'in', container.ids)],
                'target': 'current',
            }
        else:
            # Show success message and open the container
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'records.container',
                'res_id': container.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def _build_description(self):
        """Build detailed description based on template and inputs"""
        description_parts = []

        # Add industry-specific prefix
        if self.industry_template == 'legal':
            description_parts.append("Legal Records -")
        elif self.industry_template == 'medical':
            description_parts.append("Medical Records -")
        elif self.industry_template == 'financial':
            description_parts.append("Financial Records -")
        elif self.industry_template == 'hr':
            description_parts.append("HR Records -")
        elif self.industry_template == 'government':
            description_parts.append("Government Records -")
        elif self.industry_template == 'retail':
            description_parts.append("Business Records -")

        # Add contents description
        if self.contents_type != 'custom':
            if self.range_start and self.range_end:
                if self.contents_type == 'alphabetical':
                    description_parts.append(f"Files {self.range_start} through {self.range_end}")
                elif self.contents_type == 'case_files':
                    description_parts.append(f"Case Files {self.range_start} - {self.range_end}")
                elif self.contents_type == 'date_range':
                    description_parts.append(f"Documents dated {self.range_start} to {self.range_end}")
                elif self.contents_type == 'numerical':
                    description_parts.append(f"File Numbers {self.range_start}-{self.range_end}")
                elif self.contents_type == 'patient_ids':
                    description_parts.append(f"Patient IDs {self.range_start} to {self.range_end}")
                elif self.contents_type == 'employee_ids':
                    description_parts.append(f"Employee IDs {self.range_start} to {self.range_end}")

        # Add custom description if provided
        if self.contents_description:
            description_parts.append(self.contents_description)

        return " ".join(description_parts)

    def _generate_temp_barcode(self):
        """
        Generate temporary barcode for customer-created containers
        Format: TEMP-{PARTNER_ABBR}-{YYYYMMDD}-{SEQUENCE}
        Example: TEMP-CITY-20251103-0001
        """
        partner = self.partner_id
        if not partner:
            return False

        # Get partner abbreviation (first 4 chars of name, uppercase)
        partner_abbr = (partner.name or "CUST")[:4].upper().replace(" ", "")
        
        # Get today's date in YYYYMMDD format
        date_str = fields.Date.today().strftime("%Y%m%d")
        
        # Get sequence number for today (count existing temp barcodes for this partner today)
        existing_count = self.env['records.container'].search_count([
            ('partner_id', '=', partner.id),
            ('temp_barcode', 'like', f'TEMP-{partner_abbr}-{date_str}-%')
        ])
        
        sequence = str(existing_count + 1).zfill(4)
        
        return f"TEMP-{partner_abbr}-{date_str}-{sequence}"
