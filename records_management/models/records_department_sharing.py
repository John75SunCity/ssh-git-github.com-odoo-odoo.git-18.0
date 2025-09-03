# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsDepartmentSharing(models.Model):
    """Model for managing cross-department sharing and collaboration"""

    _name = "records.department.sharing"
    _description = "Records Department Sharing"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Sharing Name", required=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)

    # Departments involved
    requesting_department_id = fields.Many2one(
        "records.department", string="Requesting Department", required=True, tracking=True
    )
    target_department_id = fields.Many2one(
        "records.department", string="Target Department", required=True, tracking=True
    )

    # Sharing details
    shared_resource_type = fields.Selection(
        [
            ("container", "Container Access"),
            ("billing", "Billing Access"),
            ("inventory", "Inventory Access"),
            ("documents", "Document Access"),
            ("all", "Full Access"),
        ],
        string="Resource Type",
        required=True,
        tracking=True,
    )

    # Status and approval
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending_approval", "Pending Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("active", "Active"),
            ("expired", "Expired"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Approval workflow
    requested_by_id = fields.Many2one(
        "res.users", string="Requested By", default=lambda self: self.env.user, tracking=True
    )
    approved_by_id = fields.Many2one("res.users", string="Approved By", tracking=True)
    approval_date = fields.Datetime(string="Approval Date", tracking=True)

    # Access permissions granted
    granted_permissions = fields.Selection(
        [("read", "Read Only"), ("write", "Read/Write"), ("admin", "Administrative")],
        string="Granted Permissions",
        tracking=True,
    )

    # Validity period
    valid_from = fields.Date(string="Valid From", tracking=True)
    valid_until = fields.Date(string="Valid Until", tracking=True)

    # Related records
    container_ids = fields.Many2many(
        "records.container",
        "records_department_sharing_container_rel",
        "sharing_id",
        "container_id",
        string="Shared Containers",
    )
    billing_ids = fields.Many2many(
        "records.billing",
        "records_department_sharing_billing_rel",
        "sharing_id",
        "billing_id",
        string="Shared Billing Records",
    )

    # Audit trail
    sharing_log_ids = fields.One2many("records.department.sharing.log", "sharing_id", string="Sharing Logs")

    @api.constrains("requesting_department_id", "target_department_id")
    def _check_departments(self):
        """Ensure departments are different and belong to same company"""
        for record in self:
            if record.requesting_department_id == record.target_department_id:
                raise ValidationError(_("Cannot share with the same department"))

            if record.requesting_department_id.partner_id != record.target_department_id.partner_id:
                raise ValidationError(_("Departments must belong to the same customer"))

    def action_request_approval(self):
        """Submit sharing request for approval"""
        self.ensure_one()
        if self.state != "draft":
            return

        # Create approval notification
        self.message_post(
            body=_("Sharing request submitted for approval to %s department") % self.target_department_id.name,
            message_type="notification",
        )

        self.state = "pending_approval"

    def action_approve(self):
        """Approve the sharing request"""
        self.ensure_one()
        if self.state != "pending_approval":
            return

        self.approved_by_id = self.env.user
        self.approval_date = fields.Datetime.now()
        self.state = "approved"

        # Log the approval
        self.env["records.department.sharing.log"].create(
            {
                "sharing_id": self.id,
                "action": "approved",
                "user_id": self.env.user.id,
                "notes": _("Sharing request approved"),
            }
        )

        # Notify requesting department
        self.message_post(body=_("Sharing request approved by %s") % self.env.user.name, message_type="notification")

    def action_reject(self):
        """Reject the sharing request"""
        self.ensure_one()
        if self.state != "pending_approval":
            return

        self.state = "rejected"

        # Log the rejection
        self.env["records.department.sharing.log"].create(
            {
                "sharing_id": self.id,
                "action": "rejected",
                "user_id": self.env.user.id,
                "notes": _("Sharing request rejected"),
            }
        )

    def action_activate(self):
        """Activate the sharing agreement"""
        self.ensure_one()
        if self.state != "approved":
            return

        self.state = "active"

        # Log activation
        self.env["records.department.sharing.log"].create(
            {
                "sharing_id": self.id,
                "action": "activated",
                "user_id": self.env.user.id,
                "notes": _("Sharing agreement activated"),
            }
        )

    def action_expire(self):
        """Expire the sharing agreement"""
        self.ensure_one()
        self.state = "expired"

        # Log expiration
        self.env["records.department.sharing.log"].create(
            {
                "sharing_id": self.id,
                "action": "expired",
                "user_id": self.env.user.id,
                "notes": _("Sharing agreement expired"),
            }
        )


class RecordsDepartmentSharingLog(models.Model):
    """Audit log for department sharing activities"""

    _name = "records.department.sharing.log"
    _description = "Records Department Sharing Log"
    _order = "create_date desc"

    sharing_id = fields.Many2one(
        "records.department.sharing", string="Sharing Agreement", required=True, ondelete="cascade"
    )
    action = fields.Selection(
        [
            ("created", "Created"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("activated", "Activated"),
            ("expired", "Expired"),
            ("accessed", "Accessed"),
        ],
        string="Action",
        required=True,
    )

    user_id = fields.Many2one("res.users", string="User", required=True)
    notes = fields.Text(string="Notes")
    timestamp = fields.Datetime(string="Timestamp", default=fields.Datetime.now)


class RecordsDepartmentSharingInvite(models.Model):
    """Model for managing department sharing invitations"""

    _name = "records.department.sharing.invite"
    _description = "Records Department Sharing Invite"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Invite Title", required=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)

    # Invite details
    inviting_department_id = fields.Many2one(
        "records.department", string="Inviting Department", required=True, tracking=True
    )
    invited_department_id = fields.Many2one(
        "records.department", string="Invited Department", required=True, tracking=True
    )

    # Invite status
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("accepted", "Accepted"),
            ("declined", "Declined"),
            ("expired", "Expired"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Permissions offered
    offered_permissions = fields.Selection(
        [("read", "Read Only"), ("write", "Read/Write"), ("admin", "Administrative")],
        string="Offered Permissions",
        required=True,
        tracking=True,
    )

    resource_type = fields.Selection(
        [
            ("container", "Container Access"),
            ("billing", "Billing Access"),
            ("inventory", "Inventory Access"),
            ("documents", "Document Access"),
            ("all", "Full Access"),
        ],
        string="Resource Type",
        required=True,
        tracking=True,
    )

    # Expiry
    expires_at = fields.Datetime(string="Expires At", tracking=True)

    # Response tracking
    responded_by_id = fields.Many2one("res.users", string="Responded By", tracking=True)
    response_date = fields.Datetime(string="Response Date", tracking=True)
    response_notes = fields.Text(string="Response Notes", tracking=True)

    # Resulting sharing agreement
    resulting_sharing_id = fields.Many2one(
        "records.department.sharing", string="Resulting Sharing Agreement", tracking=True
    )

    @api.constrains("inviting_department_id", "invited_department_id")
    def _check_departments(self):
        """Ensure departments are different and belong to same company"""
        for record in self:
            if record.inviting_department_id == record.invited_department_id:
                raise ValidationError(_("Cannot invite the same department"))

            if record.inviting_department_id.partner_id != record.invited_department_id.partner_id:
                raise ValidationError(_("Departments must belong to the same customer"))

    def action_send_invite(self):
        """Send the sharing invitation"""
        self.ensure_one()
        if self.state != "draft":
            return

        # Send notification to invited department
        self.message_post(
            body=_("Sharing invitation sent to %s department") % self.invited_department_id.name,
            message_type="notification",
        )

        self.state = "sent"

    def action_accept_invite(self):
        """Accept the sharing invitation"""
        self.ensure_one()
        if self.state != "sent":
            return

        self.responded_by_id = self.env.user
        self.response_date = fields.Datetime.now()
        self.state = "accepted"

        # Create the sharing agreement
        sharing = self.env["records.department.sharing"].create(
            {
                "name": _("Sharing Agreement: %s") % self.name,
                "description": self.description,
                "requesting_department_id": self.inviting_department_id.id,
                "target_department_id": self.invited_department_id.id,
                "shared_resource_type": self.resource_type,
                "granted_permissions": self.offered_permissions,
                "state": "approved",  # Auto-approved since invite was accepted
            }
        )

        self.resulting_sharing_id = sharing.id

        # Activate the sharing
        sharing.action_activate()

    def action_decline_invite(self):
        """Decline the sharing invitation"""
        self.ensure_one()
        if self.state != "sent":
            return

        self.responded_by_id = self.env.user
        self.response_date = fields.Datetime.now()
        self.state = "declined"

    def _check_expiry(self):
        """Check for expired invites and update status"""
        expired_invites = self.search([("state", "=", "sent"), ("expires_at", "<", fields.Datetime.now())])

        expired_invites.write({"state": "expired"})
