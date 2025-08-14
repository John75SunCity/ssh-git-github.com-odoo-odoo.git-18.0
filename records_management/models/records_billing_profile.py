# -*- coding: utf-8 -*-
"""
Records Billing Profile Management Module

This module provides comprehensive billing profile management for the Records Management
System. It serves as the central configuration point for customer billing preferences,
payment terms, and contact management.

Key Features:
- Customer billing configuration and preferences
- Payment terms and billing frequency management
- Integration with billing contacts and services
- Automated billing rule application
- Credit limit and payment history tracking

Business Processes:
1. Profile Creation: Setting up billing profiles for customers
2. Contact Management: Managing billing contacts per profile
3. Payment Terms: Configuring payment schedules and terms
4. Service Association: Linking profiles to billing services
5. Credit Management: Monitoring credit limits and payment history

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsBillingProfile(models.Model):
    _name = "records.billing.profile"
    _description = "Records Billing Profile"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name, partner_id"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Profile Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the billing profile",
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
        help="User responsible for this billing profile",
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether this billing profile is active",
    )

    # ============================================================================
    # CUSTOMER RELATIONSHIP
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        ondelete="cascade",
        help="Customer associated with this billing profile",
    )

    # ============================================================================
    # BILLING CONFIGURATION
    # ============================================================================
    billing_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
            ("on_demand", "On Demand"),
        ],
        string="Billing Frequency",
        default="monthly",
        tracking=True,
        help="How often to generate bills for this profile",
    )

    payment_term_id = fields.Many2one(
        "account.payment.term",
        string="Payment Terms",
        help="Payment terms for this billing profile",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        store=True,
        help="Currency for billing",
    )

    # ============================================================================
    # CONTACT RELATIONSHIPS
    # ============================================================================
    billing_contact_ids = fields.One2many(
        "records.billing.contact",
        "billing_profile_id",
        string="Billing Contacts",
        help="Contacts associated with this billing profile",
    )

    primary_contact_id = fields.Many2one(
        "records.billing.contact",
        string="Primary Contact",
        compute="_compute_primary_contact",
        store=True,
        help="Primary billing contact for this profile",
    )

    # ============================================================================
    # SERVICE RELATIONSHIPS
    # ============================================================================
    billing_service_ids = fields.Many2many(
        "records.billing.service",
        "billing_profile_service_rel",
        "profile_id",
        "service_id",
        string="Associated Services",
        help="Billing services associated with this profile",
    )

    # ============================================================================
    # CREDIT AND LIMITS
    # ============================================================================
    credit_limit = fields.Monetary(
        string="Credit Limit",
        currency_field="currency_id",
        default=0.0,
        help="Credit limit for this customer",
    )

    current_balance = fields.Monetary(
        string="Current Balance",
        currency_field="currency_id",
        compute="_compute_current_balance",
        store=True,
        help="Current outstanding balance",
    )

    # ============================================================================
    # BILLING PREFERENCES
    # ============================================================================
    auto_billing = fields.Boolean(
        string="Auto Billing",
        default=True,
        help="Automatically generate bills based on billing frequency",
    )

    consolidate_invoices = fields.Boolean(
        string="Consolidate Invoices",
        default=False,
        help="Consolidate multiple services into single invoice",
    )

    send_reminders = fields.Boolean(
        string="Send Payment Reminders",
        default=True,
        help="Send automated payment reminder emails",
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
    @api.depends("billing_contact_ids", "billing_contact_ids.primary_contact")
    def _compute_primary_contact(self):
        """Compute primary contact for this billing profile"""
        for record in self:
            primary_contact = record.billing_contact_ids.filtered(
                lambda c: c.primary_contact and c.active
            )
            record.primary_contact_id = (
                primary_contact[0] if primary_contact else False
            )

    @api.depends("partner_id")
    def _compute_current_balance(self):
        """Compute current outstanding balance"""
        for record in self:
            # This would integrate with account.move to calculate balance
            record.current_balance = 0.0

    @api.depends("billing_contact_ids")
    def _compute_contact_count(self):
        """Compute number of billing contacts"""
        for record in self:
            record.contact_count = len(record.billing_contact_ids)

    contact_count = fields.Integer(
        string="Contact Count",
        compute="_compute_contact_count",
        store=True,
        help="Number of billing contacts",
    )

    @api.depends("billing_service_ids")
    def _compute_service_count(self):
        """Compute number of associated services"""
        for record in self:
            record.service_count = len(record.billing_service_ids)

    service_count = fields.Integer(

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
        string="Service Count",
        compute="_compute_service_count",
        store=True,
        help="Number of associated billing services",
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_contacts(self):
        """View billing contacts for this profile"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Billing Contacts: %s", self.name),
            "res_model": "records.billing.contact",
            "view_mode": "tree,form",
            "domain": [("billing_profile_id", "=", self.id)],
            "context": {
                "default_billing_profile_id": self.id,
                "default_partner_id": self.partner_id.id,
            },
        }

    def action_view_services(self):
        """View associated billing services"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Billing Services: %s", self.name),
            "res_model": "records.billing.service",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.billing_service_ids.ids)],
            "context": {
                "default_profile_id": self.id,
            },
        }

    def action_create_contact(self):
        """Create new billing contact for this profile"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("New Billing Contact"),
            "res_model": "records.billing.contact",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_billing_profile_id": self.id,
                "default_partner_id": self.partner_id.id,
                "default_name": f"{self.partner_id.name} Contact",
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("credit_limit")
    def _check_credit_limit(self):
        """Validate credit limit is not negative"""
        for record in self:
            if record.credit_limit < 0:
                raise ValidationError(_("Credit limit cannot be negative"))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display with partner name"""
        result = []
        for record in self:
            name = f"{record.name} ({record.partner_id.name})"
            result.append((record.id, name))
        return result

    @api.model
    def get_profile_for_partner(self, partner_id):
        """Get billing profile for a specific partner"""
        return self.search(
            [("partner_id", "=", partner_id), ("active", "=", True)], limit=1
        )
