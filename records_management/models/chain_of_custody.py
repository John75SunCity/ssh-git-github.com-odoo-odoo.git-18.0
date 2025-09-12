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

    # Centralized prefix for custody references to avoid mismatches
    _CUSTODY_PREFIX = "COC"

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

    # Customer/Partner relationship
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        help="Customer associated with this custody transfer",
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

    audit_log_count = fields.Integer(
        string="Audit Logs Count",
        compute="_compute_audit_log_count",
        store=False,
        help="Number of related audit log entries for quick stat button display",
    )

    audit_notes = fields.Text(
        string="Audit Notes", help="Special audit notes or observations"
    )

    # Computed Fields
    # Note: 'transfer_duration' is referenced in views for statistics, but was missing.
    # We add it as a computed Float summarizing hours between transfer_date and now or completion.
    transfer_duration = fields.Float(
        string="Transfer Duration (Hrs)",
        compute="_compute_transfer_duration",
        store=False,
        help="Elapsed hours since transfer date or until completion (if available).",
    )

    # Additional view-referenced analytical / planning fields (placeholders to prevent ParseErrors).
    expected_completion_date = fields.Datetime(
        string="Expected Completion Date",
        help="Planned date/time this custody transfer should be completed.",
        tracking=True,
    )
    actual_completion_date = fields.Datetime(
        string="Actual Completion Date",
        help="When this custody transfer actually completed.",
        readonly=True,
        tracking=True,
    )
    signature_required = fields.Boolean(
        string="Signature Required",
        help="Indicates whether signature capture is required for this transfer.",
        default=False,
    )
    compliance_officer_id = fields.Many2one(
        comodel_name="res.users",
        string="Compliance Officer",
        help="Officer responsible for compliance verification.",
    )
    transfer_distance = fields.Float(
        string="Transfer Distance (km)",
        help="Approximate distance covered during this transfer.",
    )
    transport_method = fields.Selection(
        [
            ("ground", "Ground"),
            ("air", "Air"),
            ("marine", "Marine"),
            ("internal", "Internal Move"),
        ],
        string="Transport Method",
        help="Primary transport method used for this transfer.",
    )
    carrier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Carrier",
        help="External carrier or logistics provider.",
    )
    item_count = fields.Integer(
        string="Item Count",
        help="Number of discrete items involved in this transfer (informational).",
    )
    total_weight = fields.Float(
        string="Total Weight (kg)",
        help="Estimated total weight of items transferred.",
    )
    special_handling_required = fields.Boolean(
        string="Special Handling Required",
        help="Indicates special handling or environmental controls are required.",
        default=False,
    )
    transfer_status = fields.Selection(
        [
            ("on_time", "On Time"),
            ("delayed", "Delayed"),
            ("early", "Early"),
        ],
        string="Transfer Status",
        help="Performance status relative to schedule.",
    )
    tracking_number = fields.Char(
        string="Tracking Number",
        help="External tracking / reference number if shipped with a carrier.",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id.id if self.env.company.currency_id else False,
        help="Currency for monetary fields in this record.",
    )

    insurance_value = fields.Monetary(
        string="Insurance Value",
        currency_field="currency_id",
        help="Declared insurance value for items in transfer.",
    )
    transfer_purpose = fields.Text(
        string="Transfer Purpose",
        help="Purpose and justification for this transfer.",
    )
    special_instructions = fields.Text(
        string="Special Instructions",
        help="Special handling instructions or security requirements.",
    )
    compliance_notes = fields.Text(
        string="Compliance Notes",
        help="Compliance verification details and notes.",
    )
    # Environmental & Event Snapshot Fields (added to satisfy view references that expect
    # these directly on the custody record in addition to event lines). These mirror the
    # structure used on chain.of.custody.event for quick at-a-glance filtering in list / search views.
    event_date = fields.Datetime(
        string="Event Date",
        help="Primary event timestamp for this custody record (used in list/search views).",
    )
    event_type = fields.Selection(
        [
            ("pickup", "Pickup"),
            ("handoff", "Handoff"),
            ("inspection", "Inspection"),
            ("transport", "Transport"),
            ("arrival", "Arrival"),
            ("storage", "Storage"),
            ("exception", "Exception"),
        ],
        string="Event Type",
        help="Categorization of the primary custody event represented by this record.",
    )
    responsible_person = fields.Char(
        string="Responsible Person",
        help="Non-user textual identifier when the responsible individual isn't a system user.",
    )
    location = fields.Char(
        string="Location",
        help="Textual location description captured at the time of custody record creation.",
    )
    signature_verified = fields.Boolean(
        string="Signature Verified",
        help="Indicates that captured signatures have been independently verified.",
        default=False,
    )
    temperature = fields.Float(
        string="Temperature (°C)",
        help="Environmental temperature reading at time of custody action (if applicable).",
    )
    humidity = fields.Float(
        string="Humidity (%)",
        help="Environmental humidity reading at time of custody action (if applicable).",
    )
    notes = fields.Text(
        string="Notes",
        help="General notes entered directly on the custody record (distinct from audit notes).",
    )
    delay_reason = fields.Text(
        string="Delay Reason",
        help="Explanation for any delays encountered.",
    )
    estimated_duration = fields.Float(
        string="Estimated Duration (Hrs)",
        help="Planned estimated duration for this transfer.",
    )
    actual_duration = fields.Float(
        string="Actual Duration (Hrs)",
        help="Actual duration realized (computed or manually entered).",
    )
    transfer_efficiency = fields.Float(
        string="Transfer Efficiency (%)",
        help="Efficiency metric (higher is better).",
    )
    compliance_score = fields.Float(
        string="Compliance Score",
        help="Scored evaluation of compliance processes for this transfer.",
    )
    risk_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Risk Level",
        help="Assessed risk classification for this transfer.",
    )
    # Relationship placeholders for view list displays (One2many) - minimal definitions
    custody_event_ids = fields.One2many(
        comodel_name="chain.of.custody.event",
        inverse_name="custody_id",
        string="Custody Events",
        help="Related custody events (environmental readings, signatures, etc.)",
    )
    transfer_item_ids = fields.One2many(
        comodel_name="chain.of.custody.item",
        inverse_name="custody_id",
        string="Transfer Items",
        help="Items included in this custody transfer.",
    )

    @api.depends("transfer_date", "actual_completion_date", "state")
    def _compute_transfer_duration(self):
        now = fields.Datetime.now()
        for record in self:
            if not record.transfer_date:
                record.transfer_duration = 0.0
                continue
            end_time = record.actual_completion_date or now
            if record.state in ["completed", "verified"] and record.actual_completion_date:
                end_time = record.actual_completion_date
            delta = end_time - record.transfer_date
            record.transfer_duration = max(0.0, delta.total_seconds() / 3600.0)

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
    @api.depends("audit_log_ids")
    def _compute_audit_log_count(self):
        for record in self:
            record.audit_log_count = len(record.audit_log_ids)

    @api.depends("name", "transfer_type", "to_custodian_id")
    def _compute_display_name(self):
        """Compute display name for the custody record."""
        for record in self:
            if record.name:
                selection_dict = dict(record._fields["transfer_type"].selection)
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

                domain = self._build_related_domain(record, ">", record.sequence)
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

            domain = self._build_related_domain(record, ">", record.sequence)
            record.next_transfer_id = self.search(domain, order="sequence asc", limit=1)

    @api.depends("sequence", "container_id", "document_id")
    def _compute_previous_transfer(self):
        """Compute previous transfer in the chain."""
        for record in self:
            if not record.container_id and not record.document_id:
                record.previous_transfer_id = False
                continue

            domain = self._build_related_domain(record, "<", record.sequence)
            record.previous_transfer_id = self.search(
                domain, order="sequence desc", limit=1
            )

    @api.depends("sequence", "container_id", "document_id")
    def _compute_is_final(self):
        """Compute if this is the final transfer."""
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
        """Generate unique custody reference using dynamic sequence."""
        # Pull sequence dynamically from XML-defined sequence (assumes 'chain.of.custody' is defined in data files)
        sequence_value = self.env["ir.sequence"].next_by_code("chain.of.custody")
        if not sequence_value:
            # Fallback to random number if sequence not found (avoids hardcoded "COC" duplication)
            sequence_value = str(random.randint(1000, 9999))
        return f"{self._CUSTODY_PREFIX}-{sequence_value}-{datetime.now().strftime('%Y%m%d')}"

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

    def action_view_audit_logs(self):
        """View audit logs related to this custody record."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Audit Logs"),
            "res_model": "naid.audit.log",
            "view_mode": "list,form",
            "domain": [("custody_id", "=", self.id)],
            "context": {
                "default_custody_id": self.id,
                "default_event_type": "custody_event",
            },
        }

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
        """Return the full chain for the related container/document preserving order.

        Helper used by views / reports. Falls back to empty recordset if no
        related container or document is set (should not normally happen once
        record passes constraints).
        """
        domain = self._build_related_domain(self, None, None)
        if domain:
            # Remove sequence condition for full chain
            domain = [d for d in domain if not (isinstance(d, tuple) and d[0] == "sequence")]
            return self.search(domain, order="sequence, transfer_date")
        return self.env["chain.of.custody"].browse()

    def generate_destruction_certificate(self):
        """Generate destruction certificate for this transfer."""
        self.ensure_one()
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
            # Add error handling for audit log creation
            try:
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
            except Exception as e:
                _logger.warning(f"Failed to create audit log for custody {record.id}: {e}")
            log_messages.append(f"Created custody record: {record.display_name}")
        if log_messages:
            for msg in log_messages:
                _logger.info(msg)
        return records

    def write(self, vals):
        """Override write to add audit logging only for records with tracked field changes."""
        tracked_fields = [
            "state", "transfer_type", "to_custodian_id", "from_custodian_id",
            "transfer_date", "container_id", "document_id", "reason", "security_level",
            "naid_compliant", "authorization_required", "authorized_by_id"
        ]
        changed_records = self.filtered(
            lambda rec: any(
                field in vals and getattr(rec, field, None) != vals[field]
                for field in tracked_fields
            )
        )
        result = super().write(vals)  # Updated for Odoo 18 compatibility
        for record in changed_records:
            self.env["naid.audit.log"].create(
                {
                    "event_type": "custody_updated",
                    "description": f"Custody record updated: {record.display_name}",
                    "user_id": self.env.user.id,
                    "custody_id": record.id,
                    "container_id": record.container_id.id if record.container_id else False,
                    "document_id": record.document_id.id if record.document_id else False,
                }
            )
        return result

    def unlink(self):
        """Override unlink to add audit logging before deletion."""
        for record in self:
            self.env["naid.audit.log"].create(
                {
                    "event_type": "custody_deleted",
                    "description": f"Custody record deleted: {record.display_name}",
                    "user_id": self.env.user.id,
                    "custody_id": record.id,
                    "container_id": record.container_id.id if record.container_id else False,
                    "document_id": record.document_id.id if record.document_id else False,
                }
            )
        return super().unlink()  # Updated for Odoo 18 compatibility

    # Utility Methods
    @api.model
    def get_custody_statistics(self, date_from=None, date_to=None):
        """Get custody transfer statistics."""
        domain = []
        if date_from:
            domain.append(("transfer_date", ">=", date_from))
        if date_to:
            domain.append(("transfer_date", "<=", date_to))

        # Basic statistics: count by transfer type and state
        stats = {
            'total_transfers': self.search_count(domain),
            'by_type': {},
            'by_state': {},
        }
        # Count by transfer type
        for transfer_type, label in dict(self._fields['transfer_type'].selection).items():
            count = self.search_count(domain + [('transfer_type', '=', transfer_type)])
            if count > 0:
                stats['by_type'][label] = count

        # Count by state
        for state, label in dict(self._fields['state'].selection).items():
            count = self.search_count(domain + [('state', '=', state)])
            if count > 0:
                stats['by_state'][label] = count

        return stats

    def _build_related_domain(self, record, operator=None, sequence_value=None):
        """Build domain for related custody records based on container or document.

        Args:
            record: The custody record to build domain for
            operator: Comparison operator for sequence ('>', '<', '=', etc.)
            sequence_value: The sequence value to compare against

        Returns:
            list: Domain filter list for searching related records
        """
        domain = []

        # Ensure we have a valid record with at least one relation
        if not record:
            return domain

        # Build domain based on related container or document
        if record.container_id:
            domain.append(("container_id", "=", record.container_id.id))
        elif record.document_id:
            domain.append(("document_id", "=", record.document_id.id))
        else:
            # If no container or document, return empty domain to avoid broad searches
            _logger.warning(f"Custody record {record.id} has no container_id or document_id for domain building")
            return []

        # Add sequence filter if both operator and value are provided
        if operator is not None and sequence_value is not None:
            # Validate operator is a string and one of the expected values
            if isinstance(operator, str) and operator in ['>', '<', '>=', '<=', '=', '!=']:
                domain.append(("sequence", operator, sequence_value))
            else:
                _logger.warning(f"Invalid operator '{operator}' in _build_related_domain, skipping sequence filter")

        return domain
