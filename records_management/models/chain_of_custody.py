"""Chain of Custody tracking for NAID AAA compliance in Records Management.

This model provides comprehensive audit trail tracking for document custody
from creation through destruction, ensuring full NAID AAA compliance.
"""

# Python stdlib imports
import logging
import random
import string
from datetime import datetime

# Odoo core imports
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ChainOfCustody(models.Model):
    """Comprehensive chain of custody tracking for NAID AAA compliance.

    This model tracks every custody transfer, location change, and handling event
    for documents and containers throughout their lifecycle.
    """

    _name = "chain.of.custody"
    _description = "Chain of Custody Tracking"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, transfer_date desc, id desc"
    _rec_name = "display_name"

    # Core Identification
    name = fields.Char(
        string="Custody Reference",
        required=True,
        copy=False,
        index=True,
        help="Unique reference for this custody record",
    )

    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Human-readable display name",
    )

    sequence = fields.Integer(
        string="Sequence", default=10, help="Order of custody transfers"
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Uncheck to archive this custody record",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        help="Company responsible for this custody record",
    )

    # Transfer Information
    transfer_date = fields.Datetime(
        string="Transfer Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        help="Date and time of custody transfer",
    )

    transfer_type = fields.Selection(
        [
            ("creation", "Initial Creation"),
            ("storage", "Storage Transfer"),
            ("retrieval", "Retrieval"),
            ("transport", "Transportation"),
            ("destruction", "Destruction"),
            ("return", "Return to Customer"),
            ("internal", "Internal Transfer"),
            ("audit", "Audit/Inspection"),
            ("maintenance", "Maintenance"),
            ("emergency", "Emergency Access"),
        ],
        string="Transfer Type",
        required=True,
        tracking=True,
    )

    # Custody Parties
    from_custodian_id = fields.Many2one(
        comodel_name="res.users",
        string="From Custodian",
        tracking=True,
        help="Previous custodian releasing custody",
    )

    to_custodian_id = fields.Many2one(
        comodel_name="res.users",
        string="To Custodian",
        required=True,
        tracking=True,
        help="New custodian receiving custody",
    )

    witness_id = fields.Many2one(
        comodel_name="res.users",
        string="Witness",
        tracking=True,
        help="Witness to the custody transfer",
    )

    department_id = fields.Many2one(
        comodel_name="records.department",
        string="Department",
        tracking=True,
        help="Department responsible for custody",
    )

    # Location Tracking
    from_location_id = fields.Many2one(
        comodel_name="records.location",
        string="From Location",
        tracking=True,
        help="Previous location",
    )

    to_location_id = fields.Many2one(
        comodel_name="records.location",
        string="To Location",
        required=True,
        tracking=True,
        help="New location",
    )

    specific_location = fields.Char(
        string="Specific Location",
        help="Detailed location description (shelf, room, etc.)",
    )

    # Related Records
    container_id = fields.Many2one(
        comodel_name="records.container",
        string="Container",
        ondelete="cascade",
        index=True,
        help="Related container if applicable",
    )

    document_id = fields.Many2one(
        comodel_name="records.document",
        string="Document",
        ondelete="cascade",
        index=True,
        help="Related document if applicable",
    )

    request_id = fields.Many2one(
        comodel_name="portal.request",
        string="Related Request",
        ondelete="set null",
        help="Request that triggered this custody transfer",
    )

    destruction_certificate_id = fields.Many2one(
        comodel_name="naid.certificate",
        string="Destruction Certificate",
        ondelete="set null",
        help="Certificate if this was a destruction transfer",
    )

    # Transfer Details
    reason = fields.Text(
        string="Transfer Reason",
        required=True,
        tracking=True,
        help="Detailed reason for custody transfer",
    )

    conditions = fields.Text(
        string="Conditions/Notes", help="Special conditions or notes about the transfer"
    )

    transfer_method = fields.Selection(
        [
            ("hand_delivery", "Hand Delivery"),
            ("secure_transport", "Secure Transport"),
            ("courier", "Courier Service"),
            ("internal_move", "Internal Move"),
            ("pickup_service", "Pickup Service"),
            ("mail", "Postal Mail"),
            ("electronic", "Electronic Transfer"),
        ],
        string="Transfer Method",
        tracking=True,
    )

    # NAID AAA Compliance
    naid_compliant = fields.Boolean(
        string="NAID AAA Compliant",
        default=True,
        help="Whether this transfer meets NAID AAA standards",
    )

    security_level = fields.Selection(
        [
            ("standard", "Standard Security"),
            ("high", "High Security"),
            ("confidential", "Confidential"),
            ("secret", "Secret"),
            ("top_secret", "Top Secret"),
        ],
        string="Security Level",
        default="standard",
        tracking=True,
    )

    authorization_required = fields.Boolean(
        string="Authorization Required",
        default=False,
        help="Whether special authorization was required",
    )

    authorized_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Authorized By",
        help="User who authorized this transfer",
    )

    # Digital Signatures & Verification
    custodian_signature = fields.Binary(
        string="Custodian Signature", help="Digital signature of receiving custodian"
    )

    witness_signature = fields.Binary(
        string="Witness Signature", help="Digital signature of witness"
    )

    signature_date = fields.Datetime(
        string="Signature Date", help="Date and time signatures were captured"
    )

    verification_code = fields.Char(
        string="Verification Code",
        copy=False,
        help="Unique verification code for this transfer",
    )

    # Status and Validation
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("in_transit", "In Transit"),
            ("completed", "Completed"),
            ("verified", "Verified"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    is_verified = fields.Boolean(
        string="Verified",
        default=False,
        help="Whether this transfer has been verified",
    )

    verified_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Verified By",
        help="User who verified this transfer",
    )

    verified_date = fields.Datetime(
        string="Verification Date", help="Date and time of verification"
    )

    # Audit Information
    audit_log_ids = fields.One2many(
        comodel_name="naid.audit.log",
        inverse_name="custody_id",
        string="Audit Logs",
        help="Related audit log entries",
    )

    audit_notes = fields.Text(
        string="Audit Notes", help="Special audit notes or observations"
    )

    # Computed Fields
    duration_hours = fields.Float(
        string="Duration (Hours)",
        compute="_compute_duration",
        store=True,
        help="Duration of custody transfer",
    )

    next_transfer_id = fields.Many2one(
        comodel_name="chain.of.custody",
        string="Next Transfer",
        compute="_compute_next_transfer",
        help="Next custody transfer in the chain",
    )

    previous_transfer_id = fields.Many2one(
        comodel_name="chain.of.custody",
        string="Previous Transfer",
        compute="_compute_previous_transfer",
        help="Previous custody transfer in the chain",
    )

    is_final_transfer = fields.Boolean(
        string="Final Transfer",
        compute="_compute_is_final",
        help="Whether this is the final transfer (destruction)",
    )

    # Related Record Counts
    related_container_count = fields.Integer(
        string="Related Containers", compute="_compute_related_counts"
    )

    related_document_count = fields.Integer(
        string="Related Documents", compute="_compute_related_counts"
    )

    # Computed Methods
    @api.depends("name", "transfer_type", "to_custodian_id")
    def _compute_display_name(self):
        """Compute display name for the custody record."""
        for record in self:
            if record.name and record.transfer_type and record.to_custodian_id:
                selection_dict = (
                    dict(record._fields["transfer_type"].selection)
                    if hasattr(record._fields["transfer_type"], "selection")
                    else {}
                )
                transfer_type_label = selection_dict.get(
                    record.transfer_type, record.transfer_type or ""
                )
                to_custodian_name = (
                    record.to_custodian_id.name
                    if record.to_custodian_id
                    and hasattr(record.to_custodian_id, "name")
                    else ""
                )
                record.display_name = f"{record.name or ''} - {transfer_type_label} to {to_custodian_name}"
            else:
                record.display_name = record.name or "New Custody Record"

    @api.depends("transfer_date", "state")
    def _compute_duration(self):
        """Compute duration of custody transfer."""
        for record in self:
            if not record.transfer_date:
                record.duration_hours = 0.0
                continue

            if record.state == "completed":
                # Only calculate duration if related to a container or document
                if not record.container_id and not record.document_id:
                    record.duration_hours = 0.0
                    continue

                domain = [("sequence", ">", record.sequence)]
                if record.container_id:
                    domain.append(("container_id", "=", record.container_id.id))
                elif record.document_id:
                    domain.append(("document_id", "=", record.document_id.id))

                next_transfer = self.search(domain, order="sequence asc", limit=1)

                if next_transfer and next_transfer.transfer_date:
                    end_time = next_transfer.transfer_date
                else:
                    # Use current time if no next transfer
                    end_time = fields.Datetime.now()

                duration = end_time - record.transfer_date
                record.duration_hours = max(0.0, duration.total_seconds() / 3600)
            else:
                record.duration_hours = 0.0

    @api.depends("sequence", "container_id", "document_id")
    def _compute_next_transfer(self):
        """Compute next transfer in the chain."""
        for record in self:
            if not record.container_id and not record.document_id:
                record.next_transfer_id = False
                continue

            domain = [("sequence", ">", record.sequence)]

            # Build domain based on what related records exist
            if record.container_id and record.document_id:
                # Use robust OR logic for exactly two conditions
                domain = [
                    "|",
                    ("container_id", "=", record.container_id.id),
                    ("document_id", "=", record.document_id.id),
                ] + domain
            elif record.container_id:
                domain.append(("container_id", "=", record.container_id.id))
            elif record.document_id:
                domain.append(("document_id", "=", record.document_id.id))

            record.next_transfer_id = self.search(domain, order="sequence asc", limit=1)

    @api.depends("sequence", "container_id", "document_id")
    def _compute_previous_transfer(self):
        """Compute previous transfer in the chain."""
        for record in self:
            if not record.container_id and not record.document_id:
                record.previous_transfer_id = False
                continue

            domain = [("sequence", "<", record.sequence)]

            # Build domain based on what related records exist
            if record.container_id and record.document_id:
                # Use proper prefix OR syntax for domain
                domain = [
                    "|",
                    ("container_id", "=", record.container_id.id),
                    ("document_id", "=", record.document_id.id),
                ] + domain
            elif record.container_id:
                domain.append(("container_id", "=", record.container_id.id))
            elif record.document_id:
                domain.append(("document_id", "=", record.document_id.id))

            record.previous_transfer_id = self.search(
                domain, order="sequence desc", limit=1
            )

    @api.depends("transfer_type", "next_transfer_id")
    def _compute_is_final(self):
        """Determine if this is the final transfer."""
        for record in self:
            record.is_final_transfer = (
                record.transfer_type == "destruction" or not record.next_transfer_id
            )

    @api.depends("container_id", "document_id")
    def _compute_related_counts(self):
        """Compute counts of related records."""
        for record in self:
            record.related_container_count = 1 if record.container_id else 0
            record.related_document_count = 1 if record.document_id else 0

    # Validation Methods
    @api.constrains("transfer_date")
    def _check_transfer_date(self):
        """Validate transfer date is not in the future."""
        for record in self:
            if record.transfer_date and record.transfer_date > fields.Datetime.now():
                raise ValidationError(_("Transfer date cannot be in the future."))

    @api.constrains("from_custodian_id", "to_custodian_id")
    def _check_custodians(self):
        """Validate custodian assignment."""
        for record in self:
            if (
                record.from_custodian_id
                and record.from_custodian_id == record.to_custodian_id
            ):
                raise ValidationError(
                    _("From and To custodians cannot be the same person.")
                )

    @api.constrains("container_id", "document_id")
    def _check_related_record(self):
        """Ensure at least one related record is specified."""
        for record in self:
            if not record.container_id and not record.document_id:
                raise ValidationError(
                    _("Either Container or Document must be specified.")
                )

    @api.constrains("security_level", "naid_compliant")
    def _check_naid_compliance(self):
        """Validate NAID compliance requirements."""
        for record in self:
            if record.naid_compliant and record.security_level in [
                "secret",
                "top_secret",
            ]:
                if not record.authorization_required or not record.authorized_by_id:
                    raise ValidationError(
                        _(
                            "High security transfers require authorization and authorized by user."
                        )
                    )

    # Generation Methods
    @api.model
    def _generate_reference(self):
        """Generate unique custody reference."""
        sequence = self.env["ir.sequence"].next_by_code("chain.of.custody") or "COC"
        return f"COC-{sequence}-{datetime.now().strftime('%Y%m%d')}"

    def _generate_verification_code(self):
        """Generate verification code for transfer."""
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Business Methods
    def action_confirm_transfer(self):
        """Confirm the custody transfer."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft transfers can be confirmed."))

        self.write(
            {
                "state": "pending",
                "verification_code": self._generate_verification_code(),
            }
        )

        # Create audit log
        self.env["naid.audit.log"].create(
            {
                "event_type": "custody_transfer",
                "description": f"Custody transfer confirmed: {self.display_name}",
                "user_id": self.env.user.id,
                "custody_id": self.id,
                "container_id": self.container_id.id if self.container_id else False,
                "document_id": self.document_id.id if self.document_id else False,
            }
        )

    def action_start_transfer(self):
        """Start the custody transfer process."""
        self.ensure_one()
        if self.state != "pending":
            raise UserError(_("Only pending transfers can be started."))

        self.write({"state": "in_transit"})

    def action_complete_transfer(self):
        """Complete the custody transfer."""
        self.ensure_one()
        if self.state != "in_transit":
            raise UserError(_("Only in-transit transfers can be completed."))

        self.write({"state": "completed", "signature_date": fields.Datetime.now()})

        # Update related records
        if self.container_id:
            self.container_id.write(
                {
                    "current_custodian_id": self.to_custodian_id.id,
                    "current_location_id": self.to_location_id.id,
                }
            )

        if self.document_id:
            self.document_id.write(
                {
                    "current_custodian_id": self.to_custodian_id.id,
                    "current_location_id": self.to_location_id.id,
                }
            )

    def action_verify_transfer(self):
        """Verify the custody transfer."""
        self.ensure_one()
        if self.state != "completed":
            raise UserError(_("Only completed transfers can be verified."))

        self.write(
            {
                "state": "verified",
                "is_verified": True,
                "verified_by_id": self.env.user.id,
                "verified_date": fields.Datetime.now(),
            }
        )

    def action_cancel_transfer(self):
        """Cancel the custody transfer."""
        self.ensure_one()
        if self.state in ["verified", "cancelled"]:
            raise UserError(_("Verified or cancelled transfers cannot be cancelled."))

        self.write({"state": "cancelled"})

    def action_reject_transfer(self):
        """Reject the custody transfer (alias of cancel but preserves semantic intent).

        View button calls this; implement lightweight wrapper so ParseError is resolved.
        Creates an audit log entry distinct from generic cancellation for traceability.
        """
        self.ensure_one()
        # Reuse cancel logic constraints
        if self.state in ["verified", "cancelled"]:
            raise UserError(_("Verified or cancelled transfers cannot be rejected."))
        self.write({"state": "cancelled"})
        self.env["naid.audit.log"].create(
            {
                "event_type": "custody_rejected",
                "description": f"Custody transfer rejected: {self.display_name}",
                "user_id": self.env.user.id,
                "custody_id": self.id,
                "container_id": self.container_id.id if self.container_id else False,
                "document_id": self.document_id.id if self.document_id else False,
            }
        )

    # Reporting Methods
    def generate_custody_report(self):
        """Generate comprehensive custody report."""
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.custody_chain_report",
            "model": "chain.of.custody",
            "context": {"active_ids": self.ids},
        }

    def get_full_chain(self):
        domain = []
        if self.container_id and self.document_id:
            domain = ["|", ("container_id", "=", self.container_id.id), ("document_id", "=", self.document_id.id)]
        elif self.container_id:
            domain = [("container_id", "=", self.container_id.id)]
        elif self.document_id:
            domain = [("document_id", "=", self.document_id.id)]

        if domain:
            return self.search(domain, order="sequence, transfer_date")
        return self.browse()
        return self.browse()

    # Integration Methods
    def create_destruction_record(self):
        """Create NAID destruction certificate for final transfer."""
        if not self.is_final_transfer or self.transfer_type != "destruction":
            raise UserError(_("This is not a destruction transfer."))

        # Determine customer/partner for certificate
        partner = False
        if self.document_id and getattr(self.document_id, "partner_id", False):
            partner = self.document_id.partner_id.id
        elif self.container_id and getattr(self.container_id, "partner_id", False):
            partner = self.container_id.partner_id.id
        elif self.department_id and getattr(self.department_id, "partner_id", False):
            partner = self.department_id.partner_id.id

        if not partner:
            raise UserError(
                _("Unable to determine customer for destruction certificate.")
            )

        certificate_vals = {
            "partner_id": partner,
            "destruction_date": self.transfer_date,
            "res_model": "chain.of.custody",
            "res_id": self.id,
            # Optional linkage of containers/boxes done by user later if needed
        }

        certificate = self.env["naid.certificate"].create(certificate_vals)
        self.destruction_certificate_id = certificate.id

        return certificate

    # Override Methods
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add audit logging and set default name. Batch compatible."""
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self._generate_reference()
        records = super(ChainOfCustody, self).create(vals_list)
        log_messages = []
        for record in records:
            self.env["naid.audit.log"].create(
                {
                    "event_type": "custody_created",
                    "description": f"New custody record created: {record.display_name}",
                    "user_id": self.env.user.id,
                    "custody_id": record.id,
                    "container_id": record.container_id.id
                    if record.container_id
                    else False,
                    "document_id": record.document_id.id
                    if record.document_id
                    else False,
                }
            )
            log_messages.append(f"Created custody record: {record.display_name}")
        if log_messages:
            _logger.info("\n".join(log_messages))
        return records

    def write(self, vals):
        """Override write to add audit logging."""
        result = super(ChainOfCustody, self).write(vals)

        # Log significant changes
        tracked_fields = ["state", "to_custodian_id", "to_location_id", "transfer_type"]
        changed_fields = [field for field in tracked_fields if field in vals]

        if changed_fields:
            for record in self:
                self.env["naid.audit.log"].create(
                    {
                        "event_type": "custody_modified",
                        "description": f"Custody record modified: {record.display_name} - Fields: {', '.join(changed_fields)}",
                        "user_id": self.env.user.id,
                        "custody_id": record.id,
                        "container_id": record.container_id.id
                        if record.container_id
                        else False,
                        "document_id": record.document_id.id
                        if record.document_id
                        else False,
                    }
                )

        return result

    def unlink(self):
        """Override unlink to prevent deletion of verified transfers."""
        for record in self:
            if bool(record.is_verified):
                raise UserError(
                    _(
                        "Verified custody transfers cannot be deleted for compliance reasons."
                    )
                )

        return super(ChainOfCustody, self).unlink()

    # Utility Methods
    @api.model
    def get_custody_statistics(self, date_from=None, date_to=None):
        """Get custody transfer statistics."""
        domain = []
        if date_from:
            domain.append(("transfer_date", ">=", date_from))
        if date_to:
            domain.append(("transfer_date", "<=", date_to))

        transfer_type_counts = self.read_group(
            domain, ["transfer_type"], ["transfer_type"]
        )
        # Format as {transfer_type: count}
        transfer_types = {
            entry["transfer_type"]: entry["transfer_type_count"]
            for entry in transfer_type_counts
            if entry["transfer_type"]
        }
        total_count = self.search_count(domain)
        completed_count = self.search_count(domain + [("state", "=", "completed")])
        return {
            "total_transfers": total_count,
            "completed_transfers": completed_count,
            "transfer_types": transfer_types,
        }
