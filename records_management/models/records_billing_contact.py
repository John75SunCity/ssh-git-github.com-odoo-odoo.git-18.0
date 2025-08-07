# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsBillingContact(models.Model):
    _name = "records.billing.contact"
    _description = "Records Billing Contact"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Contact Name", required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string="Sequence", default=10)

    # ============================================================================
    # CONTACT INFORMATION
    # ============================================================================
    email = fields.Char(string="Email", required=True, tracking=True)
    phone = fields.Char(string="Phone", tracking=True)
    mobile = fields.Char(string="Mobile", tracking=True)

    # ============================================================================
    # BILLING PROFILE RELATIONSHIP
    # ============================================================================
    billing_profile_id = fields.Many2one(
        "records.customer.billing.profile",
        string="Billing Profile",
        required=True,
        tracking=True,
        ondelete="cascade",
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

    # ============================================================================
    # COMMUNICATION METHOD
    # ============================================================================
    preferred_method = fields.Selection(
        [
            ("email", "Email"),
            ("phone", "Phone"),
            ("mail", "Postal Mail"),
            ("portal", "Customer Portal"),
        ],
        string="Preferred Communication Method",
        default="email",
    )

    # ============================================================================
    # NOTES
    # ============================================================================
    notes = fields.Text(string="Notes")

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================        "mail.followers", "res_id", string="Followers"
    )    @api.constrains("primary_contact", "billing_profile_id")
    def _check_primary_contact_unique(self):
        """Ensure only one primary contact per billing profile"""
        for record in self:
            if record.primary_contact:
                existing = self.search(
                    [
                        ("billing_profile_id", "=", record.billing_profile_id.id),
                        ("primary_contact", "=", True),
                        ("id", "!=", record.id),
                    ]
                )
                if existing:
                    raise ValidationError(
                        _(
                            "Only one primary contact is allowed per billing profile. "
                            "Please uncheck the primary contact flag for %s first."
                        )
                        % existing[0].name
                    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_set_primary(self):
        """Set this contact as primary"""
        # Remove primary flag from other contacts in same profile
        other_contacts = self.search(
            [
                ("billing_profile_id", "=", self.billing_profile_id.id),
                ("id", "!=", self.id),
            ]
        )
        other_contacts.write({"primary_contact": False})

        # Set this contact as primary
        self.write({"primary_contact": True})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Primary Contact Updated"),
                "message": _("%s is now the primary billing contact.") % self.name,
                "type": "success",
            },
        }

    def action_test_email(self):
        """Send test email to verify contact information"""
        if not self.email:
            raise ValidationError(_("No email address specified for this contact."))

        # Here you would implement actual email sending
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Test Email"),
                "message": _("Test email would be sent to %s") % self.email,
                "type": "info",
            },
        }
