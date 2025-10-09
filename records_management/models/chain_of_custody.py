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

# Note: Translation warnings during module loading are expected
# for constraint definitions - this is non-blocking behavior


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

    _name_company_uniq = models.Constraint(
        "unique(name, company_id)",
        "Custody Reference must be unique per company!",
    )

    # Centralized prefix for custody references to avoid mismatches
    _CUSTODY_PREFIX = "COC"

    # Core Identification
    name = fields.Char(
        string="Custody Reference",
        required=True,
        copy=False,
        index=True,
        help="Unique reference for this custody record",
        default=lambda self: "New",
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

    partner_id = fields.Many2one(
        related="department_id.partner_id",
        string="Customer",
        store=True,
        readonly=True,
        help="The customer associated with this custody record's department.",
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
        tracking=True,
        help="New location",
    )

    # Related Records
    container_ids = fields.Many2many(
        comodel_name="records.container",
        relation="chain_of_custody_container_rel",
        column1="custody_id",
        column2="container_id",
        string="Containers",
        help="Containers involved in this custody transfer",
    )

    document_ids = fields.Many2many(
        comodel_name="records.document",
        relation="chain_of_custody_document_rel",
        column1="custody_id",
        column2="document_id",
        string="Documents",
        help="Documents involved in this custody transfer",
    )


    # Event History (reintroduced to satisfy compute dependency in chain.of.custody.event)
    custody_event_ids = fields.One2many(
        comodel_name="chain.of.custody.event",
        inverse_name="custody_id",
        string="Custody Events",
        help="Chronological list of custody events linked to this record for audit and duration computations.",
    )

    # State and Status
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Status of the custody record",
    )

    # Notes and Attachments
    notes = fields.Text(string="Notes", help="Additional notes about the transfer")

    # Signature and Verification
    signature = fields.Binary(string="Signature", copy=False, help="Digital signature of the receiving custodian")
    signed_by = fields.Char(string="Signed By", copy=False, help="Name of the person who signed")
    signed_on = fields.Datetime(string="Signed On", copy=False, help="Date and time of signature")

    # Audit Fields
    create_date = fields.Datetime(string="Created On", readonly=True)
    create_uid = fields.Many2one("res.users", string="Created By", readonly=True)
    write_date = fields.Datetime(string="Last Updated On", readonly=True)
    write_uid = fields.Many2one("res.users", string="Last Updated By", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("New"):
                vals["name"] = self._get_next_custody_reference()
        return super().create(vals_list)

    def _get_next_custody_reference(self):
        """Generate a unique custody reference."""
        return f"{self._CUSTODY_PREFIX}-{self.env['ir.sequence'].next_by_code('chain.of.custody') or ''}"

    @api.depends("name", "transfer_type")
    def _compute_display_name(self):
        for record in self:
            transfer_type_display = (
                dict(self._fields["transfer_type"].selection).get(record.transfer_type)
                or ""
            )
            record.display_name = f"{record.name} ({transfer_type_display})"


    def action_start(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft custody records can be started."))
        self.write({"state": "in_progress"})

    def action_complete(self):
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Only in-progress custody records can be completed."))
        self.write({"state": "completed"})

    def action_cancel(self):
        self.ensure_one()
        self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({"state": "draft"})
