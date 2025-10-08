# -*- coding: utf-8 -*-
"""
Cross-Department Sharing Module

This module manages cross-department sharing of records and access permissions.
It provides an invitation and approval workflow for sharing access between
departments while maintaining security and audit trails.

Author: Records Management System
Version: 19.0.0.1
License: LGPL-3
"""

import json
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CrossDepartmentSharing(models.Model):
    """
    Cross-Department Sharing Model

    Manages sharing of records and access permissions between departments.
    Provides invitation and approval workflow with comprehensive audit trails.
    """

    _name = "cross.department.sharing"
    _description = "Cross-Department Sharing Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(string="Sharing Reference", compute="_compute_name", store=True)
    sharing_type = fields.Selection(
        [
            ("record_access", "Record Access Sharing"),
            ("department_access", "Department Access Sharing"),
            ("temporary_access", "Temporary Access Grant"),
        ],
        string="Sharing Type",
        required=True,
        default="record_access",
        tracking=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "Invitation Sent"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("expired", "Expired"),
            ("revoked", "Revoked"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        readonly=False,
    )

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    requesting_department_id = fields.Many2one(
        "records.department", string="Requesting Department", required=True, tracking=True
    )
    target_department_id = fields.Many2one(
        "records.department", string="Target Department", required=True, tracking=True
    )
    requesting_user_id = fields.Many2one(
        "res.users", string="Requesting User", default=lambda self: self.env.user, required=True, tracking=True
    )
    approving_user_id = fields.Many2one("res.users", string="Approving User", tracking=True)

    # ============================================================================
    # RECORD SHARING
    # ============================================================================
    shared_record_ids = fields.Many2many(
        "records.container",
        "cross_department_sharing_container_rel",
        "sharing_id",
        "container_id",
        string="Shared Records",
        help="Records being shared with the target department",
    )

    shared_model = fields.Char(string="Shared Model", help="Model name of shared records (for generic sharing)")
    shared_record_names = fields.Text(string="Shared Record Names", compute="_compute_shared_record_names", store=True)

    # ============================================================================
    # ACCESS CONTROL
    # ============================================================================
    access_level = fields.Selection(
        [
            ("read", "Read Only"),
            ("write", "Read/Write"),
            ("full", "Full Access"),
        ],
        string="Access Level",
        required=True,
        default="read",
        tracking=True,
    )

    access_duration = fields.Integer(
        string="Access Duration (Days)",
        help="Number of days the access should remain active (0 = permanent)",
        default=30,
    )
    access_expires = fields.Datetime(string="Access Expires", compute="_compute_access_expires", store=True)

    # ============================================================================
    # WORKFLOW FIELDS
    # ============================================================================
    invitation_message = fields.Text(
        string="Invitation Message", help="Message explaining the sharing request", required=True
    )
    approval_message = fields.Text(
        string="Approval/Rejection Message", help="Message from approver explaining decision"
    )
    rejection_reason = fields.Text(string="Rejection Reason", tracking=True)

    # ============================================================================
    # AUDIT TRAILS
    # ============================================================================
    invitation_sent_date = fields.Datetime(string="Invitation Sent Date", readonly=True)
    approval_date = fields.Datetime(string="Approval Date", readonly=True)
    rejection_date = fields.Datetime(string="Rejection Date", readonly=True)
    revocation_date = fields.Datetime(string="Revocation Date", readonly=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("requesting_department_id", "target_department_id", "create_date")
    def _compute_name(self):
        """Generate sharing reference name."""
        for record in self:
            if record.requesting_department_id and record.target_department_id:
                date_str = record.create_date.strftime("%Y%m%d") if record.create_date else "NEW"
                record.name = f"SHR-{date_str}-{record.requesting_department_id.name[:3].upper()}-{record.target_department_id.name[:3].upper()}"
            else:
                record.name = f"SHR-{record.id or 'NEW'}"

    @api.depends("shared_record_ids")
    def _compute_shared_record_names(self):
        """Generate list of shared record names."""
        for record in self:
            if record.shared_record_ids:
                names = [container.name or f"Container {container.id}" for container in record.shared_record_ids]
                record.shared_record_names = "\n".join(names)
            else:
                record.shared_record_names = ""

    @api.depends("approval_date", "access_duration")
    def _compute_access_expires(self):
        """Compute access expiration date."""
        for record in self:
            if record.approval_date and record.access_duration > 0:
                record.access_expires = record.approval_date + timedelta(days=record.access_duration)
            else:
                record.access_expires = False

    # ============================================================================
    # CONSTRAINTS & VALIDATIONS
    # ============================================================================
    @api.constrains("requesting_department_id", "target_department_id")
    def _check_departments(self):
        """Ensure departments are different and valid."""
        for record in self:
            if record.requesting_department_id == record.target_department_id:
                raise ValidationError(_("Cannot share with the same department."))

    @api.constrains("access_duration")
    def _check_access_duration(self):
        """Validate access duration."""
        for record in self:
            if record.access_duration < 0:
                raise ValidationError(_("Access duration cannot be negative."))

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def action_send_invitation(self):
        """Send sharing invitation to target department."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Can only send invitations in draft state."))

        # Check if user has permission to request sharing
        if not self._can_request_sharing():
            raise UserError(_("You don't have permission to request sharing from this department."))

        # Send notification to target department managers
        self._notify_target_department()

        self.write(
            {
                "state": "sent",
                "invitation_sent_date": datetime.now(),
            }
        )

        return True

    def action_approve_sharing(self):
        """Approve the sharing request."""
        self.ensure_one()
        if self.state != "sent":
            raise UserError(_("Can only approve pending invitations."))

        # Check if user has permission to approve
        if not self._can_approve_sharing():
            raise UserError(_("You don't have permission to approve sharing for this department."))

        # Grant access permissions
        self._grant_access_permissions()

        self.write(
            {
                "state": "approved",
                "approving_user_id": self.env.user.id,
                "approval_date": datetime.now(),
                "approval_message": self.approval_message or "Approved",
            }
        )

        # Notify requesting department
        self._notify_approval_result("approved")

        return True

    def action_reject_sharing(self):
        """Reject the sharing request."""
        self.ensure_one()
        if self.state != "sent":
            raise UserError(_("Can only reject pending invitations."))

        if not self._can_approve_sharing():
            raise UserError(_("You don't have permission to reject sharing for this department."))

        self.write(
            {
                "state": "rejected",
                "approving_user_id": self.env.user.id,
                "rejection_date": datetime.now(),
                "rejection_reason": self.rejection_reason or "No reason provided",
            }
        )

        # Notify requesting department
        self._notify_approval_result("rejected")

        return True

    def action_revoke_sharing(self):
        """Revoke approved sharing."""
        self.ensure_one()
        if self.state != "approved":
            raise UserError(_("Can only revoke approved sharing."))

        # Check permissions
        if not self._can_revoke_sharing():
            raise UserError(_("You don't have permission to revoke this sharing."))

        # Remove access permissions
        self._revoke_access_permissions()

        self.write(
            {
                "state": "revoked",
                "revocation_date": datetime.now(),
            }
        )

        # Notify affected departments
        self._notify_revocation()

        return True

    def action_expire_sharing(self):
        """Automatically expire sharing when access duration is reached."""
        self.ensure_one()
        if self.state == "approved" and self.access_expires and self.access_expires <= datetime.now():
            self._revoke_access_permissions()
            self.write({"state": "expired"})

    # ============================================================================
    # PERMISSION CHECK METHODS
    # ============================================================================
    def _can_request_sharing(self):
        """Check if current user can request sharing from requesting department."""
        self.ensure_one()
        # User must be member of requesting department or have admin rights
        return (
            self.env.user.id in self.requesting_department_id.user_ids.ids
            or self.env.user.has_group("records_management.group_records_manager")
            or self.env.user.has_group("records_management.group_records_admin")
        )

    def _can_approve_sharing(self):
        """Check if current user can approve sharing for target department."""
        self.ensure_one()
        # User must be manager/admin of target department
        return self.env.user.id in self.target_department_id.manager_ids.ids or self.env.user.has_group(
            "records_management.group_records_admin"
        )

    def _can_revoke_sharing(self):
        """Check if current user can revoke sharing."""
        self.ensure_one()
        # Can be revoked by requester, target department manager, or admin
        return (
            self.env.user.id == self.requesting_user_id.id
            or self.env.user.id in self.target_department_id.manager_ids.ids
            or self.env.user.has_group("records_management.group_records_admin")
        )

    # ============================================================================
    # ACCESS MANAGEMENT METHODS
    # ============================================================================
    def _grant_access_permissions(self):
        """Grant access permissions to target department users."""
        self.ensure_one()

        # Create access rules for shared records
        for container in self.shared_record_ids:
            # Grant read access by default
            access_rule_vals = {
                "name": f"Shared Access: {self.name}",
                "model_id": self.env.ref("records_management.model_records_container").id,
                "group_id": self.target_department_id.access_group_id.id,
                "perm_read": True,
                "perm_write": self.access_level in ["write", "full"],
                "perm_create": self.access_level == "full",
                "perm_unlink": self.access_level == "full",
                "domain_force": f"[('id', '=', {container.id})]",
            }

            # Create temporary access rule
            rule = self.env["ir.rule"].create(access_rule_vals)

            # Store rule reference for later revocation
            self.env["cross.department.sharing.rule"].create(
                {
                    "sharing_id": self.id,
                    "rule_id": rule.id,
                    "expires_at": self.access_expires,
                }
            )

    def _revoke_access_permissions(self):
        """Revoke access permissions from target department."""
        self.ensure_one()

        # Find and remove associated access rules
        sharing_rules = self.env["cross.department.sharing.rule"].search([("sharing_id", "=", self.id)])

        for sharing_rule in sharing_rules:
            if sharing_rule.rule_id:
                sharing_rule.rule_id.unlink()
            sharing_rule.unlink()

    # ============================================================================
    # NOTIFICATION METHODS
    # ============================================================================
    def _notify_target_department(self):
        """Send notification to target department managers."""
        self.ensure_one()

        managers = self.target_department_id.manager_ids
        if managers:
            template = self.env.ref("records_management.sharing_invitation_template")
            for manager in managers:
                template.send_mail(self.id, email_values={"recipient_ids": [(4, manager.partner_id.id)]})

    def _notify_approval_result(self, result):
        """Notify requesting department of approval/rejection."""
        self.ensure_one()

        template_code = "sharing_approved_template" if result == "approved" else "sharing_rejected_template"
        template = self.env.ref(f"records_management.{template_code}")

        template.send_mail(self.id, email_values={"recipient_ids": [(4, self.requesting_user_id.partner_id.id)]})

    def _notify_revocation(self):
        """Notify departments of sharing revocation."""
        self.ensure_one()

        # Notify both departments
        recipients = [self.requesting_user_id.partner_id, *self.target_department_id.manager_ids.mapped("partner_id")]

        template = self.env.ref("records_management.sharing_revoked_template")
        for recipient in recipients:
            template.send_mail(self.id, email_values={"recipient_ids": [(4, recipient.id)]})

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def is_expired(self):
        """Check if sharing has expired."""
        self.ensure_one()
        return self.access_expires and self.access_expires <= datetime.now() and self.state == "approved"

    def get_remaining_days(self):
        """Get remaining days until expiration."""
        self.ensure_one()
        if self.access_expires and self.state == "approved":
            remaining = self.access_expires - datetime.now()
            return max(0, remaining.days)
        return 0

    # ============================================================================
    # CRON METHODS
    # ============================================================================
    @api.model
    def _cron_expire_sharing(self):
        """Cron job to expire sharing that has reached its duration."""
        expired_sharing = self.search(
            [
                ("state", "=", "approved"),
                ("access_expires", "<=", datetime.now()),
                ("access_expires", "!=", False),
            ]
        )

        for sharing in expired_sharing:
            sharing.action_expire_sharing()

        if expired_sharing:
            self.env["ir.logging"].create(
                {
                    "name": "Cross-Department Sharing Expiration",
                    "type": "server",
                    "level": "INFO",
                    "message": "Expired cross-department sharing records",
                    "path": "cross.department.sharing",
                    "func": "_cron_expire_sharing",
                }
            )
