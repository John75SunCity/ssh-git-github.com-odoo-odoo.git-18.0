# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class RecordsContainerTypeConverterWizard(models.TransientModel):
    """
    Records Container Type Converter Wizard - Converts containers from one type to another.
    Handles the business logic for changing container specifications, updating billing rates,
    transferring contents, and maintaining audit trails during container type conversions.
    """
    _name = 'records.container.type.converter.wizard'
    _description = 'Records Container Type Converter Wizard'

    # Basic Information
    name = fields.Char(
        string='Conversion Request',
        default='Container Type Conversion',
        readonly=True
    )

    # Source Container Information
    source_container_id = fields.Many2one(
        'records.container',
        string='Source Container',
        required=True,
        help="Container to be converted"
    )

    source_type = fields.Char(
        string='Current Type',
        related='source_container_id.container_type',
        readonly=True
    )

    source_capacity = fields.Float(
        string='Current Capacity',
        related='source_container_id.capacity',
        readonly=True
    )

    source_dimensions = fields.Char(
        string='Current Dimensions',
        related='source_container_id.dimensions',
        readonly=True
    )

    # Target Container Information
    target_container_type = fields.Selection([
        ('bankers_box', 'Bankers Box'),
        ('file_box', 'File Box'),
        ('storage_box', 'Storage Box'),
        ('archive_box', 'Archive Box'),
        ('custom_box', 'Custom Box'),
        ('bin', 'Shredding Bin'),
        ('container', 'Large Container'),
        ('vault', 'Secure Vault'),
    ], string='Target Container Type', required=True,
       help="Type to convert the container to")

    target_capacity = fields.Float(
        string='Target Capacity',
        required=True,
        help="New capacity for the converted container"
    )

    target_dimensions = fields.Char(
        string='Target Dimensions',
        help="New dimensions for the converted container"
    )

    # Conversion Configuration
    conversion_reason = fields.Selection([
        ('size_requirement', 'Size Requirement Change'),
        ('security_upgrade', 'Security Upgrade'),
        ('damage_replacement', 'Damage Replacement'),
        ('consolidation', 'Content Consolidation'),
        ('customer_request', 'Customer Request'),
        ('compliance', 'Compliance Requirement'),
        ('cost_optimization', 'Cost Optimization'),
    ], string='Conversion Reason', required=True,
       help="Reason for the container type conversion")

    preserve_contents = fields.Boolean(
        string='Preserve Contents',
        default=True,
        help="Transfer all contents to the new container type"
    )

    preserve_barcode = fields.Boolean(
        string='Preserve Barcode',
        default=True,
        help="Keep the same barcode for the converted container"
    )

    preserve_location = fields.Boolean(
        string='Preserve Location',
        default=True,
        help="Keep the container in the same location"
    )

    # Content Management
    content_handling = fields.Selection([
        ('transfer_all', 'Transfer All Contents'),
        ('transfer_selected', 'Transfer Selected Contents'),
        ('redistribute', 'Redistribute to Multiple Containers'),
        ('archive', 'Archive Contents Separately'),
    ], string='Content Handling', default='transfer_all',
       help="How to handle existing contents during conversion")

    documents_to_transfer = fields.Many2many(
        'records.document',
        string='Documents to Transfer',
        help="Specific documents to transfer (used with 'Transfer Selected')"
    )

    new_containers_needed = fields.Integer(
        string='Additional Containers Needed',
        default=0,
        help="Number of additional containers needed for redistribution"
    )

    # Cost and Billing Impact
    cost_impact_analysis = fields.Text(
        string='Cost Impact Analysis',
        help="Analysis of cost changes due to conversion"
    )

    billing_rate_change = fields.Monetary(
        string='Billing Rate Change',
        currency_field='currency_id',
        help="Change in monthly billing rate (positive = increase)"
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # Customer Billing Information
    customer_billing_profile_id = fields.Many2one(
        'customer.billing.profile',
        string='Customer Billing Profile',
        related='source_container_id.partner_id.records_billing_profile_id',
        readonly=True,
        help="Customer's billing profile with rates"
    )

    customer_discount_percentage = fields.Float(
        string='Customer Discount %',
        related='source_container_id.partner_id.records_discount_percentage',
        readonly=True,
        help="Customer's discount percentage"
    )

    current_monthly_rate = fields.Monetary(
        string='Current Monthly Rate',
        compute='_compute_rate_details',
        currency_field='currency_id',
        help="Current monthly rate for source container"
    )

    target_monthly_rate = fields.Monetary(
        string='Target Monthly Rate',
        compute='_compute_rate_details',
        currency_field='currency_id',
        help="Monthly rate for target container type"
    )

    annual_cost_impact = fields.Monetary(
        string='Annual Cost Impact',
        compute='_compute_rate_details',
        currency_field='currency_id',
        help="Annual cost impact of the conversion"
    )

    customer_approval_required = fields.Boolean(
        string='Customer Approval Required',
        compute='_compute_customer_approval_required',
        store=True,
        help="Whether customer approval is needed for this conversion"
    )

    # Scheduling and Logistics
    conversion_date = fields.Datetime(
        string='Scheduled Conversion Date',
        default=fields.Datetime.now,
        required=True,
        help="When the conversion should take place"
    )

    estimated_duration = fields.Float(
        string='Estimated Duration (Hours)',
        default=1.0,
        help="Estimated time needed for the conversion"
    )

    requires_special_handling = fields.Boolean(
        string='Requires Special Handling',
        help="Whether special handling procedures are needed"
    )

    special_instructions = fields.Text(
        string='Special Instructions',
        help="Special instructions for the conversion process"
    )

    # Approval and Workflow
    approval_status = fields.Selection([
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Approval Status', default='draft', readonly=True)

    approver_id = fields.Many2one(
        'res.users',
        string='Approver',
        help="User who can approve this conversion"
    )

    approval_notes = fields.Text(
        string='Approval Notes',
        help="Notes from the approver"
    )

    # Conversion Results
    conversion_completed = fields.Boolean(
        string='Conversion Completed',
        default=False,
        readonly=True
    )

    new_container_id = fields.Many2one(
        'records.container',
        string='New Container',
        readonly=True,
        help="The new container created during conversion"
    )

    conversion_notes = fields.Text(
        string='Conversion Notes',
        help="Notes about the conversion process and results"
    )

    # State Management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', readonly=True)

    @api.depends('billing_rate_change', 'target_container_type')
    def _compute_customer_approval_required(self):
        """Determine if customer approval is required"""
        for record in self:
            # Require approval if rate increases or security changes
            rate_increase = record.billing_rate_change > 0
            security_change = record.conversion_reason == 'security_upgrade'
            record.customer_approval_required = rate_increase or security_change

    @api.depends('source_container_id', 'target_container_type')
    def _compute_rate_details(self):
        """Compute detailed rate information from customer's billing profile"""
        for record in self:
            if record.source_container_id and record.source_container_id.partner_id:
                customer = record.source_container_id.partner_id

                # Get current rate
                record.current_monthly_rate = record._get_customer_container_rate(
                    customer, record.source_container_id.container_type
                )

                # Get target rate
                if record.target_container_type:
                    record.target_monthly_rate = record._get_customer_container_rate(
                        customer, record.target_container_type
                    )
                else:
                    record.target_monthly_rate = 0.0

                # Calculate annual impact
                monthly_change = record.target_monthly_rate - record.current_monthly_rate
                record.annual_cost_impact = monthly_change * 12
            else:
                record.current_monthly_rate = 0.0
                record.target_monthly_rate = 0.0
                record.annual_cost_impact = 0.0

    @api.onchange('target_container_type')
    def _onchange_target_container_type(self):
        """Update target specifications based on container type"""
        if self.target_container_type:
            # Set default capacities and dimensions based on type
            type_specs = {
                'bankers_box': {'capacity': 1.2, 'dimensions': '15"x12"x10"'},
                'file_box': {'capacity': 1.5, 'dimensions': '16"x13"x11"'},
                'storage_box': {'capacity': 2.0, 'dimensions': '18"x15"x12"'},
                'archive_box': {'capacity': 2.5, 'dimensions': '20"x16"x14"'},
                'bin': {'capacity': 50.0, 'dimensions': '36"x24"x30"'},
                'container': {'capacity': 100.0, 'dimensions': '48"x40"x48"'},
                'vault': {'capacity': 0.5, 'dimensions': '12"x8"x6"'},
            }

            if self.target_container_type in type_specs:
                specs = type_specs[self.target_container_type]
                self.target_capacity = specs['capacity']
                self.target_dimensions = specs['dimensions']

    @api.onchange('source_container_id', 'target_container_type')
    def _onchange_cost_analysis(self):
        """Calculate cost impact of the conversion using real customer rate profiles"""
        if self.source_container_id and self.target_container_type:
            customer = self.source_container_id.partner_id

            # Get current rate from customer's billing profile
            current_rate = self._get_customer_container_rate(customer, self.source_container_id.container_type)

            # Get new rate for target container type
            new_rate = self._get_customer_container_rate(customer, self.target_container_type)

            self.billing_rate_change = new_rate - current_rate

            # Enhanced cost analysis with customer-specific context
            analysis_parts = []

            if self.billing_rate_change > 0:
                analysis_parts.append(_("Monthly rate will increase by $%.2f") % self.billing_rate_change)
                analysis_parts.append(_("From: $%.2f to $%.2f") % (current_rate, new_rate))

                # Add percentage increase
                if current_rate > 0:
                    percent_increase = (self.billing_rate_change / current_rate) * 100
                    analysis_parts.append(_("Increase: %.1f%%") % percent_increase)

            elif self.billing_rate_change < 0:
                analysis_parts.append(_("Monthly rate will decrease by $%.2f") % abs(self.billing_rate_change))
                analysis_parts.append(_("From: $%.2f to $%.2f") % (current_rate, new_rate))

                # Add percentage decrease
                if current_rate > 0:
                    percent_decrease = (abs(self.billing_rate_change) / current_rate) * 100
                    analysis_parts.append(_("Savings: %.1f%%") % percent_decrease)

            else:
                analysis_parts.append(_("No change in monthly billing rate"))
                analysis_parts.append(_("Rate remains: $%.2f") % current_rate)

            # Add customer-specific discount information
            if customer and hasattr(customer, 'records_discount_percentage') and customer.records_discount_percentage > 0:
                analysis_parts.append(_("Customer discount: %.1f%% applied") % customer.records_discount_percentage)

            # Add annual impact for significant changes
            if abs(self.billing_rate_change) > 10:
                annual_impact = self.billing_rate_change * 12
                if annual_impact > 0:
                    analysis_parts.append(_("Annual cost increase: $%.2f") % annual_impact)
                else:
                    analysis_parts.append(_("Annual cost savings: $%.2f") % abs(annual_impact))

            self.cost_impact_analysis = '\n'.join(analysis_parts)

    def _get_customer_container_rate(self, customer, container_type):
        """Get the actual billing rate for a specific container type from customer's rate profile"""
        if not customer or not container_type:
            return 0.0

        # Method 1: Check customer's billing profile (preferred)
        if hasattr(customer, 'records_billing_profile_id') and customer.records_billing_profile_id:
            billing_profile = customer.records_billing_profile_id

            # Look for specific container type rates in billing profile
            if hasattr(billing_profile, 'container_rates_ids'):
                for rate_line in billing_profile.container_rates_ids:
                    if rate_line.container_type == container_type:
                        return rate_line.monthly_rate

        # Method 2: Check customer billing lines (alternative approach)
        if hasattr(self.env, 'records.billing'):
            billing_lines = self.env['records.billing'].search([
                ('partner_id', '=', customer.id),
                ('container_type', '=', container_type),
                ('active', '=', True)
            ], limit=1)

            if billing_lines:
                return billing_lines[0].monthly_rate

        # Method 3: Check base rate models
        if hasattr(self.env, 'base.rate'):
            base_rates = self.env['base.rate'].search([
                ('container_type', '=', container_type),
                ('active', '=', True)
            ], limit=1)

            if base_rates:
                rate = base_rates[0].rate

                # Apply customer-specific discount if available
                if hasattr(customer, 'records_discount_percentage') and customer.records_discount_percentage > 0:
                    discount_multiplier = (100 - customer.records_discount_percentage) / 100
                    rate = rate * discount_multiplier

                return rate

        # Method 4: Fallback to container type mapping (last resort)
        fallback_rates = {
            'bankers_box': 20.0,
            'file_box': 25.0,
            'storage_box': 30.0,
            'archive_box': 35.0,
            'custom_box': 40.0,
            'bin': 100.0,
            'container': 150.0,
            'vault': 50.0,
        }

        base_rate = fallback_rates.get(container_type, 25.0)

        # Apply customer discount even to fallback rates
        if hasattr(customer, 'records_discount_percentage') and customer.records_discount_percentage > 0:
            discount_multiplier = (100 - customer.records_discount_percentage) / 100
            base_rate = base_rate * discount_multiplier

        return base_rate

    def action_validate_conversion(self):
        """Validate the conversion parameters"""
        self.ensure_one()

        if not self.source_container_id:
            raise UserError(_("Please select a source container"))

        if not self.target_container_type:
            raise UserError(_("Please select a target container type"))

        if self.target_capacity <= 0:
            raise UserError(_("Target capacity must be greater than zero"))

        # Check if conversion is necessary
        if self.source_type == self.target_container_type:
            raise UserError(_("Source and target container types are the same"))

        # Validate content handling
        if self.content_handling == 'transfer_selected' and not self.documents_to_transfer:
            raise UserError(_("Please select documents to transfer"))

        self.state = 'validated'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Validation Successful'),
                'message': _('Container conversion parameters validated successfully'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_submit_for_approval(self):
        """Submit conversion for approval if required"""
        self.ensure_one()

        if self.state != 'validated':
            raise UserError(_("Please validate the conversion first"))

        if self.customer_approval_required and not self.approver_id:
            raise UserError(_("Please specify an approver"))

        if self.customer_approval_required:
            self.approval_status = 'pending_approval'
            self._send_approval_notification()
        else:
            self.approval_status = 'approved'

        self.state = 'scheduled'

        # Create audit log
        self._create_audit_log('submitted_for_approval')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Submitted for Approval'),
                'message': _('Container conversion submitted for approval'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_approve_conversion(self):
        """Approve the container conversion"""
        self.ensure_one()

        if self.approval_status != 'pending_approval':
            raise UserError(_("Only pending conversions can be approved"))

        if self.customer_approval_required and self.env.user != self.approver_id:
            raise UserError(_("Only the designated approver can approve this conversion"))

        self.approval_status = 'approved'
        self._create_audit_log('approved')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Conversion Approved'),
                'message': _('Container conversion has been approved'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_execute_conversion(self):
        """Execute the container conversion"""
        self.ensure_one()

        if self.approval_status != 'approved':
            raise UserError(_("Only approved conversions can be executed"))

        if self.conversion_completed:
            raise UserError(_("This conversion has already been completed"))

        self.state = 'in_progress'

        try:
            # Create new container with target specifications
            new_container_vals = {
                'name': _('Converted from %s') % self.source_container_id.name,
                'container_type': self.target_container_type,
                'capacity': self.target_capacity,
                'dimensions': self.target_dimensions,
                'partner_id': self.source_container_id.partner_id.id,
            }

            if self.preserve_barcode:
                new_container_vals['barcode'] = self.source_container_id.barcode

            if self.preserve_location:
                new_container_vals['location_id'] = self.source_container_id.location_id.id

            self.new_container_id = self.env['records.container'].create(new_container_vals)

            # Handle content transfer
            if self.preserve_contents:
                self._transfer_contents()

            # Update billing records if rate changed
            if self.billing_rate_change != 0:
                self._update_billing_records()

            # Update source container status
            self.source_container_id.write({
                'status': 'converted',
                'notes': _('Converted to %s on %s') % (
                    self.target_container_type, fields.Datetime.now()
                )
            })

            # Mark conversion as completed
            self.write({
                'conversion_completed': True,
                'state': 'completed',
                'conversion_notes': _('Conversion completed successfully on %s') % fields.Datetime.now()
            })

            # Create audit log
            self._create_audit_log('completed')

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Conversion Completed'),
                    'message': _('Container conversion completed successfully'),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            self.state = 'scheduled'
            raise UserError(_("Error during conversion: %s") % str(e))

    def _transfer_contents(self):
        """Transfer contents from source to target container"""
        if self.content_handling == 'transfer_all':
            # Transfer all documents
            documents = self.env['records.document'].search([
                ('container_id', '=', self.source_container_id.id)
            ])
            documents.write({'container_id': self.new_container_id.id})

        elif self.content_handling == 'transfer_selected':
            # Transfer selected documents
            self.documents_to_transfer.write({'container_id': self.new_container_id.id})

        # Other content handling types would be implemented here

    def _update_billing_records(self):
        """Update customer billing records to reflect the new container type and rate"""
        customer = self.source_container_id.partner_id
        if not customer:
            return

        # Method 1: Update records.billing entries
        if hasattr(self.env, 'records.billing'):
            # Find existing billing record for the source container
            existing_billing = self.env['records.billing'].search([
                ('partner_id', '=', customer.id),
                ('container_id', '=', self.source_container_id.id),
                ('active', '=', True)
            ], limit=1)

            if existing_billing:
                # Update the existing billing record
                existing_billing.write({
                    'container_id': self.new_container_id.id,
                    'container_type': self.target_container_type,
                    'monthly_rate': self.target_monthly_rate,
                    'notes': _('Updated due to container conversion on %s') % fields.Datetime.now()
                })
            else:
                # Create new billing record for the new container
                self.env['records.billing'].create({
                    'partner_id': customer.id,
                    'container_id': self.new_container_id.id,
                    'container_type': self.target_container_type,
                    'monthly_rate': self.target_monthly_rate,
                    'start_date': fields.Date.today(),
                    'notes': _('Created due to container conversion from %s') % self.source_container_id.name
                })

        # Method 2: Update customer billing profile rates
        if hasattr(customer, 'records_billing_profile_id') and customer.records_billing_profile_id:
            billing_profile = customer.records_billing_profile_id

            if hasattr(billing_profile, 'container_rates_ids'):
                # Find rate line for target container type
                target_rate_line = billing_profile.container_rates_ids.filtered(
                    lambda r: r.container_type == self.target_container_type
                )

                if not target_rate_line:
                    # Create new rate line if it doesn't exist
                    self.env['customer.billing.profile.line'].create({
                        'billing_profile_id': billing_profile.id,
                        'container_type': self.target_container_type,
                        'monthly_rate': self.target_monthly_rate,
                        'effective_date': fields.Date.today()
                    })

        # Method 3: Create billing change log
        try:
            self.env['billing.change.log'].create({
                'partner_id': customer.id,
                'container_id': self.new_container_id.id,
                'change_type': 'container_conversion',
                'old_rate': self.current_monthly_rate,
                'new_rate': self.target_monthly_rate,
                'change_amount': self.billing_rate_change,
                'change_reason': self.conversion_reason,
                'change_date': fields.Datetime.now(),
                'user_id': self.env.user.id,
                'notes': _('Container conversion from %s (%s) to %s (%s)') % (
                    self.source_container_id.name,
                    self.source_type,
                    self.new_container_id.name,
                    self.target_container_type
                )
            })
        except Exception:
            # Model might not exist, continue without error
            pass

    def _send_approval_notification(self):
        """Send approval notification to designated approver"""
        if self.approver_id:
            # Send email notification
            try:
                template = self.env.ref('records_management.container_conversion_approval_template', False)
                if template:
                    template.send_mail(self.id)
            except Exception:
                pass

    def _create_audit_log(self, action):
        """Create audit log entry"""
        try:
            self.env['naid.audit.log'].create({
                'name': _('Container Conversion %s - %s') % (action.title(), self.source_container_id.name),
                'action': 'container_conversion_%s' % action,
                'user_id': self.env.user.id,
                'notes': _('Container %s converted from %s to %s') % (
                    self.source_container_id.name, self.source_type, self.target_container_type
                ),
                'audit_date': fields.Datetime.now(),
            })
        except Exception:
            pass
