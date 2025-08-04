# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CustomerInventoryReport(models.Model):
    _name = "customer.inventory.report"
    _description = "Customer Inventory Report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "report_date desc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Report Name", required=True, tracking=True, index=True)
    report_number = fields.Char(string="Report Number", index=True)
    description = fields.Text(string="Report Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # Framework Required Fields
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Report Creator",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("generating", "Generating"),
            ("ready", "Ready"),
            ("sent", "Sent to Customer"),
            ("confirmed", "Confirmed"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # CUSTOMER & REPORT DETAILS
    # ============================================================================

    # Customer Information
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        domain=[("is_company", "=", True)],
    )
    customer_name = fields.Char(
        string="Customer Name",
        related="customer_id.name",
        store=True,
    )
    customer_contact_id = fields.Many2one(
        "res.partner",
        string="Customer Contact",
        domain="[('parent_id', '=', customer_id)]",
    )

    # Report Period
    report_period = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annual", "Semi-Annual"),
            ("annual", "Annual"),
            ("custom", "Custom Period"),
        ],
        string="Report Period",
        default="monthly",
        required=True,
    )

    report_date = fields.Date(
        string="Report Date",
        default=fields.Date.today,
        required=True,
    )
    period_start_date = fields.Date(string="Period Start Date", required=True)
    period_end_date = fields.Date(string="Period End Date", required=True)

    # ============================================================================
    # INVENTORY METRICS
    # ============================================================================

    # Document Counts
    total_documents = fields.Integer(
        string="Total Documents",
        compute="_compute_inventory_metrics",
        store=True,
    )
    active_documents = fields.Integer(
        string="Active Documents",
        compute="_compute_inventory_metrics",
        store=True,
    )
    archived_documents = fields.Integer(
        string="Archived Documents",
        compute="_compute_inventory_metrics",
        store=True,
    )

    # Box Counts
    total_boxes = fields.Integer(
        string="Total Boxes",
        compute="_compute_inventory_metrics",
        store=True,
    )
    active_boxes = fields.Integer(
        string="Active Boxes",
        compute="_compute_inventory_metrics",
        store=True,
    )
    destroyed_boxes = fields.Integer(
        string="Destroyed Boxes",
        compute="_compute_inventory_metrics",
        store=True,
    )

    # Storage Metrics
    total_storage_volume = fields.Float(
        string="Total Storage Volume (Cubic Ft)",
        compute="_compute_storage_metrics",
        store=True,
        digits=(10, 2),
    )
    storage_utilization = fields.Float(
        string="Storage Utilization (%)",
        compute="_compute_storage_metrics",
        store=True,
        digits=(5, 2),
    )

    # Activity Metrics
    documents_added = fields.Integer(
        string="Documents Added This Period",
        compute="_compute_activity_metrics",
        store=True,
    )
    documents_retrieved = fields.Integer(
        string="Documents Retrieved This Period",
        compute="_compute_activity_metrics",
        store=True,
    )
    documents_destroyed = fields.Integer(
        string="Documents Destroyed This Period",
        compute="_compute_activity_metrics",
        store=True,
    )

    # ============================================================================
    # FINANCIAL INFORMATION
    # ============================================================================

    # Currency Configuration
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Cost Breakdown
    storage_costs = fields.Monetary(
        string="Storage Costs",
        currency_field="currency_id",
        compute="_compute_financial_metrics",
        store=True,
    )
    service_costs = fields.Monetary(
        string="Service Costs",
        currency_field="currency_id",
        compute="_compute_financial_metrics",
        store=True,
    )
    destruction_costs = fields.Monetary(
        string="Destruction Costs",
        currency_field="currency_id",
        compute="_compute_financial_metrics",
        store=True,
    )
    total_costs = fields.Monetary(
        string="Total Costs",
        currency_field="currency_id",
        compute="_compute_financial_metrics",
        store=True,
    )

    # Period Comparisons
    previous_period_cost = fields.Monetary(
        string="Previous Period Cost",
        currency_field="currency_id",
    )
    cost_variance = fields.Monetary(
        string="Cost Variance",
        currency_field="currency_id",
        compute="_compute_variance_metrics",
        store=True,
    )
    cost_variance_percentage = fields.Float(
        string="Cost Variance %",
        compute="_compute_variance_metrics",
        store=True,
        digits=(5, 2),
    )

    # ============================================================================
    # COMPLIANCE & QUALITY
    # ============================================================================

    # Compliance Status
    compliance_status = fields.Selection(
        [
            ("compliant", "Fully Compliant"),
            ("minor_issues", "Minor Issues"),
            ("major_issues", "Major Issues"),
            ("non_compliant", "Non-Compliant"),
        ],
        string="Compliance Status",
        default="compliant",
        tracking=True,
    )

    compliance_score = fields.Float(
        string="Compliance Score (%)",
        digits=(5, 2),
        compute="_compute_compliance_metrics",
        store=True,
    )

    retention_violations = fields.Integer(
        string="Retention Policy Violations",
        compute="_compute_compliance_metrics",
        store=True,
    )
    security_issues = fields.Integer(
        string="Security Issues",
        compute="_compute_compliance_metrics",
        store=True,
    )

    # Quality Metrics
    service_quality_score = fields.Float(
        string="Service Quality Score",
        digits=(3, 2),
        default=5.0,
    )
    customer_satisfaction = fields.Selection(
        [
            ("1", "Very Dissatisfied"),
            ("2", "Dissatisfied"),
            ("3", "Neutral"),
            ("4", "Satisfied"),
            ("5", "Very Satisfied"),
        ],
        string="Customer Satisfaction",
    )

    # ============================================================================
    # REPORT GENERATION & DELIVERY
    # ============================================================================

    # Generation Information
    report_generation_date = fields.Datetime(
        string="Generation Date",
        readonly=True,
    )
    generated_by_id = fields.Many2one(
        "res.users",
        string="Generated By",
        readonly=True,
    )
    generation_duration = fields.Float(
        string="Generation Time (Minutes)",
        digits=(5, 2),
        readonly=True,
    )

    # Delivery Information
    delivery_method = fields.Selection(
        [
            ("email", "Email"),
            ("portal", "Customer Portal"),
            ("mail", "Physical Mail"),
            ("pickup", "Customer Pickup"),
        ],
        string="Delivery Method",
        default="email",
    )
    delivery_date = fields.Datetime(string="Delivery Date")
    delivery_confirmed = fields.Boolean(string="Delivery Confirmed", default=False)

    # Report Format
    report_format = fields.Selection(
        [
            ("pdf", "PDF Report"),
            ("excel", "Excel Spreadsheet"),
            ("csv", "CSV Data"),
            ("json", "JSON Data"),
        ],
        string="Report Format",
        default="pdf",
    )

    # ============================================================================
    # LOCATIONS & SERVICES
    # ============================================================================

    # Location Summary
    primary_location_id = fields.Many2one(
        "records.location",
        string="Primary Storage Location",
    )
    total_locations = fields.Integer(
        string="Total Storage Locations",
        compute="_compute_location_metrics",
        store=True,
    )

    # Service Summary
    active_services = fields.Text(
        string="Active Services",
        compute="_compute_service_summary",
        store=True,
    )
    service_requests_count = fields.Integer(
        string="Service Requests This Period",
        compute="_compute_service_metrics",
        store=True,
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Related Records
    box_ids = fields.Many2many(
        "records.container",
        string="Customer Boxes",
        compute="_compute_related_records",
        store=True,
    )
    document_ids = fields.Many2many(
        "records.document",
        string="Customer Documents",
        compute="_compute_related_records",
        store=True,
    )
    service_request_ids = fields.One2many(
        "portal.request",
        "customer_id",
        string="Service Requests",
        domain="[('request_date', '>=', period_start_date), ('request_date', '<=', period_end_date)]",
    )

    # Report Attachments
    report_file = fields.Binary(string="Generated Report File")
    report_filename = fields.Char(string="Report Filename")

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # NOTES & COMMENTS
    # ============================================================================

    notes = fields.Text(string="Internal Notes")
    customer_notes = fields.Text(string="Customer Notes")
    recommendations = fields.Text(string="Recommendations")
    next_actions = fields.Text(string="Next Actions")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("customer_id", "period_start_date", "period_end_date")
    def _compute_inventory_metrics(self):
        """Compute inventory metrics for the customer and period"""
        for record in self:
            if not record.customer_id:
                record.update({
                    'total_documents': 0,
                    'active_documents': 0,
                    'archived_documents': 0,
                    'total_boxes': 0,
                    'active_boxes': 0,
                    'destroyed_boxes': 0,
                })
                continue

            # Document counts
            domain = [('customer_id', '=', record.customer_id.id)]
            all_docs = self.env['records.document'].search(domain)
            record.total_documents = len(all_docs)
            record.active_documents = len(all_docs.filtered(lambda d: d.active))
            record.archived_documents = len(all_docs.filtered(lambda d: not d.active))

            # Box counts
            box_domain = [('customer_id', '=', record.customer_id.id)]
            all_boxes = self.env['records.container'].search(box_domain)
            record.total_boxes = len(all_boxes)
            record.active_boxes = len(all_boxes.filtered(lambda b: b.state in ['active', 'stored']))
            record.destroyed_boxes = len(all_boxes.filtered(lambda b: b.state == 'destroyed'))

    @api.depends("customer_id")
    def _compute_storage_metrics(self):
        """Compute storage utilization metrics"""
        for record in self:
            if not record.customer_id:
                record.total_storage_volume = 0.0
                record.storage_utilization = 0.0
                continue

            # Calculate total storage volume
            boxes = self.env['records.container'].search([('customer_id', '=', record.customer_id.id)])
            total_volume = sum(box.volume for box in boxes if box.volume)
            record.total_storage_volume = total_volume

            # Storage utilization (simplified calculation)
            if total_volume > 0:
                # Assume capacity based on box count * average capacity
                estimated_capacity = len(boxes) * 2.0  # 2 cubic feet per box average
                record.storage_utilization = min((total_volume / estimated_capacity) * 100, 100) if estimated_capacity else 0
            else:
                record.storage_utilization = 0.0

    @api.depends("customer_id", "period_start_date", "period_end_date")
    def _compute_activity_metrics(self):
        """Compute activity metrics for the period"""
        for record in self:
            if not (record.customer_id and record.period_start_date and record.period_end_date):
                record.update({
                    'documents_added': 0,
                    'documents_retrieved': 0,
                    'documents_destroyed': 0,
                })
                continue

            # Documents added during period
            added_docs = self.env['records.document'].search([
                ('customer_id', '=', record.customer_id.id),
                ('create_date', '>=', record.period_start_date),
                ('create_date', '<=', record.period_end_date),
            ])
            record.documents_added = len(added_docs)

            # Simplified metrics for retrieved and destroyed
            # In a real implementation, you'd track these activities
            record.documents_retrieved = 0  # Would be computed from retrieval requests
            record.documents_destroyed = 0  # Would be computed from destruction records

    @api.depends("customer_id", "period_start_date", "period_end_date")
    def _compute_financial_metrics(self):
        """Compute financial metrics"""
        for record in self:
            if not record.customer_id:
                record.update({
                    'storage_costs': 0.0,
                    'service_costs': 0.0,
                    'destruction_costs': 0.0,
                    'total_costs': 0.0,
                })
                continue

            # Simplified cost calculation
            # In real implementation, would pull from invoices and service records
            monthly_storage = record.total_boxes * 5.0  # $5 per box per month
            
            # Calculate months in period
            if record.period_start_date and record.period_end_date:
                days = (record.period_end_date - record.period_start_date).days
                months = max(days / 30.0, 1.0)
            else:
                months = 1.0

            record.storage_costs = monthly_storage * months
            record.service_costs = record.service_requests_count * 25.0  # $25 per service request
            record.destruction_costs = record.destroyed_boxes * 15.0  # $15 per box destruction
            record.total_costs = record.storage_costs + record.service_costs + record.destruction_costs

    @api.depends("total_costs", "previous_period_cost")
    def _compute_variance_metrics(self):
        """Compute variance metrics"""
        for record in self:
            if record.previous_period_cost:
                record.cost_variance = record.total_costs - record.previous_period_cost
                record.cost_variance_percentage = (record.cost_variance / record.previous_period_cost) * 100
            else:
                record.cost_variance = 0.0
                record.cost_variance_percentage = 0.0

    @api.depends("customer_id")
    def _compute_compliance_metrics(self):
        """Compute compliance metrics"""
        for record in self:
            if not record.customer_id:
                record.update({
                    'compliance_score': 100.0,
                    'retention_violations': 0,
                    'security_issues': 0,
                })
                continue

            # Simplified compliance calculation
            # In real implementation, would check actual compliance records
            violations = 0  # Would be computed from compliance audits
            security_issues = 0  # Would be computed from security logs

            record.retention_violations = violations
            record.security_issues = security_issues
            
            # Calculate compliance score
            total_issues = violations + security_issues
            if total_issues == 0:
                record.compliance_score = 100.0
            else:
                record.compliance_score = max(100.0 - (total_issues * 10), 0.0)

    @api.depends("customer_id")
    def _compute_location_metrics(self):
        """Compute location metrics"""
        for record in self:
            if record.customer_id:
                locations = self.env['records.location'].search([
                    ('box_ids.customer_id', '=', record.customer_id.id)
                ])
                record.total_locations = len(locations.ids)
            else:
                record.total_locations = 0

    @api.depends("customer_id", "period_start_date", "period_end_date")
    def _compute_service_metrics(self):
        """Compute service metrics"""
        for record in self:
            if record.customer_id and record.period_start_date and record.period_end_date:
                service_requests = self.env['portal.request'].search([
                    ('partner_id', '=', record.customer_id.id),
                    ('request_date', '>=', record.period_start_date),
                    ('request_date', '<=', record.period_end_date),
                ])
                record.service_requests_count = len(service_requests)
            else:
                record.service_requests_count = 0

    @api.depends("customer_id")
    def _compute_service_summary(self):
        """Compute active services summary"""
        for record in self:
            if record.customer_id:
                # Build summary of active services
                services = []
                if record.total_boxes > 0:
                    services.append(f"Document Storage ({record.total_boxes} boxes)")
                if record.service_requests_count > 0:
                    services.append(f"Service Requests ({record.service_requests_count} this period)")
                
                record.active_services = "\n".join(services) if services else "No active services"
            else:
                record.active_services = ""

    @api.depends("customer_id")
    def _compute_related_records(self):
        """Compute related records"""
        for record in self:
            if record.customer_id:
                boxes = self.env['records.container'].search([('customer_id', '=', record.customer_id.id)])
                documents = self.env['records.document'].search([('customer_id', '=', record.customer_id.id)])
                record.box_ids = [(6, 0, boxes.ids)]
                record.document_ids = [(6, 0, documents.ids)]
            else:
                record.box_ids = [(6, 0, [])]
                record.document_ids = [(6, 0, [])]

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_generate_report(self):
        """Generate the inventory report"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft reports can be generated."))

        start_time = fields.Datetime.now()
        
        self.write({
            'state': 'generating',
            'report_generation_date': start_time,
            'generated_by_id': self.env.user.id,
        })
        
        # Simulate report generation
        # In real implementation, this would generate the actual report file
        
        end_time = fields.Datetime.now()
        duration = (end_time - start_time).total_seconds() / 60.0
        
        self.write({
            'state': 'ready',
            'generation_duration': duration,
            'report_filename': f"{self.name}.pdf",
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Report Generated'),
                'message': _('Inventory report has been generated successfully.'),
                'type': 'success',
            },
        }

    def action_send_to_customer(self):
        """Send report to customer"""
        self.ensure_one()
        if self.state != 'ready':
            raise UserError(_("Only ready reports can be sent."))

        if not self.customer_contact_id and not self.customer_id.email:
            raise UserError(_("Customer must have an email address to send report."))

        # Send email with report
        template = self.env.ref('records_management.mail_template_inventory_report', False)
        if template:
            template.send_mail(self.id, force_send=True)

        self.write({
            'state': 'sent',
            'delivery_date': fields.Datetime.now(),
            'delivery_method': 'email',
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Report Sent'),
                'message': _('Report has been sent to customer successfully.'),
                'type': 'success',
            },
        }

    def action_confirm_delivery(self):
        """Confirm report delivery"""
        self.ensure_one()
        self.write({
            'delivery_confirmed': True,
            'state': 'confirmed',
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Delivery Confirmed'),
                'message': _('Report delivery has been confirmed.'),
                'type': 'success',
            },
        }

    def action_view_customer_records(self):
        """View customer's records"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Records'),
            'res_model': 'records.container',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.customer_id.id)],
            'context': {'default_customer_id': self.customer_id.id},
        }

    def action_schedule_next_report(self):
        """Schedule next period report"""
        self.ensure_one()
        
        # Calculate next period dates
        if self.report_period == 'monthly':
            next_start = self.period_end_date + fields.timedelta(days=1)
            next_end = next_start + fields.timedelta(days=30)
        elif self.report_period == 'quarterly':
            next_start = self.period_end_date + fields.timedelta(days=1)
            next_end = next_start + fields.timedelta(days=90)
        else:
            next_start = self.period_end_date + fields.timedelta(days=1)
            next_end = next_start + fields.timedelta(days=365)

        # Create next report
        next_report = self.create({
            'name': f"{self.customer_id.name} - {self.report_period.title()} Report - {next_end.strftime('%Y-%m')}",
            'customer_id': self.customer_id.id,
            'customer_contact_id': self.customer_contact_id.id,
            'report_period': self.report_period,
            'period_start_date': next_start,
            'period_end_date': next_end,
            'report_format': self.report_format,
            'delivery_method': self.delivery_method,
            'previous_period_cost': self.total_costs,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Next Period Report'),
            'res_model': 'customer.inventory.report',
            'res_id': next_report.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains('period_start_date', 'period_end_date')
    def _check_period_dates(self):
        """Ensure period dates are logical"""
        for record in self:
            if record.period_start_date and record.period_end_date:
                if record.period_end_date <= record.period_start_date:
                    raise ValidationError(_("Period end date must be after start date."))

    @api.constrains('service_quality_score')
    def _check_quality_score(self):
        """Ensure quality score is within valid range"""
        for record in self:
            if record.service_quality_score and not (0 <= record.service_quality_score <= 10):
                raise ValidationError(_("Service quality score must be between 0 and 10."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model
    def create(self, vals):
        """Override create to set defaults"""
        if not vals.get('report_number'):
            vals['report_number'] = self.env['ir.sequence'].next_by_code('customer.inventory.report') or 'CIR'
        
        # Set period dates based on report period if not provided
        if not vals.get('period_start_date') and vals.get('report_period'):
            today = fields.Date.today()
            if vals['report_period'] == 'monthly':
                vals['period_start_date'] = today.replace(day=1)
                vals['period_end_date'] = today
            elif vals['report_period'] == 'quarterly':
                # Start of quarter
                quarter_start = today.replace(month=((today.month - 1) // 3) * 3 + 1, day=1)
                vals['period_start_date'] = quarter_start
                vals['period_end_date'] = today

        return super().create(vals)

    def write(self, vals):
        """Override write to track changes"""
        if 'state' in vals:
            for record in self:
                old_state = dict(record._fields['state'].selection).get(record.state)
                new_state = dict(record._fields['state'].selection).get(vals['state'])
                record.message_post(
                    body=_("Report status changed from %s to %s") % (old_state, new_state)
                )

        return super().write(vals)
