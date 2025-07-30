# -*- coding: utf-8 -*-
"""
NAID Certificate Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class NaidCertificate(models.Model):
    """
    NAID Certificate Management
    NAID AAA destruction certificates and compliance tracking
    """

    _name = "naid.certificate"
    _description = "NAID Certificate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "issue_date desc, name"
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(
        string="Certificate Number",
        required=True,
        tracking=True,
        default=lambda self: _("New"),
        copy=False,
    )
    description = fields.Text(string="Certificate Description", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Certifying Officer",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ==========================================
    # CERTIFICATE DETAILS
    # ==========================================
    certificate_type = fields.Selection(
        [
            ("destruction", "Destruction Certificate"),
            ("transport", "Transport Certificate"),
            ("storage", "Storage Certificate"),
            ("compliance", "Compliance Certificate"),
        ],
        string="Certificate Type",
        required=True,
        tracking=True,
    )

    issue_date = fields.Date(
        string="Issue Date", default=fields.Date.today, required=True, tracking=True
    )
    valid_until = fields.Date(string="Valid Until", tracking=True)

    # ==========================================
    # CUSTOMER INFORMATION
    # ==========================================
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        domain=[("is_company", "=", True)],
    )

    # ==========================================
    # DESTRUCTION DETAILS
    # ==========================================
    destruction_date = fields.Date(string="Destruction Date", tracking=True)
    destruction_method = fields.Selection(
        [
            ("shredding", "Shredding"),
            ("pulping", "Pulping"),
            ("incineration", "Incineration"),
            ("degaussing", "Degaussing"),
            ("physical_destruction", "Physical Destruction"),
        ],
        string="Destruction Method",
        tracking=True,
    )

    total_weight = fields.Float(string="Total Weight (lbs)", tracking=True)
    total_volume = fields.Float(string="Total Volume (cubic ft)", tracking=True)

    # ==========================================
    # NAID COMPLIANCE
    # ==========================================
    naid_compliance_level = fields.Selection(
        [("aaa", "NAID AAA"), ("aa", "NAID AA"), ("a", "NAID A")],
        string="NAID Compliance Level",
        default="aaa",
        tracking=True,
    )

    witness_present = fields.Boolean(string="Witness Present", tracking=True)
    witness_name = fields.Char(string="Witness Name", tracking=True)
    witness_signature = fields.Binary(string="Witness Signature")

    # ==========================================
    # VERIFICATION
    # ==========================================
    verified = fields.Boolean(string="Verified", tracking=True)
    verified_by = fields.Many2one("res.users", string="Verified By", tracking=True)
    verification_date = fields.Date(string="Verification Date", tracking=True)

    # ==========================================
    # RELATED RECORDS
    # ==========================================
    shredding_service_id = fields.Many2one(
        "shredding.service", string="Shredding Service", ondelete="set null"
    )

    # ==========================================
    # CERTIFICATE FILES
    # ==========================================
    certificate_pdf = fields.Binary(string="Certificate PDF")
    certificate_filename = fields.Char(string="Certificate Filename")

    # ==========================================
    # STATUS
    # ==========================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("issued", "Issued"),
            ("verified", "Verified"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        required=True,
    )

    # ==========================================
    # NOTES
    # ==========================================
    notes = fields.Text(string="Notes", tracking=True)
    compliance_notes = fields.Text(string="Compliance Notes", tracking=True)

    # ==========================================
    # WORKFLOW METHODS
    # ==========================================
    def action_issue_certificate(self):
        """Issue the certificate"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft certificates can be issued"))

        self.write({"state": "issued"})
        self.message_post(body=_("Certificate issued"))

    def action_verify_certificate(self):
        """Verify the certificate"""
        self.ensure_one()
        if self.state != "issued":
            raise UserError(_("Only issued certificates can be verified"))

        self.write(
            {
                "state": "verified",
                "verified": True,
                "verified_by": self.env.user.id,
                "verification_date": fields.Date.today(),
            }
        )
        self.message_post(body=_("Certificate verified"))

    def action_archive_certificate(self):
        """Archive the certificate"""
        self.ensure_one()
        if self.state != "verified":
            raise UserError(_("Only verified certificates can be archived"))

        self.write({"state": "archived"})
        self.message_post(body=_("Certificate archived"))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number"""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "naid.certificate"
                ) or _("New")
        return super().create(vals_list)
