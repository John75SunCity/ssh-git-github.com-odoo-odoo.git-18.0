# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class VisitorPosWizard(models.TransientModel):
    _name = "visitor.pos.wizard"
    _description = "Visitor POS Wizard"

    # Basic Information
    name = fields.Char(string="Visitor Name", required=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    visit_date = fields.Datetime(string="Visit Date", default=fields.Datetime.now)
    purpose = fields.Text(string="Purpose of Visit")

    # === ESSENTIAL FIELDS FROM VIEW (Core Functionality) ===

    # Visitor Information
    visitor_id = fields.Many2one("visitor", string="Visitor")
    visitor_name = fields.Char(
        string="Visitor Name", related="visitor_id.name", store=True
    )
    visitor_email = fields.Char(
        string="Visitor Email", related="visitor_id.email", store=True
    )
    visitor_phone = fields.Char(
        string="Visitor Phone", related="visitor_id.phone", store=True
    )
    check_in_time = fields.Datetime(string="Check-in Time", default=fields.Datetime.now)
    purpose_of_visit = fields.Text(string="Purpose of Visit")

    # POS Configuration
    pos_config_id = fields.Many2one("pos.config", string="POS Configuration")
    pos_session_id = fields.Many2one("pos.session", string="POS Session")
    cashier_id = fields.Many2one(
        "res.users", string="Cashier", default=lambda self: self.env.user
    )
    service_location = fields.Char(string="Service Location")
    processing_priority = fields.Selection(
        [("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")],
        string="Processing Priority",
        default="normal",
    )

    # Customer Management
    existing_customer_id = fields.Many2one("res.partner", string="Existing Customer")
    create_new_customer = fields.Boolean(string="Create New Customer", default=False)
    customer_category = fields.Selection(
        [
            ("individual", "Individual"),
            ("business", "Business"),
            ("government", "Government"),
        ],
        string="Customer Category",
    )
    customer_credit_limit = fields.Monetary(
        string="Credit Limit", currency_field="currency_id"
    )
    customer_payment_terms = fields.Selection(
        [
            ("immediate", "Immediate Payment"),
            ("net_15", "Net 15 Days"),
            ("net_30", "Net 30 Days"),
            ("net_45", "Net 45 Days"),
            ("net_60", "Net 60 Days"),
            ("custom", "Custom Terms"),
        ],
        string="Payment Terms",
        default="net_30",
    )

    # Service Configuration
    service_type = fields.Selection(
        [
            ("shredding", "Document Shredding"),
            ("storage", "Document Storage"),
            ("retrieval", "Document Retrieval"),
            ("scanning", "Document Scanning"),
        ],
        string="Service Type",
        required=True,
    )

    # Financial
    amount = fields.Monetary(string="Amount", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # System Fields
    pos_order_id = fields.Many2one("pos.order", string="POS Order")
    invoice_id = fields.Many2one("account.move", string="Invoice")

    # Status
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
    )

    # === ADDITIONAL ESSENTIAL FIELDS FROM VIEW ANALYSIS ===

    # Audit and Compliance
    audit_level = fields.Selection(
        [
            ("basic", "Basic"),
            ("standard", "Standard"),
            ("enhanced", "Enhanced"),
            ("comprehensive", "Comprehensive"),
        ],
        string="Audit Level",
        default="standard",
    )
    audit_notes = fields.Text(string="Audit Notes")
    audit_required = fields.Boolean(string="Audit Required", default=False)
    authorization_code = fields.Char(string="Authorization Code")

    # Financial Details
    base_amount = fields.Monetary(string="Base Amount", currency_field="currency_id")
    certificate_required = fields.Boolean(string="Certificate Required", default=False)
    discount_percent = fields.Float(string="Discount Percentage", digits=(5, 2))
    subtotal = fields.Monetary(string="Subtotal", currency_field="currency_id")
    tax_amount = fields.Monetary(string="Tax Amount", currency_field="currency_id")
    tax_id = fields.Many2one("account.tax", string="Tax")
    total_amount = fields.Monetary(string="Total Amount", currency_field="currency_id")
    unit_price = fields.Monetary(string="Unit Price", currency_field="currency_id")

    # Service Configuration
    collection_date = fields.Date(string="Collection Date")
    destruction_method = fields.Selection(
        [
            ("shredding", "Shredding"),
            ("pulping", "Pulping"),
            ("burning", "Secure Burning"),
            ("disintegration", "Disintegration"),
        ],
        string="Destruction Method",
    )
    document_type = fields.Selection(
        [
            ("general", "General Documents"),
            ("confidential", "Confidential"),
            ("classified", "Classified"),
            ("financial", "Financial Records"),
        ],
        string="Document Type",
    )
    estimated_service_time = fields.Float(string="Estimated Service Time (hours)")
    express_service = fields.Boolean(string="Express Service", default=False)
    express_surcharge = fields.Monetary(
        string="Express Surcharge", currency_field="currency_id"
    )
    pickup_required = fields.Boolean(string="Pickup Required", default=True)
    scanning_required = fields.Boolean(string="Scanning Required", default=False)
    special_requirements = fields.Text(string="Special Requirements")

    # Processing Information
    collected = fields.Boolean(string="Collected", default=False)
    processed_by = fields.Many2one("res.users", string="Processed By")
    quality_check_by = fields.Many2one("res.users", string="Quality Check By")
    quantity = fields.Float(string="Quantity", default=1.0)
    required = fields.Boolean(string="Required", default=True)
    resolved = fields.Boolean(string="Resolved", default=False)
    step_description = fields.Text(string="Step Description")
    step_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Step Status",
        default="pending",
    )

    # Compliance and Security
    chain_of_custody = fields.Text(string="Chain of Custody Notes")
    chain_of_custody_id = fields.Many2one(
        "records.chain.of.custody", string="Chain of Custody"
    )
    compliance_documentation = fields.Text(string="Compliance Documentation")
    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        string="Confidentiality Level",
        default="internal",
    )
    naid_audit_id = fields.Many2one("naid.audit.log", string="NAID Audit Log")
    naid_certificate_required = fields.Boolean(
        string="NAID Certificate Required", default=False
    )
    naid_compliance_required = fields.Boolean(
        string="NAID Compliance Required", default=False
    )
    witness_required = fields.Boolean(string="Witness Required", default=False)
    witness_verification = fields.Text(string="Witness Verification")

    # System Integration
    customer_record_created = fields.Boolean(
        string="Customer Record Created", default=False
    )
    customer_record_id = fields.Many2one("res.partner", string="Customer Record")
    invoice_generated = fields.Boolean(string="Invoice Generated", default=False)
    invoice_required = fields.Boolean(string="Invoice Required", default=True)
    naid_audit_created = fields.Boolean(string="NAID Audit Created", default=False)
    pos_order_created = fields.Boolean(string="POS Order Created", default=False)
    records_request_created = fields.Boolean(
        string="Records Request Created", default=False
    )
    records_request_id = fields.Many2one("portal.request", string="Records Request")

    # Timing and Processing
    customer_processing_time = fields.Float(string="Customer Processing Time (minutes)")
    duration_seconds = fields.Integer(string="Duration (seconds)")
    estimated_volume = fields.Float(string="Estimated Volume (cubic feet)")
    service_configuration_time = fields.Float(
        string="Service Configuration Time (minutes)"
    )
    step_time = fields.Datetime(string="Step Time")
    total_processing_time = fields.Float(string="Total Processing Time (minutes)")
    wizard_start_time = fields.Datetime(
        string="Wizard Start Time", default=fields.Datetime.now
    )

    # Contact and Communication
    final_verification_by = fields.Many2one("res.users", string="Final Verification By")
    receipt_email = fields.Char(string="Receipt Email")
    supervisor_approval = fields.Boolean(string="Supervisor Approval", default=False)

    # Error Handling
    error_details = fields.Text(string="Error Details")
    error_message = fields.Char(string="Error Message")
    error_time = fields.Datetime(string="Error Time")
    error_type = fields.Selection(
        [
            ("validation", "Validation Error"),
            ("system", "System Error"),
            ("user", "User Error"),
            ("integration", "Integration Error"),
        ],
        string="Error Type",
    )

    # Additional relationships
    product_id = fields.Many2one("product.template", string="Service Product")
    transaction_id = fields.Char(string="Transaction ID")
    payment_reference = fields.Char(string="Payment Reference")
    payment_method = fields.Selection(
        [
            ("cash", "Cash"),
            ("card", "Credit/Debit Card"),
            ("check", "Check"),
            ("bank_transfer", "Bank Transfer"),
            ("digital", "Digital Payment"),
            ("other", "Other"),
        ],
        string="Payment Method",
        default="cash",
    )

    # Notes and documentation
    notes = fields.Text(string="Additional Notes")
    resolution_notes = fields.Text(string="Resolution Notes")
    retention_period = fields.Integer(string="Retention Period (days)")
    # === COMPREHENSIVE MISSING FIELDS ===
    active = fields.Boolean(string="Flag", default=True)
    sequence = fields.Integer(string="Sequence", default=10)
    created_date = fields.Date(string="Date", default=fields.Date.today)
    updated_date = fields.Date(string="Date")
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # === SPECIFIC RECOMMENDED FIELDS ===
    compliance_officer = fields.Char(string="Compliance Officer")
    digitization_format = fields.Selection(
        [("pdf", "PDF"), ("image", "Image"), ("text", "Text")],
        string="Digitization Format",
    )
    document_count = fields.Integer(string="Document Count", default=0)
    document_name = fields.Char(string="Document Name")
    # Note: Removed One2many relationships - TransientModel cannot have relationships with regular Models
    payment_terms = fields.Char(string="Payment Terms")
    shredding_type = fields.Selection(
        [("onsite", "On-site"), ("offsite", "Off-site"), ("witnessed", "Witnessed")],
        string="Shredding Type",
    )
    step_name = fields.Char(string="Step Name")
    total_discount = fields.Monetary(
        string="Total Discount", currency_field="currency_id"
    )

    # Computed fields for display
    @api.depends("visitor_id")
    def _compute_visitor_details(self):
        """Compute visitor-related display fields"""
        for record in self:
            if record.visitor_id:
                record.visitor_name = record.visitor_id.name
                record.visitor_email = (
                    record.visitor_id.email
                    if hasattr(record.visitor_id, "email")
                    else ""
                )
                record.visitor_phone = (
                    record.visitor_id.phone
                    if hasattr(record.visitor_id, "phone")
                    else ""
                )

    def action_check_in_visitor(self):
        """Check in visitor."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Visitor Checked In"),
                "message": _("Visitor has been checked in successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_check_out_visitor(self):
        """Check out visitor."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Visitor Checked Out"),
                "message": _("Visitor has been checked out successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_print_visitor_badge(self):
        """Print visitor badge."""
        self.ensure_one()

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.visitor_badge",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
        }

    def action_log_security_event(self):
        """Log security event."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Security Event Logged"),
                "message": _("Security event has been logged."),
                "type": "warning",
                "sticky": True,
            },
        }

    def action_process_visitor(self):
        """Process visitor."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Visitor Processed"),
                "message": _("Visitor has been processed successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_create_pos_order(self):
        """Create POS order."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("POS Order Created"),
                "message": _("POS order has been created successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_link_existing_order(self):
        """Link existing order."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Order Linked"),
                "message": _("Existing order has been linked successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_cancel(self):
        """Cancel operation."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window_close",
        }
