# -*- coding: utf-8 -*-
"""
Records Chain of Custody Management Module

This module provides comprehensive chain of custody tracking for the Records Management
System, ensuring complete NAID AAA compliance through detailed custody event logging,
secure transfer protocols, and immutable audit trails for all document movements.

Key Features:
- Complete custody event tracking with timestamps and personnel identification
- NAID AAA compliant audit trails with encrypted signatures and verification
- Multi-level custody transfers with supervisor approval and documentation
- Real-time custody status monitoring with automated alerts and notifications
- Integration with destruction workflows and certificate generation

Business Processes:
1. Custody Initiation: Establishing initial custody when documents are received
2. Transfer Events: Recording custody changes during internal transfers
3. External Transfers: Managing custody transfers to third-party providers
4. Destruction Events: Final custody transfer to authorized destruction facilities
5. Audit Documentation: Complete custody history with legal compliance verification

Compliance Standards:
- NAID AAA certification requirements for chain of custody documentation
- ISO 15489 standards for document lifecycle management and custody tracking
- Legal admissibility requirements for custody chain documentation
- Secure signature protocols for custody transfer verification

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import hashlib
import time

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RecordsChainOfCustody(models.Model):
    _name = "records.chain.of.custody"
    _description = "Records Chain of Custody"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "custody_date desc, sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Custody Record",
        required=True,
        tracking=True,
        index=True,
        help="Unique identifier for this custody record",
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Order sequence for custody events"
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
        help="User responsible for this custody record",
    )
    active = fields.Boolean(
        string="Active", default=True, help="Whether this custody record is active"
    )

    # ============================================================================
    # DOCUMENT AND CUSTOMER RELATIONSHIPS
    # ============================================================================
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        help="Customer who owns the documents",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner", 
        related="customer_id",
        store=True,
        help="Related partner field for One2many relationships compatibility"
    )
    document_id = fields.Many2one(
        "records.document",
        string="Document",
        ondelete="cascade",
        help="Specific document under custody",
    )
    container_id = fields.Many2one(
        "records.container",
        string="Container",
        ondelete="cascade",
        help="Container holding the documents",
    )
    work_order_id = fields.Many2one(
        "document.retrieval.work.order",
        string="Work Order",
        help="Associated work order if applicable",
    )
    compliance_id = fields.Many2one(
        "naid.compliance",
        string="NAID Compliance Framework",
        help="Associated NAID compliance framework",
    )

    # ============================================================================
    # CUSTODY EVENT DETAILS
    # ============================================================================
    custody_event = fields.Selection(
        [
            ("received", "Documents Received"),
            ("stored", "Documents Stored"),
            ("retrieved", "Documents Retrieved"),
            ("transferred", "Custody Transferred"),
            ("returned", "Documents Returned"),
            ("destroyed", "Documents Destroyed"),
            ("verified", "Custody Verified"),
            ("audit", "Audit Event"),
        ],
        string="Custody Event Type",
        required=True,
        tracking=True,
        help="Type of custody event being recorded",
    )
    custody_date = fields.Datetime(
        string="Custody Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        help="Date and time when custody event occurred",
    )
    description = fields.Text(
        string="Event Description", help="Detailed description of the custody event"
    )

    # ============================================================================
    # CUSTODY TRANSFER INFORMATION
    # ============================================================================
    custody_from_id = fields.Many2one(
        "res.users",
        string="Custody From",
        help="User transferring custody (previous custodian)",
    )
    custody_to_id = fields.Many2one(
        "res.users",
        string="Custody To",
        help="User receiving custody (new custodian)"
    )
    transfer_reason = fields.Selection(
        [
            ("routine", "Routine Transfer"),
            ("request", "Customer Request"),
            ("destruction", "For Destruction"),
            ("audit", "Audit Requirement"),
            ("maintenance", "System Maintenance"),
            ("emergency", "Emergency Transfer"),
        ],
        string="Transfer Reason",
        help="Reason for custody transfer",
    )
    supervisor_approval = fields.Boolean(
        string="Supervisor Approval",
        default=False,
        help="Whether supervisor approval was obtained",
    )
    supervisor_id = fields.Many2one(
        "res.users",
        string="Approving Supervisor",
        help="Supervisor who approved the custody transfer",
    )

    # ============================================================================
    # PRIORITY AND REQUEST MANAGEMENT
    # ============================================================================
    priority = fields.Selection(
        [
            ("low", "Low Priority"),
            ("medium", "Medium Priority"),
            ("high", "High Priority"),
            ("urgent", "Urgent"),
            ("critical", "Critical"),
        ],
        string="Priority Level",
        default="medium",
        tracking=True,
        help="Priority level of this custody event",
    )
    request_type = fields.Selection(
        [
            ("pickup", "Document Pickup"),
            ("delivery", "Document Delivery"),
            ("transfer", "Internal Transfer"),
            ("destruction", "Document Destruction"),
            ("retrieval", "Document Retrieval"),
            ("verification", "Custody Verification"),
        ],
        string="Request Type",
        help="Type of request associated with custody event",
    )

    # ============================================================================
    # NAID AAA COMPLIANCE FIELDS
    # ============================================================================
    custody_signature = fields.Binary(
        string="Custody Signature", help="Digital signature for custody transfer"
    )
    signature_date = fields.Datetime(
        string="Signature Date", help="Date and time when signature was captured"
    )
    witness_id = fields.Many2one(
        "res.users", string="Witness", help="Witness to the custody transfer"
    )
    verification_code = fields.Char(
        string="Verification Code",
        help="Unique verification code for this custody event",
    )
    chain_integrity = fields.Selection(
        [
            ("intact", "Chain Intact"),
            ("broken", "Chain Broken"),
            ("suspicious", "Suspicious Activity"),
            ("verified", "Independently Verified"),
        ],
        string="Chain Integrity Status",
        default="intact",
        tracking=True,
        help="Status of chain of custody integrity",
    )

    # ============================================================================
    # LOCATION AND PHYSICAL TRACKING
    # ============================================================================
    location_from_id = fields.Many2one(
        "records.location",
        string="Origin Location",
        help="Location where documents originated",
    )
    location_to_id = fields.Many2one(
        "records.location",
        string="Destination Location",
        help="Location where documents are being transferred",
    )
    physical_condition = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("damaged", "Damaged"),
        ],
        string="Physical Condition",
        help="Physical condition of documents during transfer",
    )
    container_seal = fields.Char(
        string="Container Seal Number", help="Security seal number if applicable"
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending Approval"),
            ("confirmed", "Confirmed"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("verified", "Verified"),
            ("cancelled", "Cancelled"),
        ],
        string="Custody Status",
        default="draft",
        tracking=True,
        help="Current status of the custody record",
    )

    # ============================================================================
    # METADATA AND TRACKING
    # ============================================================================
    key = fields.Char(string="Metadata Key", help="Key for additional metadata storage")
    value = fields.Char(
        string="Metadata Value", help="Value for additional metadata storage"
    )
    notes = fields.Text(string="Internal Notes", help="Internal notes and observations")
    external_reference = fields.Char(
        string="External Reference", help="External system reference number"
    )
    
    # ============================================================================
    # ADDITIONAL FIELDS
    # ============================================================================
    transfer_date = fields.Datetime(string='Transfer Date', default=fields.Datetime.now)
    verified = fields.Boolean(string='Verified', default=False)

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("name", "custody_event", "custody_date")
    def _compute_display_name(self):
        """Compute display name with event details"""
        for record in self:
            parts = []
            if record.name:
                parts.append(record.name)
            if record.custody_event:
                event_label = dict(record._fields["custody_event"].selection).get(
                    record.custody_event, record.custody_event
                )
                parts.append(_("(%s)", event_label))
            if record.custody_date:
                parts.append(record.custody_date.strftime("%Y-%m-%d %H:%M"))
            record.display_name = " - ".join(parts) if parts else "New Custody Record"

    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Formatted display name with event details",
    )

    @api.depends("custody_from_id", "custody_to_id", "custody_event")
    def _compute_transfer_summary(self):
        """Compute custody transfer summary"""
        for record in self:
            if record.custody_from_id and record.custody_to_id:
                record.transfer_summary = _("%s → %s", record.custody_from_id.name, record.custody_to_id.name)
            elif record.custody_event:
                event_label = dict(record._fields["custody_event"].selection).get(
                    record.custody_event, record.custody_event
                )
                record.transfer_summary = event_label
            else:
                record.transfer_summary = _("No Transfer")

    transfer_summary = fields.Char(
        string="Transfer Summary",
        compute="_compute_transfer_summary",
        store=True,
        help="Summary of custody transfer",
    )

    @api.depends("custody_date", "state")
    def _compute_days_since_event(self):
        """Compute days since custody event, accounting for user timezone"""
        for record in self:
            if record.custody_date:
                now_dt = fields.Datetime.context_timestamp(
                    record, fields.Datetime.now()
                )
                event_dt = fields.Datetime.context_timestamp(
                    record, record.custody_date
                )
                # Ensure both are datetime objects
                now_dt = fields.Datetime.to_datetime(now_dt)
                event_dt = fields.Datetime.to_datetime(event_dt)
                delta = now_dt - event_dt
                record.days_since_event = delta.days
            else:
                record.days_since_event = 0

    days_since_event = fields.Integer(
        string="Days Since Event",
        compute="_compute_days_since_event",
        help="Number of days since custody event occurred",
    )

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-generate verification code"""
        for vals in vals_list:
            if not vals.get("verification_code"):
                vals["verification_code"] = (
                    self.env["ir.sequence"].next_by_code("records.chain.of.custody")
                    or "NEW"
                )

            # Set custody date if not provided
            if not vals.get("custody_date"):
                vals["custody_date"] = fields.Datetime.now()

        return super().create(vals_list)

    def write(self, vals):
        """Override write to log state changes"""
        # Log significant state changes
        if "state" in vals:
            for record in self:
                if vals["state"] != record.state:
                    old = dict(record._fields["state"].selection).get(record.state, record.state)
                    new = dict(record._fields["state"].selection).get(vals["state"], vals["state"])
                    record.message_post(
                        body=_("Custody status changed from %s to %s", old, new)
                    )
        return super().write(vals)

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def generate_verification_code(self):
        """Generate unique verification code for custody event"""
        self.ensure_one()

        # Create hash based on record data and timestamp
        data_string = "%s_%s_%s_%s" % (
            self.id, self.custody_date, time.time(), self.customer_id.id
        )
        verification_hash = (
            hashlib.sha256(data_string.encode()).hexdigest()[:12].upper()
        )

        self.verification_code = "COC-%s" % verification_hash

        return self.verification_code

    def verify_custody_integrity(self):
        """Verify integrity of custody chain"""
        self.ensure_one()

        # Check for previous custody records
        previous_records = self.search(
            [
                ("document_id", "=", self.document_id.id),
                ("custody_date", "<", self.custody_date),
            ],
            order="custody_date desc",
            limit=1,
        )

        if previous_records and previous_records.custody_to_id != self.custody_from_id:
            self.chain_integrity = "broken"
            self.message_post(
                body=_("Chain of custody integrity broken: Previous custodian mismatch"),
                message_type="comment",
            )
            return False

        self.chain_integrity = "verified"
        return True

    def create_custody_certificate(self):
        """Generate custody transfer certificate"""
        self.ensure_one()

        if not self.verification_code:
            self.generate_verification_code()

        # Create certificate record
        certificate_vals = {
            "name": _("Custody Certificate - %s", self.name),
            "certificate_type": "custody",
            "customer_id": self.customer_id.id,
            "document_ids": [(6, 0, [self.document_id.id])] if self.document_id else [],
            "custody_record_id": self.id,
            "verification_code": self.verification_code,
            "issue_date": fields.Date.today(),
        }

        certificate = self.env["naid.certificate"].create(certificate_vals)

        self.message_post(
            body=_("Custody certificate generated: %s", certificate.name),
            message_type="notification",
        )

        return certificate

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm_custody(self):
        """Confirm custody event"""
        self.ensure_one()
        if self.state != "draft":
            raise ValidationError(_("Only draft custody records can be confirmed"))
        self.write({"state": "confirmed", "signature_date": fields.Datetime.now()})
        self.verify_custody_integrity()
        self.message_post(body=_("Custody event confirmed by %s", self.env.user.name))

    def action_complete_custody(self):
        """Complete custody transfer"""
        self.ensure_one()
        if self.state not in ["confirmed", "in_progress"]:
            raise ValidationError(_("Only confirmed or in-progress custody records can be completed"))
        self.write({"state": "completed"})
        if self.custody_event in ["transferred", "destroyed", "returned"]:
            self.create_custody_certificate()
        self.message_post(body=_("Custody transfer completed"))

    def action_verify_custody(self):
        """Verify custody record by supervisor"""
        self.ensure_one()
        if self.state != "completed":
            raise ValidationError(_("Only completed custody records can be verified"))
        self.write({"state": "verified", "supervisor_id": self.env.user.id, "supervisor_approval": True})
        self.message_post(body=_("Custody record verified by supervisor: %s", self.env.user.name))

    def action_cancel_custody(self):
        """Cancel custody record"""
        self.ensure_one()
        if self.state in ["completed", "verified"]:
            raise ValidationError(_("Cannot cancel completed or verified custody records"))
        self.write({"state": "cancelled"})
        self.message_post(body=_("Custody record cancelled by %s", self.env.user.name), message_type="comment")

    def action_reset_to_draft(self):
        """Reset custody record to draft"""
        self.ensure_one()
        if self.state == "verified":
            raise ValidationError(_("Cannot reset verified custody records to draft"))
        self.write({"state": "draft"})
        self.message_post(body=_("Custody record reset to draft"), message_type="comment")

    def action_view_custody_history(self):
        """View complete custody history for document"""
        self.ensure_one()

        domain = []
        if self.document_id:
            domain = [("document_id", "=", self.document_id.id)]
        elif self.container_id:
            domain = [("container_id", "=", self.container_id.id)]
        else:
            domain = [("customer_id", "=", self.customer_id.id)]

        return {
            "type": "ir.actions.act_window",
            "name": _("Custody History"),
            "res_model": "records.chain.of.custody",
            "view_mode": "tree,form",
            "domain": domain,
            "context": {"default_customer_id": self.customer_id.id},
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("custody_from_id", "custody_to_id")
    def _check_custody_transfer(self):
        """Validate custody transfer users"""
        for record in self:
            if record.custody_from_id and record.custody_to_id:
                if record.custody_from_id == record.custody_to_id:
                    raise ValidationError(
                        _("Cannot transfer custody from and to the same user")
                    )

    @api.constrains("custody_date")
    def _check_custody_date(self):
        """Validate custody date"""
        for record in self:
            if record.custody_date and record.custody_date > fields.Datetime.now():
                raise ValidationError(_("Custody date cannot be in the future"))

    @api.constrains("priority", "custody_event")
    def _check_priority_event_combination(self):
        """Validate priority and event type combinations"""
        for record in self:
            if record.custody_event == "destroyed" and record.priority not in [
                "high",
                "urgent",
                "critical",
            ]:
                raise ValidationError(
                    _("Destruction events must have high, urgent, or critical priority")
                )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name_parts = [record.name]

            if record.custody_event:
                event_label = dict(record._fields["custody_event"].selection).get(
                    record.custody_event, record.custody_event or "Unknown Event"
                )
                name_parts.append(_("(%s)", event_label))

            if record.customer_id:
                name_parts.append(_("- %s", record.customer_id.name))

            result.append((record.id, " ".join(name_parts)))

        return result

    @api.model
    def _search_name(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Enhanced search by name, customer, or verification code"""
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                "|",
                ("name", operator, name),
                ("customer_id.name", operator, name),
                ("verification_code", operator, name),
                ("external_reference", operator, name),
            ]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def get_custody_chain(self, document_id=None, container_id=None, customer_id=None):
        """Get complete custody chain for a document, container, or customer"""
        domain = [("state", "!=", "cancelled")]

        if document_id:
            domain.append(("document_id", "=", document_id))
        elif container_id:
            domain.append(("container_id", "=", container_id))
        elif customer_id:
            domain.append(("customer_id", "=", customer_id))

        return self.search(domain, order="custody_date asc")

    @api.model
    def create_automatic_custody_event(
        self, document_id, event_type, user_from=None, user_to=None, description=None
    ):
        """Create automatic custody event for system workflows"""
        document = self.env["records.document"].browse(document_id)
        if not document.exists():
            return False

        vals = {
            "name": _("Auto-%s: %s", event_type.title(), document.name),
            "document_id": document_id,
            "customer_id": document.customer_id.id,
            "custody_event": event_type,
            "custody_date": fields.Datetime.now(),
            "description": description or _("Automatic %s event", event_type),
            "custody_from_id": user_from.id if user_from else False,
            "custody_to_id": user_to.id if user_to else False,
            "state": "confirmed",
        }

        custody_record = self.create(vals)
        custody_record.verify_custody_integrity()

        return custody_record
