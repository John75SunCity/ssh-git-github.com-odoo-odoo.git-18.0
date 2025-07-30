# -*- coding: utf-8 -*-
"""
Records Document Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class RecordsDocument(models.Model):
    """
    Records Document Management
    Individual document tracking within records containers
    """

    _name = "records.document"
    _description = "Records Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string="Document Title", required=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Document Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ==========================================
    # DOCUMENT CLASSIFICATION
    # ==========================================
    document_type = fields.Selection(
        [
            ("financial", "Financial Records"),
            ("legal", "Legal Documents"),
            ("personnel", "Personnel Files"),
            ("medical", "Medical Records"),
            ("insurance", "Insurance Documents"),
            ("tax", "Tax Records"),
            ("contracts", "Contracts"),
            ("correspondence", "Correspondence"),
            ("other", "Other"),
        ],
        string="Document Type",
        required=True,
        tracking=True,
    )

    document_type_id = fields.Many2one(
        "records.document.type", string="Document Type Reference", tracking=True
    )
    document_category = fields.Char(string="Document Category", tracking=True)

    confidential = fields.Boolean(string="Confidential", tracking=True)
    classification_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        string="Classification",
        default="internal",
        tracking=True,
    )

    # State management
    state = fields.Selection(
        [
            ("active", "Active"),
            ("pending_destruction", "Pending Destruction"),
            ("destroyed", "Destroyed"),
        ],
        string="State",
        default="active",
        tracking=True,
    )

    # Permanent flag for records that should never be destroyed
    permanent_flag = fields.Boolean(string="Permanent Record", tracking=True)
    permanent_flag_set_by = fields.Many2one(
        "res.users", string="Permanent Flag Set By", tracking=True
    )
    permanent_flag_set_date = fields.Date(
        string="Permanent Flag Set Date", tracking=True
    )

    # ==========================================
    # PHYSICAL PROPERTIES
    # ==========================================
    page_count = fields.Integer(string="Number of Pages", tracking=True)
    document_format = fields.Selection(
        [
            ("paper", "Paper"),
            ("digital", "Digital Scan"),
            ("microfilm", "Microfilm"),
            ("cd_dvd", "CD/DVD"),
            ("usb", "USB Drive"),
        ],
        string="Format",
        default="paper",
        tracking=True,
    )

    # Additional classification fields
    media_type = fields.Selection(
        [
            ("paper", "Paper"),
            ("digital", "Digital"),
            ("microfilm", "Microfilm"),
            ("other", "Other"),
        ],
        string="Media Type",
        default="paper",
        tracking=True,
    )

    original_format = fields.Char(string="Original Format", tracking=True)
    digitized = fields.Boolean(string="Digitized", tracking=True)

    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    container_id = fields.Many2one(
        "records.container", string="Records Container", tracking=True
    )
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        domain=[("is_company", "=", True)],
        tracking=True,
    )
    department_id = fields.Many2one(
        "records.department", string="Department", tracking=True
    )
    retention_policy_id = fields.Many2one(
        "records.retention.policy", string="Retention Policy", tracking=True
    )

    # One2many relationships
    digital_scan_ids = fields.One2many(
        "records.digital.scan", "document_id", string="Digital Scans"
    )

    # ==========================================
    # DATE TRACKING
    # ==========================================
    creation_date = fields.Date(string="Document Date", tracking=True)
    created_date = fields.Date(string="Created Date", tracking=True)
    received_date = fields.Date(
        string="Received Date", default=fields.Date.today, tracking=True
    )
    storage_date = fields.Date(string="Storage Date", tracking=True)
    last_access_date = fields.Date(string="Last Access Date", tracking=True)

    # ==========================================
    # RETENTION AND DISPOSAL
    # ==========================================
    retention_period_years = fields.Integer(
        string="Retention Period (Years)", default=7, tracking=True
    )
    destruction_date = fields.Date(
        string="Scheduled Destruction Date",
        compute="_compute_destruction_date",
        store=True,
    )
    destruction_eligible_date = fields.Date(
        string="Destruction Eligible Date",
        compute="_compute_destruction_date",
        store=True,
    )
    days_until_destruction = fields.Integer(
        string="Days Until Destruction", compute="_compute_days_until_destruction"
    )
    destroyed = fields.Boolean(string="Destroyed", tracking=True)
    destruction_certificate_id = fields.Many2one(
        "naid.certificate", string="Destruction Certificate"
    )

    # ==========================================
    # NOTES
    # ==========================================
    notes = fields.Text(string="Notes", tracking=True)
    special_instructions = fields.Text(string="Special Instructions", tracking=True)
    action_audit_trail = fields.Char(string='Action Audit Trail')
    action_download = fields.Char(string='Action Download')
    action_mark_permanent = fields.Char(string='Action Mark Permanent')
    action_scan_document = fields.Char(string='Action Scan Document')
    action_schedule_destruction = fields.Char(string='Action Schedule Destruction')
    action_type = fields.Selection([], string='Action Type')  # TODO: Define selection options
    action_unmark_permanent = fields.Char(string='Action Unmark Permanent')
    action_view_chain_of_custody = fields.Char(string='Action View Chain Of Custody')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    audit = fields.Char(string='Audit')
    audit_trail_count = fields.Integer(string='Audit Trail Count', compute='_compute_audit_trail_count', store=True)
    audit_trail_ids = fields.One2many('naid.audit.log', 'records_document_id', string='Audit Trail Ids')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    chain_of_custody_count = fields.Integer(string='Chain Of Custody Count', compute='_compute_chain_of_custody_count', store=True)
    chain_of_custody_ids = fields.One2many('naid.chain.custody', 'records_document_id', string='Chain Of Custody Ids')
    compliance_verified = fields.Boolean(string='Compliance Verified', default=False)
    context = fields.Char(string='Context')
    custody_chain = fields.Char(string='Custody Chain')
    destruction = fields.Char(string='Destruction')
    destruction_authorized_by = fields.Char(string='Destruction Authorized By')
    destruction_due = fields.Char(string='Destruction Due')
    destruction_facility = fields.Char(string='Destruction Facility')
    destruction_method = fields.Char(string='Destruction Method')
    destruction_notes = fields.Char(string='Destruction Notes')
    destruction_this_month = fields.Char(string='Destruction This Month')
    destruction_witness = fields.Char(string='Destruction Witness')
    details = fields.Char(string='Details')
    digital = fields.Char(string='Digital')
    event_date = fields.Date(string='Event Date')
    event_type = fields.Selection([], string='Event Type')  # TODO: Define selection options
    file_format = fields.Char(string='File Format')
    file_size = fields.Char(string='File Size')
    group_by_container = fields.Char(string='Group By Container')
    group_by_customer = fields.Char(string='Group By Customer')
    group_by_destruction = fields.Char(string='Group By Destruction')
    group_by_state = fields.Selection([], string='Group By State')  # TODO: Define selection options
    group_by_type = fields.Selection([], string='Group By Type')  # TODO: Define selection options
    help = fields.Char(string='Help')
    location = fields.Char(string='Location')
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    naid_destruction_verified = fields.Boolean(string='Naid Destruction Verified', default=False)
    non_permanent = fields.Char(string='Non Permanent')
    pending_destruction = fields.Char(string='Pending Destruction')
    permanent = fields.Char(string='Permanent')
    recent_access = fields.Char(string='Recent Access')
    res_model = fields.Char(string='Res Model')
    resolution = fields.Char(string='Resolution')
    responsible_person = fields.Char(string='Responsible Person')
    scan_date = fields.Date(string='Scan Date')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    signature_verified = fields.Boolean(string='Signature Verified', default=False)
    storage_location = fields.Char(string='Storage Location')
    timestamp = fields.Char(string='Timestamp')
    view_mode = fields.Char(string='View Mode')

    @api.depends('audit_trail_ids')
    def _compute_audit_trail_count(self):
        for record in self:
            record.audit_trail_count = len(record.audit_trail_ids)

    @api.depends('chain_of_custody_ids')
    def _compute_chain_of_custody_count(self):
        for record in self:
            record.chain_of_custody_count = len(record.chain_of_custody_ids)

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends("received_date", "retention_period_years")
    def _compute_destruction_date(self):
        """Calculate destruction date based on retention period"""
        for record in self:
            if record.received_date and record.retention_period_years:
                from dateutil.relativedelta import relativedelta

                record.destruction_date = record.received_date + relativedelta(
                    years=record.retention_period_years
                )
                record.destruction_eligible_date = record.destruction_date
            else:
                record.destruction_date = False
                record.destruction_eligible_date = False

    @api.depends("destruction_eligible_date")
    def _compute_days_until_destruction(self):
        """Calculate days until destruction"""
        today = fields.Date.today()
        for record in self:
            if record.destruction_eligible_date:
                delta = record.destruction_eligible_date - today
                record.days_until_destruction = delta.days
            else:
                record.days_until_destruction = 0

    # ==========================================
    # ACTION METHODS
    # ==========================================
    def action_mark_destroyed(self):
        """Mark document as destroyed"""
        self.ensure_one()
        self.write({"destroyed": True})
        self.message_post(body=_("Document marked as destroyed"))

    def action_create_destruction_certificate(self):
        """Create destruction certificate"""
        self.ensure_one()
        if not self.destroyed:
            self.write({"destroyed": True})

        cert_vals = {
            "name": f"Destruction Certificate - {self.name}",
            "document_id": self.id,
            "customer_id": self.customer_id.id if self.customer_id else False,
            "destruction_date": fields.Date.today(),
        }

        cert = self.env["naid.certificate"].create(cert_vals)
        self.write({"destruction_certificate_id": cert.id})
        self.message_post(body=_("Destruction certificate created"))

        return {
            "type": "ir.actions.act_window",
            "name": "Destruction Certificate",
            "res_model": "naid.certificate",
            "res_id": cert.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_chain_of_custody(self):
        """View chain of custody for this document"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Chain of Custody - %s" % self.name,
            "res_model": "records.chain.of.custody",
            "domain": [("document_id", "=", self.id)],
            "view_mode": "tree,form",
            "context": {"default_document_id": self.id},
            "target": "current",
        }

    def action_schedule_destruction(self):
        """Schedule document for destruction"""
        self.ensure_one()
        if self.permanent_flag:
            raise ValidationError(
                _("Cannot schedule permanent documents for destruction")
            )

        # Create destruction record
        destruction_vals = {
            "name": f"Destruction - {self.name}",
            "document_id": self.id,
            "customer_id": self.customer_id.id if self.customer_id else False,
            "scheduled_date": self.destruction_eligible_date,
            "state": "scheduled",
        }

        destruction = self.env["naid.destruction.record"].create(destruction_vals)
        self.message_post(body=_("Document scheduled for destruction"))

        return {
            "type": "ir.actions.act_window",
            "name": "Destruction Record",
            "res_model": "naid.destruction.record",
            "res_id": destruction.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_mark_permanent(self):
        """Mark document as permanent (never destroy)"""
        self.ensure_one()
        self.write(
            {
                "permanent_flag": True,
                "permanent_flag_set_by": self.env.user.id,
                "permanent_flag_set_date": fields.Date.today(),
            }
        )
        self.message_post(
            body=_("Document marked as permanent by %s") % self.env.user.name
        )

    def action_unmark_permanent(self):
        """Remove permanent flag from document"""
        self.ensure_one()
        self.write(
            {
                "permanent_flag": False,
                "permanent_flag_set_by": False,
                "permanent_flag_set_date": False,
            }
        )
        self.message_post(body=_("Permanent flag removed by %s") % self.env.user.name)

    def action_scan_document(self):
        """Scan or upload digital copy of document"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Scan Document - %s" % self.name,
            "res_model": "records.digital.scan",
            "view_mode": "form",
            "context": {"default_document_id": self.id},
            "target": "new",
        }

    def action_audit_trail(self):
        """View audit trail for this document"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Audit Trail - %s" % self.name,
            "res_model": "mail.message",
            "domain": [("res_id", "=", self.id), ("model", "=", "records.document")],
            "view_mode": "tree",
            "target": "current",
        }

    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains("retention_period_years")
    def _check_retention_period(self):
        """Validate retention period"""
        for record in self:
            if record.retention_period_years and record.retention_period_years < 0:
                raise ValidationError(_("Retention period cannot be negative"))

    @api.constrains("page_count")
    def _check_page_count(self):
        """Validate page count"""
        for record in self:
            if record.page_count and record.page_count < 0:
                raise ValidationError(_("Page count cannot be negative"))

    @api.depends("received_date", "document_type_id")
    def _compute_destruction_eligible_date(self):
        """Calculate destruction eligible date based on retention policy"""
        for record in self:
            if (
                record.received_date
                and record.document_type_id
                and record.document_type_id.retention_years
            ):
                from dateutil.relativedelta import relativedelta

                record.destruction_eligible_date = record.received_date + relativedelta(
                    years=record.document_type_id.retention_years
                )
            else:
                record.destruction_eligible_date = False
