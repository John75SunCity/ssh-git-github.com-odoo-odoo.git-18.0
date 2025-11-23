# -*- coding: utf-8 -*-
import logging  # stdlib first

from odoo import _, api, fields, models  # Odoo core
from odoo.exceptions import ValidationError, UserError  # Odoo addons

_logger = logging.getLogger(__name__)


class BinIssueReportWizard(models.TransientModel):
    """
    Bin Issue Report Wizard

    Comprehensive wizard for reporting bin issues with photo documentation,
    automatic work order creation, and billing integration based on fault determination.

    Features:
    - Photo documentation using existing mobile.photo system
    - Automatic work order creation with appropriate priority
    - Customer billing vs. company maintenance
    - Integration with base.rates for pricing
    - NAID compliance audit logging
    """
    _name = 'bin.issue.report.wizard'
    _description = 'Bin Issue Report Wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # BIN IDENTIFICATION
    # ============================================================================
    bin_id = fields.Many2one(
        comodel_name='shredding.service.bin',
        string="Bin",
        required=True,
        readonly=True
    )

    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string="Current Customer Location",
        readonly=True,
        help="Customer location where bin is currently placed"
    )

    location_id = fields.Many2one(
        comodel_name='stock.location',
        string="Specific Location",
        help="Specific location where issue was discovered"
    )

    # ============================================================================
    # ISSUE CLASSIFICATION
    # ============================================================================
    issue_type = fields.Selection([
        ('damaged_customer_fault', 'Damaged - Customer Fault (Billable)'),
        ('damaged_company_fault', 'Damaged - Company/Wear & Tear (Non-Billable)'),
        ('missing_label', 'Missing Label (Non-Billable Maintenance)'),
        ('bad_barcode', 'Unreadable Barcode (Non-Billable Maintenance)'),
        ('maintenance_required', 'General Maintenance Required'),
        ('lost_stolen', 'Lost or Stolen Bin'),
        ('other', 'Other Issue'),
    ], string="Issue Type", required=True, tracking=True)

    issue_severity = fields.Selection([
        ('low', 'Low - Minor issue, bin still usable'),
        ('medium', 'Medium - Issue affects functionality'),
        ('high', 'High - Bin unusable, replacement needed'),
        ('critical', 'Critical - Safety hazard')
    ], string="Severity", required=True, default='medium', tracking=True)

    issue_description = fields.Text(
        string="Issue Description",
        required=True,
        help="Detailed description of the issue for work order creation"
    )

    # ============================================================================
    # FAULT DETERMINATION & BILLING
    # ============================================================================
    customer_fault_confirmed = fields.Boolean(
        string="Customer Fault Confirmed",
        help="Check if customer fault has been confirmed for billing purposes"
    )

    fault_evidence = fields.Text(
        string="Fault Evidence",
        help="Evidence supporting fault determination (for billing disputes)"
    )

    estimated_replacement_cost = fields.Monetary(
        string="Estimated Replacement/Repair Cost",
        currency_field='currency_id',
        help="Estimated cost for billing calculation"
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # ============================================================================
    # PHOTO DOCUMENTATION (Leveraging existing system)
    # ============================================================================
    require_photos = fields.Boolean(
        string="Photos Required",
        compute='_compute_require_photos',
        help="Photos are required for damage claims and certain issues"
    )

    photo_ids = fields.One2many(
        comodel_name='mobile.photo',
        inverse_name='wizard_reference',
        string="Issue Photos",
        help="Photos documenting the bin issue"
    )

    photo_count = fields.Integer(
        string="Photo Count",
        compute='_compute_photo_count'
    )

    gps_latitude = fields.Float(
        string="GPS Latitude",
        digits=(10, 7),
        help="GPS coordinates where issue was discovered"
    )

    gps_longitude = fields.Float(
        string="GPS Longitude",
        digits=(10, 7),
        help="GPS coordinates where issue was discovered"
    )

    # ============================================================================
    # WORK ORDER CREATION
    # ============================================================================
    create_work_order = fields.Boolean(
        string="Create Work Order",
        default=True,
        help="Automatically create work order for issue resolution"
    )

    work_order_priority = fields.Selection([
        ('0', 'Very Low'),
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High')
    ], string="Work Order Priority", compute='_compute_work_order_priority', store=True)

    scheduled_date = fields.Datetime(
        string="Scheduled Resolution Date",
        help="When the work order should be scheduled"
    )

    assigned_technician_id = fields.Many2one(
        comodel_name="res.users",
        string="Assigned Technician",
        domain=lambda self: [("groups_id", "in", [self.env.ref("records_management.group_records_user").id])],
    )

    # ============================================================================
    # CUSTOMER COMMUNICATION
    # ============================================================================
    notify_customer = fields.Boolean(
        string="Notify Customer",
        default=True,
        help="Send notification to customer about the issue"
    )

    customer_message = fields.Text(
        string="Customer Message",
        help="Message to send to customer about the issue"
    )

    # ============================================================================
    # BILLING INTEGRATION
    # ============================================================================
    bill_customer = fields.Boolean(
        string="Bill Customer",
        compute='_compute_bill_customer',
        store=True,
        help="Whether to bill customer for this issue"
    )

    billing_rate_id = fields.Many2one(
        comodel_name='base.rates',
        string="Billing Rate",
        domain=[('rate_type', '=', 'other'), ('active', '=', True)],
        help="Rate to use for billing damaged bin replacement"
    )

    billing_amount = fields.Monetary(
        string="Billing Amount",
        currency_field='currency_id',
        compute='_compute_billing_amount',
        store=True
    )

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('issue_type')
    def _compute_require_photos(self):
        """Photos required for damage claims and certain issues."""
        for record in self:
            photo_required_types = ['damaged_customer_fault', 'damaged_company_fault', 'lost_stolen']
            record.require_photos = record.issue_type in photo_required_types

    @api.depends('photo_ids')
    def _compute_photo_count(self):
        """Count attached photos."""
        for record in self:
            record.photo_count = len(record.photo_ids)

    @api.depends('issue_type', 'issue_severity')
    def _compute_work_order_priority(self):
        """Compute work order priority based on issue type and severity."""
        for record in self:
            if record.issue_severity == 'critical':
                record.work_order_priority = '3'  # High
            elif record.issue_type == 'damaged_customer_fault':
                record.work_order_priority = '3'  # High - billable, urgent
            elif record.issue_severity == 'high':
                record.work_order_priority = '2'  # Normal
            elif record.issue_type in ['missing_label', 'bad_barcode']:
                record.work_order_priority = '1'  # Low - maintenance
            else:
                record.work_order_priority = '2'  # Normal

    @api.depends('issue_type', 'customer_fault_confirmed')
    def _compute_bill_customer(self):
        """Determine if customer should be billed."""
        for record in self:
            billable_types = ['damaged_customer_fault', 'lost_stolen']
            record.bill_customer = record.issue_type in billable_types and record.customer_fault_confirmed

    @api.depends('bill_customer', 'billing_rate_id', 'estimated_replacement_cost')
    def _compute_billing_amount(self):
        """Compute billing amount from rates or estimate."""
        for record in self:
            if not record.bill_customer:
                record.billing_amount = 0.0
                continue

            # Try to get damaged bin rate from base rates
            if record.billing_rate_id:
                record.billing_amount = record.billing_rate_id.base_rate
            elif record.estimated_replacement_cost:
                record.billing_amount = record.estimated_replacement_cost
            else:
                # Fallback - get default damaged bin rate
                damaged_bin_rate = self.env['base.rates'].search([
                    ('name', 'ilike', 'damaged bin'),
                    ('active', '=', True),
                    ('effective_date', '<=', fields.Date.today()),
                    '|', ('expiry_date', '=', False), ('expiry_date', '>', fields.Date.today())
                ], limit=1)

                if damaged_bin_rate:
                    record.billing_amount = damaged_bin_rate.base_rate
                else:
                    # Default damaged bin replacement cost based on bin size
                    bin_replacement_costs = {
                        '23': 45.00,   # 23 gallon Shredinator
                        '32g': 65.00,  # 32 gallon bin
                        '32c': 70.00,  # 32 gallon console
                        '64': 95.00,   # 64 gallon bin
                        '96': 125.00,  # 96 gallon bin
                    }
                    record.billing_amount = bin_replacement_costs.get(record.bin_id.bin_size, 65.00)

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('issue_type')
    def _onchange_issue_type(self):
        """Update fields based on issue type selection."""
        if self.issue_type:
            # Auto-populate customer message based on issue type
            message_templates = {
                'damaged_customer_fault': _("We've identified damage to your shred bin that appears to be caused by misuse. A replacement charge will apply. Our technician will contact you to schedule replacement."),
                'damaged_company_fault': _("We've identified wear and tear damage to your shred bin. We'll replace it at no charge. Our technician will contact you to schedule replacement."),
                'missing_label': _("Your shred bin is missing its identification label. Our technician will visit to install a new label. No charge applies."),
                'bad_barcode': _("Your shred bin's barcode is unreadable. Our technician will visit to install a new barcode label. No charge applies."),
                'maintenance_required': _("Your shred bin requires maintenance. Our technician will contact you to schedule service."),
                'lost_stolen': _("Your shred bin appears to be lost or stolen. A replacement charge will apply. Please contact us immediately if you locate the bin."),
            }
            self.customer_message = message_templates.get(self.issue_type, '')

            # Set fault confirmation for clearly customer-fault issues
            if self.issue_type in ['damaged_customer_fault', 'lost_stolen']:
                self.customer_fault_confirmed = True
            else:
                self.customer_fault_confirmed = False

    @api.onchange('bin_id')
    def _onchange_bin_id(self):
        """Populate related fields when bin is selected."""
        if self.bin_id:
            self.customer_id = self.bin_id.current_customer_id
            self.location_id = self.bin_id.last_scan_location_id

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_take_photo(self):
        """Open mobile photo capture interface."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Take Issue Photo"),
            "res_model": "mobile.photo",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": _("Bin Issue: %s - %s") % (self.bin_id.barcode, self.issue_type or "Unknown"),
                "default_photo_type": "damage_report",
                "default_wizard_reference": str(self.id),
                "default_partner_id": self.customer_id.id if self.customer_id else False,
                "default_gps_latitude": self.gps_latitude,
                "default_gps_longitude": self.gps_longitude,
                "default_compliance_notes": self.issue_description,
                "default_is_compliance_photo": True,
            },
        }

    def action_view_photos(self):
        """View all photos attached to this issue report."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Issue Photos: %s") % self.bin_id.barcode,
            "res_model": "mobile.photo",
            "view_mode": "kanban,list,form",
            "domain": [("wizard_reference", "=", str(self.id))],
            "context": {"search_default_group_by_type": 1},
        }

    def action_submit_report(self):
        """Submit the issue report and create work order."""
        self.ensure_one()

        # Validate required information
        self._validate_report()

        # Create work order if requested
        work_order = None
        if self.create_work_order:
            work_order = self._create_work_order()

        # Create billing if applicable
        if self.bill_customer and self.billing_amount > 0:
            self._create_billing_record(work_order)

        # Send customer notification if requested
        if self.notify_customer and self.customer_message:
            self._send_customer_notification()

        # Create issue record for tracking
        issue_record = self._create_issue_record(work_order)

        # Update bin status
        self._update_bin_status()

        # Create audit log
        self._create_audit_log(issue_record, work_order)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Issue Report Created'),
            'res_model': 'bin.issue.record',
            'res_id': issue_record.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    def _validate_report(self):
        """Validate issue report before submission."""
        self.ensure_one()

        # Require photos for damage claims
        if self.require_photos and self.photo_count == 0:
            raise ValidationError(_(
                "Photos are required for this type of issue. Please take at least one photo documenting the problem."
            ))

        # Require fault evidence for customer billing
        if self.bill_customer and not self.fault_evidence:
            raise ValidationError(_(
                "Fault evidence is required when billing the customer. Please document why this is customer fault."
            ))

        # Validate GPS coordinates if provided
        if self.gps_latitude and not (-90 <= self.gps_latitude <= 90):
            raise ValidationError(_("GPS latitude must be between -90 and 90 degrees."))

        if self.gps_longitude and not (-180 <= self.gps_longitude <= 180):
            raise ValidationError(_("GPS longitude must be between -180 and 180 degrees."))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _create_work_order(self):
        """Create work order for issue resolution."""
        self.ensure_one()

        # Determine billing status for work order
        billable = self.bill_customer and self.billing_amount > 0

        work_order = self.bin_id.create_issue_work_order(
            issue_type=self.issue_type,
            description=self._format_work_order_description(),
            estimated_cost=self.billing_amount if billable else 0.0,
            billable=billable
        )

        # Update work order with additional details
        update_vals = {
            'priority': self.work_order_priority,
            'date_deadline': self.scheduled_date.date() if self.scheduled_date else fields.Date.today(),
        }

        if self.assigned_technician_id:
            update_vals['user_ids'] = [(6, 0, [self.assigned_technician_id.id])]

        if self.customer_id:
            update_vals['partner_id'] = self.customer_id.id

        work_order.write(update_vals)

        return work_order

    def _format_work_order_description(self):
        """Format detailed description for work order."""
        description = [
            _("BIN ISSUE REPORT"),
            "=" * 50,
            _("Bin: %s (%s)") % (self.bin_id.barcode, self.bin_id.bin_size),
            _("Issue Type: %s") % dict(self.issue_type and self._fields["issue_type"].selection).get(self.issue_type, ""),
            _("Severity: %s") % dict(self._fields["issue_severity"].selection).get(self.issue_severity, ""),
            "",
            _("ISSUE DESCRIPTION:"),
            self.issue_description or _("No description provided"),
            "",
        ]
        if self.customer_id:
            description.extend([
                _("LOCATION DETAILS:"),
                _("Customer: %s") % self.customer_id.name,
                _("Address: %s") % self._format_address(),
                "",
            ])
        if self.gps_latitude and self.gps_longitude:
            description.extend([
                _("GPS COORDINATES:"),
                _("Latitude: %s") % self.gps_latitude,
                _("Longitude: %s") % self.gps_longitude,
                "",
            ])
        if self.fault_evidence:
            description.extend([
                _("FAULT EVIDENCE:"),
                self.fault_evidence,
                "",
            ])
        if self.bill_customer:
            description.extend([
                _("BILLING INFORMATION:"),
                _("Customer Fault: Yes"),
                _("Estimated Cost: %s %s") % (self.billing_amount, self.currency_id.symbol),
                "",
            ])
        if self.photo_count > 0:
            description.extend([
                _("DOCUMENTATION:"),
                _("Photos attached: %s") % self.photo_count,
                _("View photos in work order attachments"),
                "",
            ])
        return "\n".join(description)

    def _format_address(self):
        """Format customer address for work order."""
        if not self.customer_id:
            return _("No address available")

        address_parts = []
        if self.customer_id.street:
            address_parts.append(self.customer_id.street)
        if self.customer_id.street2:
            address_parts.append(self.customer_id.street2)
        if self.customer_id.city:
            address_parts.append(self.customer_id.city)
        if self.customer_id.state_id:
            address_parts.append(self.customer_id.state_id.name)
        if self.customer_id.zip:
            address_parts.append(self.customer_id.zip)

        return ", ".join(address_parts) if address_parts else _("No address available")

    def _create_billing_record(self, work_order):
        """Create billing record for customer fault issues."""
        # This would integrate with accounting module
        # Security: Log only non-sensitive metadata, not billing amounts or customer details
        _logger.info(
            "Billing record creation initiated for bin issue: Bin ID=%s, Work Order ID=%s",
            self.bin_id.id if self.bin_id else 'None',
            work_order.id if work_order else 'None'
        )

    def _send_customer_notification(self):
        """Send notification to customer about the issue."""
        if not self.customer_id or not self.customer_message:
            return

        # Create mail message
        template_values = {
            "subject": _(
                "Shred Bin Issue Report - %s"
            ) % self.bin_id.barcode,
            "body_html": self._format_customer_email(),
            "partner_ids": [(6, 0, [self.customer_id.id])],
            "model": "shredding.service.bin",
            "res_id": self.bin_id.id,
        }

        mail = self.env['mail.mail'].create(template_values)
        mail.send()

    def _format_customer_email(self):
        """Format customer notification email."""
        return _("""
        <p>Dear %s,</p>

        <p>We have identified an issue with your shred bin <strong>%s</strong> located at your facility.</p>

        <p><strong>Issue Details:</strong></p>
        <ul>
            <li>Issue Type: %s</li>
            <li>Severity: %s</li>
            <li>Description: %s</li>
        </ul>

        <p>%s</p>

        %s

        <p>If you have any questions, please contact us immediately.</p>

        <p>Best regards,<br/>
        Records Management Team</p>
        """) % (
            self.customer_id.name,
            self.bin_id.barcode,
            dict(self._fields['issue_type'].selection).get(self.issue_type, ''),
            dict(self._fields['issue_severity'].selection).get(self.issue_severity, ''),
            self.issue_description,
            self.customer_message,
            self._format_billing_notice() if self.bill_customer else ''
        )

    def _format_billing_notice(self):
        """Format billing notice for customer email."""
        if not self.bill_customer:
            return ''

        return _("""
        <p><strong>Important Billing Notice:</strong></p>
        <p>This issue has been determined to be caused by customer fault.
        A replacement/repair charge of <strong>%s %s</strong> will be applied to your account.</p>
        """) % (self.billing_amount, self.currency_id.symbol)

    def _create_issue_record(self, work_order):
        """Create permanent issue record for tracking."""
        issue_vals = {
            "name": _("Issue: %s - %s") % (self.bin_id.barcode, self.issue_type),
            "bin_id": self.bin_id.id,
            "issue_type": self.issue_type,
            "issue_severity": self.issue_severity,
            "description": self.issue_description,
            "customer_id": self.customer_id.id if self.customer_id else False,
            "location_id": self.location_id.id if self.location_id else False,
            "work_order_id": work_order.id if work_order else False,
            "reported_by_id": self.env.user.id,
            "report_date": fields.Datetime.now(),
            "customer_fault": self.customer_fault_confirmed,
            "billing_amount": self.billing_amount if self.bill_customer else 0.0,
            "resolution_status": "reported",
            "gps_latitude": self.gps_latitude,
            "gps_longitude": self.gps_longitude,
        }
        return self.env['bin.issue.record'].create(issue_vals)

    def _update_bin_status(self):
        """Update bin status based on issue type."""
        if self.issue_type in ['damaged_customer_fault', 'damaged_company_fault']:
            self.bin_id.write({'status': 'maintenance'})
        elif self.issue_type == 'lost_stolen':
            self.bin_id.write({'status': 'retired'})

    def _create_audit_log(self, issue_record, work_order):
        """Create NAID compliance audit log."""
        description = _("Bin issue reported: %s") % issue_record.name
        if work_order:
            description += _(" - Work Order %s created") % work_order.name
        if self.bill_customer:
            description += _(" - Customer billing required: %s %s") % (self.billing_amount, self.currency_id.symbol)
        self.bin_id._create_service_audit_log('issue_reported', description)


# ============================================================================
# BIN ISSUE RECORD MODEL (Permanent tracking)
# ============================================================================
    # Note: Persistent bin issue records live in models/bin_issue_record.py
    # This wizard file should only contain TransientModel definitions.
