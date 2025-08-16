# -*- coding: utf-8 -*-
"""
Records Billing Contact Management Module

This module provides comprehensive billing contact management for the Records Management
System. It enables customers to designate multiple billing contacts with different
communication preferences and hierarchical roles for streamlined invoice management.

Key Features:
- Multi-contact billing management with primary/backup designation
- Flexible communication preferences for different invoice types
- Integration with billing profiles for comprehensive customer management
- Communication method preferences (email, phone, mail, portal)
- Hierarchical contact management with sequence-based ordering
- Real-time contact validation and notification testing

Business Processes:
1. Contact Registration: Adding billing contacts to customer billing profiles
2. Primary Contact Management: Designating and managing primary billing contacts
3. Communication Preference Setup: Configuring invoice delivery preferences
4. Contact Hierarchy Management: Organizing contacts by priority and role
5. Invoice Distribution: Routing invoices to appropriate contacts based on preferences
6. Contact Verification: Testing and validating contact information

Contact Types:
- Primary Contact: Main billing contact for all invoice types
- Backup Contact: Secondary contact for redundancy and coverage
- Service Contacts: Specialized contacts for specific service types
- Financial Contacts: Contacts focused on payment and accounting matters

Communication Management:
- Storage Invoice Routing: Dedicated contacts for storage billing
- Service Invoice Routing: Specialized contacts for service charges
- Statement Distribution: Account statement delivery management
- Overdue Notice Handling: Delinquency notice routing and escalation
- Multi-channel Communication: Email, phone, mail, and portal integration

Technical Implementation:
- Modern Odoo 18.0 architecture with mail thread integration
- Comprehensive field validation and business rule enforcement
- Integration with billing profile management and customer portal
- Communication preference tracking and automated routing
- Contact hierarchy management with validation constraints

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import re
import pytz

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsBillingContact(models.Model):
    _name = "records.billing.contact"
    _description = "Records Billing Contact"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Contact Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the billing contact",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this contact",
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether this contact is active"
    )

    sequence = fields.Integer(
        string="Sequence", default=10, help="Order of contact in listings"
    )

    # ============================================================================
    # CONTACT INFORMATION
    # ============================================================================
    email = fields.Char(
        string="Email",
        required=True,
        tracking=True,
        help="Primary email address for billing communications",
    )

    phone = fields.Char(string="Phone", tracking=True, help="Primary phone number")
    mobile = fields.Char(string="Mobile", tracking=True, help="Mobile phone number")
    job_title = fields.Char(string="Job Title", help="Job title or position")
    department = fields.Char(string="Department", help="Department or division")

    # ============================================================================
    # BILLING PROFILE RELATIONSHIP
    # ============================================================================
    billing_profile_id = fields.Many2one(
        "records.billing.profile",
        string="Billing Profile",
        required=True,
        tracking=True,
        ondelete="cascade",
        help="Associated billing profile",
    )

    customer_billing_profile_id = fields.Many2one(
        "records.customer.billing.profile",
        string="Customer Billing Profile",
        tracking=True,
        ondelete="cascade",
        help="Associated customer billing profile from records_customer_billing_profile",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="billing_profile_id.partner_id",
        store=True,
        help="Customer associated with this contact",
    )

    # ============================================================================
    # BILLING SERVICE RELATIONSHIPS
    # ============================================================================
    billing_service_ids = fields.Many2many(
        "records.billing.service",
        "billing_contact_service_rel",
        "contact_id",
        "service_id",
        string="Associated Billing Services",
        help="Billing services this contact should receive invoices for",
    )

    # ============================================================================
    # COMMUNICATION PREFERENCES
    # ============================================================================
    receive_storage_invoices = fields.Boolean(
        string="Receive Storage Invoices",
        default=True,
        help="Contact will receive storage billing invoices",
    )

    receive_service_invoices = fields.Boolean(
        string="Receive Service Invoices",
        default=True,
        help="Contact will receive service billing invoices",
    )

    receive_statements = fields.Boolean(
        string="Receive Statements",
        default=True,
        help="Contact will receive account statements",
    )

    receive_overdue_notices = fields.Boolean(
        string="Receive Overdue Notices",
        default=True,
        help="Contact will receive overdue payment notices",
    )

    receive_promotional = fields.Boolean(
        string="Receive Promotional Materials",
        default=False,
        help="Contact will receive promotional communications",
    )

    receive_service_updates = fields.Boolean(
        string="Receive Service Updates",
        default=True,
        help="Contact will receive service notifications and updates",
    )

    # ============================================================================
    # CONTACT HIERARCHY
    # ============================================================================
    primary_contact = fields.Boolean(
        string="Primary Contact",
        default=False,
        help="This is the primary billing contact",
    )

    backup_contact = fields.Boolean(
        string="Backup Contact", default=False, help="This is a backup billing contact"
    )

    contact_type = fields.Selection(
        [
            ("primary", "Primary Billing Contact"),
            ("backup", "Backup Billing Contact"),
            ("financial", "Financial Contact"),
            ("service", "Service Contact"),
            ("technical", "Technical Contact"),
            ("executive", "Executive Contact"),
        ],
        string="Contact Type",
        default="primary",
        help="Type of billing contact",
    )

    # ============================================================================
    # COMMUNICATION METHOD
    # ============================================================================
    preferred_method = fields.Selection(
        [
            ("email", "Email"),
            ("phone", "Phone"),
            ("mail", "Postal Mail"),
            ("portal", "Customer Portal"),
            ("fax", "Fax"),
        ],
        string="Preferred Communication Method",
        default="email",
        help="Preferred method for billing communications",
    )

    secondary_method = fields.Selection(
        [
            ("email", "Email"),
            ("phone", "Phone"),
            ("mail", "Postal Mail"),
            ("portal", "Customer Portal"),
            ("fax", "Fax"),
        ],
        string="Secondary Communication Method",
        help="Secondary method for billing communications",
    )

    # ============================================================================
    # DELIVERY PREFERENCES
    # ============================================================================
    email_format = fields.Selection(
        [
            ("pdf", "PDF Attachment"),
            ("html", "HTML Email"),
            ("both", "Both PDF and HTML"),
        ],
        string="Email Format",
        default="pdf",
        help="Preferred email format for invoices",
    )

    delivery_schedule = fields.Selection(
        [
            ("immediate", "Immediate"),
            ("daily", "Daily Summary"),
            ("weekly", "Weekly Summary"),
            ("monthly", "Monthly Summary"),
        ],
        string="Delivery Schedule",
        default="immediate",
        help="Schedule for invoice delivery",
    )

    invoice_delivery_method = fields.Selection(
        [
            ("email", "Email"),
            ("mail", "Postal Mail"),
            ("portal", "Customer Portal"),
            ("fax", "Fax"),
        ],
        string="Invoice Delivery Method",
        default="email",
        help="Method for delivering invoices to this contact",
    )

    invoice_format = fields.Selection(
        [
            ("pdf", "PDF"),
            ("html", "HTML"),
            ("both", "Both"),
        ],
        string="Invoice Format",
        default="pdf",
        help="Format for invoice delivery",
    )

    consolidated_invoicing = fields.Boolean(
        string="Consolidated Invoicing",
        default=False,
        help="Consolidate multiple invoices into single delivery",
    )

    # ============================================================================
    # COMMUNICATION NOTIFICATION SETTINGS
    # ============================================================================
    email_notifications = fields.Boolean(
        string="Email Notifications",
        default=True,
        help="Receive email notifications for billing events",
    )

    notification_frequency = fields.Selection(
        [
            ("immediate", "Immediate"),
            ("hourly", "Hourly"),
            ("daily", "Daily"),
            ("weekly", "Weekly"),
        ],
        string="Notification Frequency",
        default="immediate",
        help="Frequency of notification delivery",
    )

    sms_notifications = fields.Boolean(
        string="SMS Notifications",
        default=False,
        help="Receive SMS notifications for urgent billing matters",
    )

    urgent_notifications_only = fields.Boolean(
        string="Urgent Notifications Only",
        default=False,
        help="Only receive notifications for urgent matters",
    )

    # ============================================================================
    # CONTACT DETAILS
    # ============================================================================
    language = fields.Selection(
        selection="_get_languages",
        string="Language",
        default="en_US",
        help="Preferred language for communications",
    )

    timezone = fields.Selection(
        selection="_get_timezones",
        string="Timezone",
        help="Contact's timezone for scheduling",
    )

    notes = fields.Text(string="Notes", help="Internal notes about this contact")

    # ============================================================================
    # ACTIVITY TRACKING
    # ============================================================================
    last_contact_date = fields.Datetime(
        string="Last Contact Date", help="Date of last communication with this contact"
    )

    last_invoice_sent = fields.Datetime(
        string="Last Invoice Sent",
        help="Date when last invoice was sent to this contact",
    )

    communication_count = fields.Integer(
        string="Communication Count",
        default=0,
        help="Number of communications sent to this contact",
    )

    # ============================================================================
    # CURRENCY FIELDS
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        store=True,
        help="Company currency for billing",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(compute="_compute_display_name", store=True)

    @api.depends("name", "job_title", "department")
    def _compute_display_name(self):
        """Compute display name with additional details"""
        for record in self:
            name_parts = [record.name]
            if record.job_title:
                name_parts.append(f"({record.job_title})")
            if record.department:
                name_parts.append(f"- {record.department}")
            record.display_name = " ".join(name_parts)

    @api.depends(
        "receive_storage_invoices", "receive_service_invoices", "receive_statements"
    )
    def _compute_invoice_types(self):
        """Compute which invoice types this contact receives"""
        for record in self:
            types = []
            if record.receive_storage_invoices:
                types.append("Storage")
            if record.receive_service_invoices:
                types.append("Service")
            if record.receive_statements:
                types.append("Statements")
            record.invoice_types = ", ".join(types) if types else "None"

    invoice_types = fields.Char(
        string="Invoice Types",
        compute="_compute_invoice_types",
        store=True,
        help="Types of invoices this contact receives",
    )

    @api.depends("primary_contact", "backup_contact", "contact_type")
    def _compute_contact_priority(self):
        """Compute contact priority for sorting and display"""
        for record in self:
            if record.primary_contact or record.contact_type == "primary":
                record.contact_priority = 1
            elif record.backup_contact or record.contact_type == "backup":
                record.contact_priority = 2
            elif record.contact_type == "executive":
                record.contact_priority = 3
            elif record.contact_type == "financial":
                record.contact_priority = 4
            else:
                record.contact_priority = 5

    contact_priority = fields.Integer(
        string="Contact Priority",
        compute="_compute_contact_priority",
        store=True,
        help="Priority level for contact sorting",
    )

    @api.depends("billing_service_ids")
    def _compute_service_count(self):
        """Compute number of associated billing services"""
        for record in self:
            record.service_count = len(record.billing_service_ids)

    service_count = fields.Integer(
        string="Service Count",
        compute="_compute_service_count",
        store=True,
        help="Number of associated billing services",
    )

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
    help='Current status of the record')

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle primary contact logic"""
        for vals in vals_list:
            # If creating primary contact, ensure only one primary per profile
            if vals.get("primary_contact") and vals.get("billing_profile_id"):
                self._ensure_single_primary(vals["billing_profile_id"])

        return super().create(vals_list)

    def write(self, vals):
        """Override write to handle primary contact changes"""
        if "primary_contact" in vals and vals["primary_contact"]:
            for record in self:
                self._ensure_single_primary(record.billing_profile_id.id, record.id)  # pylint: disable=no-member

        return super().write(vals)

    service_type = fields.Selection([("primary", "Primary"), ("billing", "Billing"), ("technical", "Technical"), ("emergency", "Emergency")], string="Contact Type")
    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _ensure_single_primary(self, billing_profile_id, exclude_id=None):
        """Ensure only one primary contact per billing profile"""
        domain = [
            ("billing_profile_id", "=", billing_profile_id),
            ("primary_contact", "=", True),
        ]
        if exclude_id:
            domain.append(("id", "!=", exclude_id))

        existing_primary = self.search(domain)
        if existing_primary:
            # pylint: disable=no-member
            existing_primary.write({"primary_contact": False})

    def _get_languages(self):
        """Get available languages"""
        return self.env["res.lang"].get_installed()

    def _get_timezones(self):
        """Get available timezones"""
        return [(tz, tz) for tz in pytz.all_timezones]

    def send_test_communication(self):
        """Send test communication to verify contact information"""
        self.ensure_one()

        if not self.email and self.preferred_method == "email":
            raise ValidationError(
                _("No email address specified for email communication.")
            )

        # Update activity tracking
        # pylint: disable=no-member
        self.write(
            {
                "last_contact_date": fields.Datetime.now(),
                "communication_count": self.communication_count + 1,
            }
        )

        # Log the test communication
        self.message_post(
            body=_(
                "Test communication sent to %s via %s",
                self.name,
                dict(self._fields["preferred_method"].selection)[self.preferred_method],
            )
        )

        return True

    def update_invoice_delivery_tracking(self):
        """Update tracking when invoice is delivered to this contact"""
        self.ensure_one()

        # pylint: disable=no-member
        self.write(
            {
                "last_invoice_sent": fields.Datetime.now(),
                "communication_count": self.communication_count + 1,
            }
        )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_set_primary(self):
        """Set this contact as primary"""
        self.ensure_one()

        # Remove primary flag from other contacts in same profile
        # pylint: disable=no-member
        other_contacts = self.search(
            [
                ("billing_profile_id", "=", self.billing_profile_id.id),
                ("id", "!=", self.id),
            ]
        )

        # pylint: disable=no-member
        other_contacts.write({"primary_contact": False})

        # Set this contact as primary
        # pylint: disable=no-member
        self.write(
            {
                "primary_contact": True,
                "contact_type": "primary",
            }
        )

        self.message_post(body=_("Contact set as primary billing contact"))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Primary Contact Updated"),
                "message": _("%s is now the primary billing contact.", self.name),
                "type": "success",
            },
        }

    def action_test_email(self):
        """Send test email to verify contact information"""
        self.ensure_one()

        if not self.email:
            raise ValidationError(_("No email address specified for this contact."))

        # Send test communication
        self.send_test_communication()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Test Email Sent"),
                "message": _("Test email sent to %s", self.email),
                "type": "success",
            },
        }

    def action_view_communications(self):
        """View all communications sent to this contact"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Communications: %s", self.name),
            "res_model": "mail.message",
            "view_mode": "tree,form",
            "domain": [
                ("model", "=", self._name),
                ("res_id", "=", self.id),
            ],
            "context": {"default_model": self._name, "default_res_id": self.id},
        }

    def action_view_billing_services(self):
        """View associated billing services"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Billing Services: %s", self.name),
            "res_model": "records.billing.service",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.billing_service_ids.ids)],  # pylint: disable=no-member
            "context": {
                "default_contact_id": self.id,
                "search_default_group_by_service_type": 1,
            },
        }

    def action_update_preferences(self):
        """Open wizard to update communication preferences"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Update Communication Preferences"),
            "res_model": "records.billing.contact",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_id": self.id,
                "focus_preferences": True,
            },
        }

    def action_deactivate_contact(self):
        """Deactivate billing contact"""
        self.ensure_one()

        # If this is a primary contact, promote backup contact
        if self.primary_contact:
            # pylint: disable=no-member
            backup_contacts = self.search(
                [
                    ("billing_profile_id", "=", self.billing_profile_id.id),
                    ("backup_contact", "=", True),
                    ("active", "=", True),
                    ("id", "!=", self.id),
                ],
                limit=1,
            )

            if backup_contacts:
                # pylint: disable=no-member
                backup_contacts.write(
                    {
                        "primary_contact": True,
                        "backup_contact": False,
                        "contact_type": "primary",
                    }
                )

                self.message_post(
                    body=_("Primary contact role transferred to %s", backup_contacts[0].name)
                )

        # pylint: disable=no-member
        self.write({"active": False})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Contact Deactivated"),
                "message": _("Billing contact has been deactivated"),
                "type": "warning",
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("primary_contact", "billing_profile_id")
    def _check_primary_contact_unique(self):
        """Ensure only one primary contact per billing profile"""
        for record in self:
            if record.primary_contact:
                # pylint: disable=no-member
                existing = self.search(
                    [
                        ("billing_profile_id", "=", record.billing_profile_id.id),
                        ("primary_contact", "=", True),
                        ("id", "!=", record.id),  # pylint: disable=no-member
                    ]
                )

                if existing:
                    raise ValidationError(
                        _(
                            "Only one primary contact is allowed per billing profile. "
                            "Please uncheck the primary contact flag for %s first.",
                            existing[0].name,
                        )
                    )

    @api.constrains("email")
    def _check_email_format(self):
        """Validate email format using regex pattern"""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        for record in self:
            if record.email:
                if not re.match(email_pattern, record.email):
                    raise ValidationError(_("Invalid email format: %s", record.email))

    @api.constrains("preferred_method", "email", "phone")
    def _check_communication_method(self):
        """Validate communication method requirements"""
        for record in self:
            if record.preferred_method == "email" and not record.email:
                raise ValidationError(
                    _(
                        "Email address is required when email is the preferred communication method"
                    )
                )

            if record.preferred_method == "phone" and not (
                record.phone or record.mobile
            ):
                raise ValidationError(
                    _(
                        "Phone number is required when phone is the preferred communication method"
                    )
                )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name_parts = [record.name]

            if record.primary_contact:
                name_parts.append("(Primary)")
            elif record.backup_contact:
                name_parts.append("(Backup)")

            if record.job_title:
                name_parts.append(f"- {record.job_title}")

            result.append((record.id, " ".join(name_parts)))  # pylint: disable=no-member

        return result

    @api.model
    def _search_name(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Enhanced search by name, email, or job title"""
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                "|",
                ("name", operator, name),
                ("email", operator, name),
                ("job_title", operator, name),
                ("department", operator, name),
            ]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def get_primary_contact(self, billing_profile_id):
        """Get primary contact for billing profile"""
        # pylint: disable=no-member
        return self.search(
            [
                ("billing_profile_id", "=", billing_profile_id),
                ("primary_contact", "=", True),
                ("active", "=", True),
            ],
            limit=1,
        )

    @api.model
    def get_contacts_for_invoice_type(self, billing_profile_id, invoice_type="storage"):
        """Get contacts that should receive specific invoice type"""
        domain = [
            ("billing_profile_id", "=", billing_profile_id),
            ("active", "=", True),
        ]

        if invoice_type == "storage":
            domain.append(("receive_storage_invoices", "=", True))
        elif invoice_type == "service":
            domain.append(("receive_service_invoices", "=", True))
        elif invoice_type == "statement":
            domain.append(("receive_statements", "=", True))
        elif invoice_type == "overdue":
            domain.append(("receive_overdue_notices", "=", True))

        return self.search(domain, order="contact_priority, sequence, name")

    @api.model
    def get_contacts_for_service(self, service_id):
        """Get contacts associated with specific billing service"""
        # pylint: disable=no-member
        return self.search(
            [
                ("billing_service_ids", "in", [service_id]),
                ("active", "=", True),
            ],
            order="contact_priority, sequence, name",
        )