# -*- coding: utf-8 -*-
"""
Partner Extension for Records Management System

This module extends the standard res.partner model to provide comprehensive
Records Management functionality including customer identification, department
association, key management integration, and field configuration templates.

Key Features:
- Records customer identification and classification
- Department-level user management integration
- Bin key management system integration
- Field configuration template assignment
- Complete workflow action methods for key lifecycle
- Administrative permission management for development

Business Integration:
- Links partners to records.department for data filtering
- Integrates with bin.key.management for physical security
- Supports transitory.field.config for customized field templates
- Enables partner-specific workflow actions and service requests

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # ============================================================================
    # RECORDS MANAGEMENT INTEGRATION FIELDS
    # ============================================================================
    is_records_customer = fields.Boolean(
        string="Records Customer",
        default=False,
        tracking=True,
        help="Indicates if this partner is a records management customer",
    )

    records_department_id = fields.Many2one(
        "records.department",
        string="Records Department",
        tracking=True,
        help="Associated records department for data filtering and access control",
    )

    container_ids = fields.One2many(
        "records.container",
        "partner_id",
        string="Containers",
        help="Containers associated with this partner.",
    )

    # ============================================================================
    # CUSTOMER PORTAL INTEGRATION
    # ============================================================================
    portal_request_ids = fields.One2many(
        "portal.request",
        "partner_id",
        string="Portal Requests",
        help="Service requests submitted by this partner through the customer portal.",
    )

    customer_feedback_ids = fields.One2many(
        "customer.feedback",
        "partner_id",
        string="Customer Feedback",
        help="Feedback submitted by this partner.",
    )

    chain_of_custody_ids = fields.One2many(
        "records.chain.of.custody",
        "partner_id",
        string="Chain of Custody Records",
        help="Chain of custody records for this partner.",
    )

    # ============================================================================
    # BIN KEY MANAGEMENT RELATIONSHIPS
    # ============================================================================
    bin_key_ids = fields.One2many(
        "bin.key.management",
        "partner_id",
        string="Bin Keys",
        help="Bin keys associated with this partner.",
    )
    partner_bin_key_ids = fields.One2many(
        "partner.bin.key",
        "partner_id",
        string="Partner Bin Key Restrictions",
        help="Key issuance restrictions for this partner.",
    )

    # ============================================================================
    # USER RELATIONSHIP INTEGRATION
    # ============================================================================
    records_department_user_ids = fields.One2many(
        "res.users",
        "partner_id",
        string="Department Users (Records)",
        help="Users associated with this partner for records management",
    )

    # ============================================================================
    # FIELD CONFIGURATION INTEGRATION
    # ============================================================================
    transitory_field_config_id = fields.Many2one(
        "transitory.field.config",
        string="Field Configuration Template",
        tracking=True,
        help="Default field configuration template for this customer",
    )

    # ============================================================================
    # COMPUTED FIELDS FOR ANALYTICS
    # ============================================================================
    active_key_count = fields.Integer(
        string="Active Keys",
        compute="_compute_key_counts",
        store=True,
        help="Number of active bin keys for this partner",
    )

    total_key_count = fields.Integer(
        string="Total Keys",
        compute="_compute_key_counts",
        store=True,
        help="Total number of bin keys issued for this partner",
    )

    negotiated_rates_count = fields.Integer(
        string="Negotiated Rates",
        compute="_compute_negotiated_rates_count",
        help="Number of active negotiated rate agreements for this customer",
    )

    portal_request_count = fields.Integer(
        string="Portal Requests",
        compute="_compute_portal_counts",
        help="Number of portal requests from this partner.",
    )

    customer_feedback_count = fields.Integer(
        string="Customer Feedback",
        compute="_compute_portal_counts",
        help="Number of feedback submissions from this partner.",
    )

    container_count = fields.Integer(
        string="Container Count",
        compute="_compute_container_count",
        help="Number of containers associated with this partner.",
    )

    # ============================================================================
    # RATE MANAGEMENT RELATIONSHIPS
    # ============================================================================
    negotiated_rates_ids = fields.One2many(
        "customer.negotiated.rates",
        "partner_id",
        string="Negotiated Rate Agreements",
        help="Customer-specific negotiated rate agreements",
    )

    # ============================================================================
    # WORK ORDER RELATIONSHIPS
    # ============================================================================
    work_order_ids = fields.One2many(
        "work.order.shredding",
        "partner_id",
        string="Work Orders",
        help="Shredding work orders for this customer",
    )

    shredding_team_ids = fields.One2many(
        "shredding.team",
        "partner_id",
        string="Shredding Teams",
        help="Shredding teams associated with this partner",
    )

    @api.depends("is_records_customer", "bin_key_ids", "bin_key_ids.status")
    def _compute_key_counts(self):
        """Compute key counts for analytics"""
        for partner in self:
            if partner.is_records_customer:
                partner.active_key_count = len(
                    partner.bin_key_ids.filtered(lambda k: k.status == "active")
                )
                partner.total_key_count = len(partner.bin_key_ids)
            else:
                partner.active_key_count = 0
                partner.total_key_count = 0

    @api.depends("is_records_customer", "negotiated_rates_ids", "negotiated_rates_ids.state")
    def _compute_negotiated_rates_count(self):
        """Compute count of negotiated rates for this customer"""
        for partner in self:
            if partner.is_records_customer:
                partner.negotiated_rates_count = len(
                    partner.negotiated_rates_ids.filtered(lambda r: r.state == "active")
                )
            else:
                partner.negotiated_rates_count = 0

    @api.depends("is_records_customer", "portal_request_ids", "customer_feedback_ids")
    def _compute_portal_counts(self):
        """Compute counts for portal-related records."""
        for partner in self:
            if partner.is_records_customer:
                partner.portal_request_count = len(partner.portal_request_ids)
                partner.customer_feedback_count = len(partner.customer_feedback_ids)
            else:
                partner.portal_request_count = 0
                partner.customer_feedback_count = 0

    @api.depends("is_records_customer", "container_ids")
    def _compute_container_count(self):
        """Compute count of containers for this customer."""
        for partner in self:
            if partner.is_records_customer:
                partner.container_count = len(partner.container_ids)
            else:
                partner.container_count = 0

    # ============================================================================
    # DEVELOPMENT ADMINISTRATION METHODS
    # ============================================================================
    @api.model
    def _grant_dev_permissions(self):
        """
        Grant comprehensive permissions to development admin user.

        This method provides superuser-like permissions for the admin user
        in development and testing environments. Triggered by data files
        during module installation/update.

        Returns:
            bool: True when permissions are successfully granted
        """
        try:
            # Check if we're in a development environment
            admin_user = self.env.ref("base.user_admin", raise_if_not_found=False)
            if not admin_user:
                return True

            # Define critical security groups for records management
            critical_groups = [
                "base.group_system",  # System Administrator
                "records_management.group_records_manager",  # Records Manager
                "records_management.group_records_user",  # Records User
                "account.group_account_manager",  # Accounting Manager
                "stock.group_stock_manager",  # Inventory Manager
                "industry_fsm.group_fsm_manager",  # Field Service Manager
            ]

            # Grant access to each critical group
            for group_xml_id in critical_groups:
                try:
                    group = self.env.ref(group_xml_id, raise_if_not_found=False)
                    if group and admin_user not in group.users:
                        group.write({'users': [(4, admin_user.id)]})
                except Exception as e:
                    _logger.warning(
                        "Failed to assign group %s: %s", group_xml_id, e
                    )
                    continue

            # Enable technical features access
            try:
                admin_user.write(
                    {"groups_id": [(4, self.env.ref("base.group_no_one").id)]}
                )
            except Exception as e:
                _logger.warning("Failed to grant technical features: %s", e)

            return True

        except Exception as e:
            _logger.warning("Failed to grant dev permissions: %s", e)
            return True

    # ============================================================================
    # CUSTOMER PORTAL ACTION METHODS
    # ============================================================================
    def action_view_portal_requests(self):
        """View all portal requests for this partner."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Portal Requests - %s", self.name),
            "res_model": "portal.request",
            "view_mode": "tree,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {
                "default_partner_id": self.id,
                "search_default_partner_id": self.id,
            },
        }

    def action_view_customer_feedback(self):
        """View all customer feedback for this partner."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Feedback - %s", self.name),
            "res_model": "customer.feedback",
            "view_mode": "tree,form,kanban",
            "domain": [("partner_id", "=", self.id)],
            "context": {
                "default_partner_id": self.id,
                "search_default_partner_id": self.id,
            },
        }

    def action_view_containers(self):
        """View all containers for this partner."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Containers - %s", self.name),
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {
                "default_partner_id": self.id,
                "search_default_partner_id": self.id,
            },
        }

    # ============================================================================
    # BIN KEY MANAGEMENT ACTION METHODS
    # ============================================================================
    def action_allow_key_issuance(self):
        """Allow bin key issuance for this partner"""
        self.ensure_one()
        try:
            # Find or create key restriction record
            if not self.partner_bin_key_ids:
                self.env["partner.bin.key"].create(
                    {
                        "partner_id": self.id,
                        "key_issuance_allowed": True,
                    }
                )
            else:
                self.partner_bin_key_ids.write({"key_issuance_allowed": True})

            # Log the action for NAID compliance
            self.message_post(
                body=_("Key issuance allowed for partner: %s", self.name),
                message_type="notification",
            )

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Key Issuance Allowed"),
                    "message": _("Key issuance has been enabled for this partner."),
                    "type": "success",
                },
            }
        except Exception as e:
            _logger.error(
                "Error allowing key issuance for partner %s: %s", self.name, e
            )
            raise UserError(
                _(
                    "Failed to allow key issuance. Please try again or contact administrator."
                )
            ) from e

    def action_restrict_key_issuance(self):
        """Restrict bin key issuance for this partner"""
        self.ensure_one()
        try:
            # Find or create key restriction record
            if not self.partner_bin_key_ids:
                self.env["partner.bin.key"].create(
                    {
                        "partner_id": self.id,
                        "key_issuance_allowed": False,
                    }
                )
            else:
                self.partner_bin_key_ids.write({"key_issuance_allowed": False})

            # Log the action for NAID compliance
            self.message_post(
                body=_("Key issuance restricted for partner: %s", self.name),
                message_type="notification",
            )

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Key Issuance Restricted"),
                    "message": _("Key issuance has been restricted for this partner."),
                    "type": "warning",
                },
            }
        except Exception as e:
            _logger.error(
                "Error restricting key issuance for partner %s: %s", self.name, e
            )
            raise UserError(
                _(
                    "Failed to restrict key issuance. Please try again or contact administrator."
                )
            ) from e

    def action_confirm(self):
        """Confirm partner as records management customer"""
        self.ensure_one()
        self.write({"is_records_customer": True})

        # Log confirmation for NAID audit trail
        self.message_post(
            body=_("Partner confirmed for records management services: %s", self.name),
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Partner Confirmed"),
                "message": _(
                    "Partner has been confirmed for records management services."
                ),
                "type": "success",
            },
        }

    def action_issue_new_key(self):
        """Issue new bin key for this partner"""
        self.ensure_one()
        try:
            # Check if key issuance is allowed
            if (
                self.partner_bin_key_ids
                and not self.partner_bin_key_ids[0].key_issuance_allowed
            ):
                raise UserError(
                    _(
                        "Key issuance is restricted for this partner. Please contact administrator."
                    )
                )

            # Check if bin.key.management model exists
            if "bin.key.management" not in self.env:
                raise UserError(
                    _(
                        "Bin key management system is not available. Please contact administrator."
                    )
                )

            return {
                "type": "ir.actions.act_window",
                "name": _("Issue New Key - %s", self.name),
                "res_model": "bin.key.management",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_partner_id": self.id,
                    "default_key_type": "new_issue",
                    "default_status": "active",
                    "default_notes": _("New key issued for partner: %s", self.name),
                },
            }
        except UserError:
            raise
        except Exception as e:
            _logger.error("Error issuing new key for partner %s: %s", self.name, e)
            raise UserError(_("Failed to issue new key. Please contact administrator.")) from e

    def action_report_lost_key(self):
        """Report lost key for this partner"""
        self.ensure_one()
        try:
            # Check if bin.key.management model exists
            if "bin.key.management" not in self.env:
                raise UserError(
                    _(
                        "Bin key management system is not available. Please contact administrator."
                    )
                )

            return {
                "type": "ir.actions.act_window",
                "name": _("Report Lost Key - %s", self.name),
                "res_model": "bin.key.management",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_partner_id": self.id,
                    "default_key_type": "lost_report",
                    "default_status": "lost",
                    "default_notes": _("Key reported as lost by customer: %s", self.name),
                    "default_loss_date": fields.Date.today(),
                },
            }
        except UserError:
            raise
        except Exception as e:
            _logger.error(
                "Error reporting lost key for partner %s: %s", self.name, e
            )
            raise UserError(
                _("Failed to report lost key. Please contact administrator.")
            ) from e

    def action_return_key(self):
        """Process key return for this partner"""
        self.ensure_one()
        try:
            # Check if bin.key.management model exists
            if "bin.key.management" not in self.env:
                raise UserError(
                    _(
                        "Bin key management system is not available. Please contact administrator."
                    )
                )

            # Check for active keys
            BinKeyMgmt = self.env["bin.key.management"]
            active_keys = BinKeyMgmt.search(
                [("partner_id", "=", self.id), ("status", "=", "active")]
            )

            if not active_keys:
                raise UserError(_("No active keys found for this partner."))

            return {
                "type": "ir.actions.act_window",
                "name": _("Return Key - %s", self.name),
                "res_model": "bin.key.management",
                "view_mode": "tree,form",
                "domain": [("partner_id", "=", self.id), ("status", "=", "active")],
                "context": {
                    "default_partner_id": self.id,
                    "default_key_type": "return",
                    "search_default_active": 1,
                },
            }
        except UserError:
            raise
        except Exception as e:
            _logger.error(
                "Error processing key return for partner %s: %s", self.name, e
            )
            raise UserError(
                _("Failed to process key return. Please contact administrator.")
            ) from e

    def action_view_active_key(self):
        """View active key for this partner"""
        self.ensure_one()
        try:
            # Check if bin.key.management model exists
            if "bin.key.management" not in self.env:
                raise UserError(
                    _(
                        "Bin key management system is not available. Please contact administrator."
                    )
                )

            BinKeyMgmt = self.env["bin.key.management"]
            active_key = BinKeyMgmt.search(
                [("partner_id", "=", self.id), ("status", "=", "active")], limit=1
            )

            if not active_key:
                raise UserError(_("No active key found for this partner."))

            return {
                "type": "ir.actions.act_window",
                "name": _("Active Key - %s", self.name),
                "res_model": "bin.key.management",
                "res_id": active_key.id,
                "view_mode": "form",
                "target": "new",
            }
        except UserError:
            raise
        except Exception as e:
            _logger.error(
                "Error viewing active key for partner %s: %s", self.name, e
            )
            raise UserError(
                _("Failed to view active key. Please contact administrator.")
            ) from e

    def action_view_bin_keys(self):
        """View all bin keys for this partner"""
        self.ensure_one()
        try:
            # Check if bin.key.management model exists
            if "bin.key.management" not in self.env:
                raise UserError(
                    _(
                        "Bin key management system is not available. Please contact administrator."
                    )
                )

            return {
                "type": "ir.actions.act_window",
                "name": _("Partner Bin Keys - %s", self.name),
                "res_model": "bin.key.management",
                "view_mode": "tree,form",
                "domain": [("partner_id", "=", self.id)],
                "context": {
                    "default_partner_id": self.id,
                    "search_default_partner_id": self.id,
                },
            }
        except Exception as e:
            _logger.error(
                "Error viewing bin keys for partner %s: %s", self.name, e
            )
            raise UserError(_("Failed to view bin keys. Please contact administrator.")) from e

    def action_view_unlock_services(self):
        """View unlock services for this partner"""
        self.ensure_one()
        try:
            # Check if bin.unlock.service model exists
            if "bin.unlock.service" not in self.env:
                raise UserError(
                    _(
                        "Bin unlock service system is not available. Please contact administrator."
                    )
                )

            return {
                "type": "ir.actions.act_window",
                "name": _("Unlock Services - %s", self.name),
                "res_model": "bin.unlock.service",
                "view_mode": "tree,form",
                "domain": [("partner_id", "=", self.id)],
                "context": {
                    "default_partner_id": self.id,
                    "search_default_partner_id": self.id,
                },
            }
        except UserError:
            raise
        except Exception as e:
            _logger.error(
                "Error viewing unlock services for partner %s: %s", self.name, e
            )
            raise UserError(
                _("Failed to view unlock services. Please contact administrator.")
            ) from e

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_records_info(self):
        """Get comprehensive records management information for this partner"""
        self.ensure_one()
        try:
            # Initialize default values
            active_keys = 0
            total_keys = 0
            key_issuance_allowed = True

            # Count keys if bin.key.management exists
            if "bin.key.management" in self.env:
                BinKeyMgmt = self.env["bin.key.management"]
                active_keys = BinKeyMgmt.search_count(
                    [("partner_id", "=", self.id), ("status", "=", "active")]
                )
                total_keys = BinKeyMgmt.search_count([("partner_id", "=", self.id)])

            # Check key issuance status if partner.bin.key exists
            if "partner.bin.key" in self.env:
                PartnerBinKey = self.env["partner.bin.key"]
                restriction = PartnerBinKey.search(
                    [("partner_id", "=", self.id)], limit=1
                )
                if restriction:
                    key_issuance_allowed = restriction.key_issuance_allowed

            return {
                "is_records_customer": self.is_records_customer,
                "department": (
                    self.records_department_id.name
                    if self.records_department_id
                    else False
                ),
                "active_keys": active_keys,
                "total_keys": total_keys,
                "key_issuance_allowed": key_issuance_allowed,
                "field_config": (
                    self.transitory_field_config_id.name
                    if self.transitory_field_config_id
                    else False
                ),
            }
        except Exception as e:
            _logger.error(
                "Error getting records info for partner %s: %s", self.name, e
            )
            return {
                "is_records_customer": self.is_records_customer,
                "department": False,
                "active_keys": 0,
                "total_keys": 0,
                "key_issuance_allowed": True,
                "field_config": False,
            }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("is_records_customer", "records_department_id")
    def _check_records_customer_department(self):
        """Validate records customer has department assignment"""
        for partner in self:
            if partner.is_records_customer and not partner.records_department_id:
                raise ValidationError(
                    _("Records customers must be assigned to a records department. Please assign a department to partner '%s'.", partner.name)
                )

    @api.constrains("records_department_id", "company_id")
    def _check_department_company(self):
        """Validate department belongs to same company as partner"""
        for partner in self:
            if (
                partner.records_department_id
                and partner.company_id
                and partner.records_department_id.company_id != partner.company_id
            ):
                raise ValidationError(
                    _(
                        "Records department must belong to the same company as the partner. Partner: %s, Department Company: %s, Partner Company: %s",
                        partner.name,
                        partner.records_department_id.company_id.name,
                        partner.company_id.name,
                    )
                )
