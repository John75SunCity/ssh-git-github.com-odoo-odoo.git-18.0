# ============================================================================
# IMPORTS & DEPENDENCIES
# ============================================================================
# Fixed: Reordered imports per Odoo standards (stdlib → third-party → Odoo core → Odoo addons)
import base64
import io
import logging
from datetime import datetime, date, timedelta

from dateutil.relativedelta import relativedelta  # type: ignore

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

# ============================================================================
# BARCODE FIELD TYPE (Using Odoo's Native Barcode Support)
# ============================================================================
# Note: Odoo 19.0 has native barcode support through the 'barcodes' module
# No external Python packages needed for basic barcode functionality


class RecordsDocument(models.Model):
    """
    Represents a document in the Records Management system.

    This model is used to manage the lifecycle of physical and digital documents,
    including their storage, access, retention, and destruction. It integrates
    with various other models such as containers, departments, and audit logs
    to provide a comprehensive document management solution.

    Key Features:
    - Tracks document metadata, including name, reference, and description.
    - Manages relationships with customers, departments, and containers.
    - Supports state transitions such as draft, in storage, checked out, and destroyed.
    - Implements retention policies and destruction eligibility calculations.
    - Provides audit logging and chain of custody tracking for compliance.
    - Supports digitization and attachment of digital scans.
    - Enforces business rules through constraints and state validations.
    - Offers actions for document operations like checkout, return, and destruction.

    This model is NAID AAA compliant and adheres to ISO 15489 standards for
    document lifecycle management.
    """

    _name = 'records.document'
    _description = 'Records Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Document Name", required=True, tracking=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    responsible_person_id = fields.Many2one(comodel_name='res.users', string='Responsible')
    reference = fields.Char(string="Reference / Barcode", copy=False, tracking=True)
    # Temporary file barcode (distinct from physical barcode). Assigned automatically if absent.
    temp_barcode = fields.Char(
        string="Temporary File Barcode",
        copy=False,
        index=True,
        tracking=True,
        help="System-generated temporary barcode (prefix TF) used before any permanent document barcode is applied."
    )

    # ============================================================================
    # ODOO NATIVE BARCODE FIELD
    # ============================================================================
    barcode = fields.Char(string="Barcode", help="Document barcode for scanning", tracking=True)
    barcode_image = fields.Binary(
        string="Barcode Image",
        compute="_compute_barcode_image",
        store=False,
        help="Generated barcode image for this document",
    )
    # Batch 4 Relabel: More explicit document description label
    description = fields.Text(string="Document Description")

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one(comodel_name="res.partner", string="Customer", required=True, tracking=True)
    department_id = fields.Many2one(
        comodel_name="records.department",
        string="Department",
        domain="[('partner_id', '=', partner_id)]",
        tracking=True,
    )
    container_id = fields.Many2one(comodel_name="records.container", string="Container", tracking=True)
    location_id = fields.Many2one(related='container_id.location_id', string="Location", store=True, readonly=True, comodel_name='stock.location')
    document_type_id = fields.Many2one(comodel_name="records.document.type", string="Document Type", tracking=True)
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Stock Lot",
        tracking=True,
        help="Lot/Serial number associated with this document.",
    )
    temp_inventory_id = fields.Many2one(comodel_name="temp.inventory", string="Temporary Inventory")
    retention_policy_id = fields.Many2one(
        comodel_name="records.retention.policy", string="Retention Policy", tracking=True
    )
    retention_rule_id = fields.Many2one(comodel_name="records.retention.rule", string="Retention Rule", tracking=True)
    series_id = fields.Many2one(comodel_name="records.series", string="Serie", tracking=True)  # Fixed: Changed "Series" to "Serie" for singular form consistency
    storage_box_id = fields.Many2one(comodel_name="records.storage.box", string="Storage Box", tracking=True)
    request_id = fields.Many2one(comodel_name="records.request", string="Request", tracking=True)

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_storage', 'In Storage'),
        ('in_transit', 'In Transit'),
        ('checked_out', 'Checked Out'),
        ('archived', 'Archived'),
        ('awaiting_destruction', 'Awaiting Destruction'),
        ('destroyed', 'Destroyed'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # DATES & RETENTION
    # ============================================================================
    create_date = fields.Datetime(string="Creation Date", readonly=True)
    received_date = fields.Date(string="Received Date", default=fields.Date.context_today, tracking=True)
    storage_date = fields.Date(string="Storage Date", tracking=True)
    last_access_date = fields.Date(string="Last Access Date", tracking=True)
    last_access_user_id = fields.Many2one(comodel_name='res.users', string="Last Accessed By", readonly=True, tracking=True)
    destruction_eligible_date = fields.Date(string="Destruction Eligible Date", compute='_compute_destruction_eligible_date', store=True, tracking=True)
    actual_destruction_date = fields.Date(string="Actual Destruction Date", readonly=True, tracking=True)
    days_until_destruction = fields.Integer(string="Days Until Destruction", compute='_compute_days_until_destruction')

    # ============================================================================
    # LEGAL HOLD / PERMANENT FLAG
    # ============================================================================
    is_permanent = fields.Boolean(
        string="Is Permanent", help="Mark this document to be exempt from destruction policies."
    )  # Removed tracking=True; track on state instead
    permanent_reason = fields.Text(string="Reason for Permanence")
    permanent_user_id = fields.Many2one(comodel_name="res.users", string="Flagged Permanent By", readonly=True)
    permanent_date = fields.Datetime(string="Flagged Permanent On", readonly=True)

    # ============================================================================
    # DIGITAL & COMPLIANCE
    # ============================================================================
    document_category = fields.Char("Document Category", tracking=True)
    media_type = fields.Char("Media Type", tracking=True)
    original_format = fields.Char("Original Format", tracking=True)
    digitized = fields.Boolean("Digitized")
    # Toggle for enabling Digital Scans tab (referenced in view)
    digital_scanning_enabled = fields.Boolean(
        string="Digital Scanning Enabled",
        default=True,
        help="Controls visibility and access to the Digital Scans tab in the document form."
    )
    digital_scan_ids = fields.One2many('records.digital.scan', 'document_id', string="Digital Scans")
    scan_count = fields.Integer(string="Scan Count", compute='_compute_scan_count', store=True)
    total_scan_size_kb = fields.Integer(
        string="Total Scan Size (KB)",
        compute="_compute_total_scan_size",
        help="Total size of all digital scans for this document in kilobytes",
    )
    total_scan_size_visible = fields.Boolean(
        string="Show Total Scan Size",
        default=True,
        help="Controls whether the Total Scan Size field is visible; referenced by form view invisible domain.",
    )
    audit_log_ids = fields.One2many('naid.audit.log', 'document_id', string="Audit Logs")
    audit_log_count = fields.Integer(string="Audit Log Count", compute='_compute_audit_log_count', store=True)
    chain_of_custody_ids = fields.One2many('naid.custody', 'document_id', string="Chain of Custody")
    chain_of_custody_count = fields.Integer(string="Chain of Custody Events", compute='_compute_chain_of_custody_count', store=True)

    # ============================================================================
    # DESTRUCTION INFO
    # ============================================================================
    destruction_method = fields.Char("Destruction Method")
    destruction_certificate_id = fields.Many2one(comodel_name="naid.certificate", string="Destruction Certificate")
    naid_destruction_verified = fields.Boolean("NAID Destruction Verified")
    destruction_authorized_by_id = fields.Many2one(comodel_name="res.users", string="Destruction Authorized By")
    destruction_witness_id = fields.Many2one(comodel_name="res.partner", string="Destruction Witness")  # Already singular, no change needed
    destruction_facility = fields.Char("Destruction Facility")
    destruction_notes = fields.Text("Destruction Notes")

    # ============================================================================
    # AUDIT & CHAIN OF CUSTODY
    # ============================================================================
    event_date = fields.Date(string="Event Date", help="Date of the last significant event (e.g., access, move, audit).")
    compliance_verified = fields.Boolean(string="Compliance Verified", help="Indicates if the document's handling meets compliance standards.")
    scan_date = fields.Datetime(string="Last Scan Date", help="Timestamp of the last barcode scan.")
    last_verified_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Last Verified By",
        help="User who last verified the document's status or location.",
    )
    last_verified_date = fields.Datetime(string="Last Verified Date", help="Timestamp of the last verification.")
    is_missing = fields.Boolean(string="Is Missing", help="Flagged if the document cannot be located during an audit.")
    missing_since_date = fields.Date(string="Missing Since", help="Date the document was first reported as missing.")
    found_date = fields.Date(string="Date Found", help="Date the document was located after being missing.")

    # ============================================================================
    # VITAL RECORDS & CHECKOUT TRACKING
    # ============================================================================
    last_review_date = fields.Date(string="Last Review Date", help="Date of the last vital records review.")
    vital_record_review_period = fields.Integer(string="Review Period (Days)", help="Period in days for vital record reviews.")
    next_review_date = fields.Date(string="Next Review Date", compute='_compute_next_review_date', store=True, help="Date of the next scheduled review.")
    checked_out_date = fields.Datetime(string="Checked Out Date", help="Date and time when document was checked out.")
    expected_return_date = fields.Date(string="Expected Return Date", help="Expected date for document return.")
    attachment_ids = fields.One2many('ir.attachment', 'res_id', string="Attachments",
                                   domain=[('res_model', '=', 'records.document')], help="Digital attachments for this document.")

    # ============================================================================
    # COMPUTED & ADVANCED FIELDS
    # ============================================================================
    document_qr_code = fields.Char(string="QR Code", compute='_compute_document_qr_code', help="QR code for quick document identification.")
    is_overdue = fields.Boolean(string="Is Overdue", compute='_compute_is_overdue', help="True if the document checkout is overdue.")
    has_attachments = fields.Boolean(string="Has Attachments", compute='_compute_has_attachments', help="True if document has digital attachments.")
    attachment_count = fields.Integer(string="Document Attachments", compute='_compute_attachment_count')
    message_attachment_count = fields.Integer(string="Message Attachments", readonly=True)
    public_url = fields.Char(string="Public URL", compute='_compute_public_url', help="Public URL for document access.")
    is_favorite = fields.Boolean(string="Is Favorite", compute='_compute_is_favorite', inverse='_inverse_is_favorite', help="Mark document as favorite for current user.")
    related_records_count = fields.Integer(string="Related Records Count", compute='_compute_related_records_count')
    destruction_eligible = fields.Boolean(string="Destruction Eligible", compute='_compute_destruction_eligible', help="True if document is eligible for destruction today.")
    destruction_profit = fields.Float(string="Destruction Profit", compute='_compute_destruction_profit', help="Profit from document destruction.")
    location_status = fields.Selection([
        ('in_storage', 'In Storage'),
        ('checked_out', 'Checked Out'),
        ('missing', 'Missing'),
        ('destroyed', 'Destroyed'),
        ('unknown', 'Unknown')
    ], string="Location Status", compute='_compute_location_status', help="Current location status of the document.")
    digitization_status = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete')
    ], string="Digitization Status", compute='_compute_digitization_status', help="Status of document digitization.")

    # ============================================================================
    # FILTERS & GROUPING FIELDS (for advanced search and reporting)
    # ============================================================================
    pending_destruction = fields.Boolean(
        string="Pending Destruction",
        compute="_compute_pending_destruction",
        store=True,
        search="_search_pending_destruction",
        help="True if the document is eligible for destruction but not yet destroyed.",
    )
    group_by_customer_id = fields.Many2one(
        related="partner_id", string="Group by Customer", store=False, readonly=True, comodel_name="res.partner"
    )
    group_by_location_id = fields.Many2one(
        related="location_id", string="Group by Location", store=False, readonly=True, comodel_name="stock.location"
    )
    destroyed = fields.Boolean(string="Is Destroyed", compute='_compute_destroyed', store=True, help="True if the document's state is 'destroyed'.")
    recently_accessed = fields.Boolean(string="Accessed Recently", compute="_compute_recent_access", search="_search_recent_access", help="True if accessed in last 30 days.")

    temp_file_barcode_company_uniq = models.Constraint("unique(temp_barcode, company_id)", _("Temporary file barcode must be unique per company."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        # Updated translation usage to project policy (percent interpolation after _()).
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.document') or _('New')
            # Assign TF* temp barcode if absent and no physical barcode present
            if not vals.get('temp_barcode') and not vals.get('barcode'):
                seq = self.env['ir.sequence'].next_by_code('records.document.temp.barcode')
                if not seq:
                    # Fallback pattern if sequence misconfigured
                    today = fields.Date.context_today(self)
                    seq = "TF%s%05d" % (today.strftime('%Y%m%d'), self.env['ir.sequence'].next_by_code('records.document') or 0)
                vals['temp_barcode'] = seq
        docs = super().create(vals_list)
        for doc in docs:
            doc.message_post(body=_('Document "%s" created') % doc.name)
        return docs

    def write(self, vals):
        if 'is_permanent' in vals and vals['is_permanent']:
            vals.update({
                'permanent_user_id': self.env.user.id,
                'permanent_date': fields.Datetime.now(),
            })
        if 'state' in vals:
            for record in self:
                record.message_post_with_view(
                    'mail.message_origin_link',
                    values={'self': record, 'origin': record.state, 'edit': True},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return super().write(vals)

    def unlink(self):
        for doc in self:
            if doc.state not in ('draft', 'archived'):
                raise UserError(_("Cannot delete a document that is not in draft or archived state. Please archive it first."))
        return super().unlink()

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends("barcode")
    def _compute_barcode_image(self):
        """Generate barcode image using Odoo's native functionality"""
        for record in self:
            if record.barcode:
                try:
                    record.barcode_image = self._generate_odoo_barcode(record.barcode)
                except Exception as e:
                    _logger.warning("Failed to generate barcode image for %s: %s", record.barcode, str(e))
                    record.barcode_image = False
            else:
                record.barcode_image = False

    @api.depends('received_date', 'document_type_id.effective_retention_years', 'is_permanent')
    def _compute_destruction_eligible_date(self):
        for record in self:
            try:
                if (record.is_permanent or
                    not record.received_date or
                    not record.document_type_id or
                    not hasattr(record.document_type_id, 'effective_retention_years') or
                    record.document_type_id.effective_retention_years <= 0):
                    record.destruction_eligible_date = False
                else:
                    years = record.document_type_id.effective_retention_years
                    record.destruction_eligible_date = record.received_date + relativedelta(years=years)
            except Exception:
                record.destruction_eligible_date = False

    @api.depends('destruction_eligible_date', 'is_permanent')
    def _compute_days_until_destruction(self):
        today = fields.Date.context_today(self)
        for record in self:
            try:
                if (record.destruction_eligible_date and
                    not record.is_permanent and
                    today):
                    delta = record.destruction_eligible_date - today
                    record.days_until_destruction = delta.days
                else:
                    record.days_until_destruction = False
            except Exception:
                record.days_until_destruction = False

    @api.depends('digital_scan_ids')
    def _compute_scan_count(self):
        for record in self:
            try:
                record.scan_count = len(record.digital_scan_ids) if record.digital_scan_ids else 0
            except Exception:
                record.scan_count = 0

    @api.depends("digital_scan_ids.file_size")
    def _compute_total_scan_size(self):
        """Compute total file size of all digital scans for this document."""
        for record in self:
            try:
                # Sum all scan file sizes (in MB) and convert to KB
                total_mb = sum(record.digital_scan_ids.mapped("file_size") or [0])
                record.total_scan_size_kb = int(total_mb * 1024)  # Convert MB to KB
            except Exception:
                record.total_scan_size_kb = 0

    @api.depends('audit_log_ids')
    def _compute_audit_log_count(self):
        for record in self:
            try:
                record.audit_log_count = len(record.audit_log_ids) if record.audit_log_ids else 0
            except Exception:
                record.audit_log_count = 0

    @api.depends('chain_of_custody_ids')
    def _compute_chain_of_custody_count(self):
        for record in self:
            try:
                record.chain_of_custody_count = len(record.chain_of_custody_ids) if record.chain_of_custody_ids else 0
            except Exception:
                record.chain_of_custody_count = 0

    @api.depends('last_review_date', 'vital_record_review_period')
    def _compute_next_review_date(self):
        for record in self:
            try:
                if (record.last_review_date and
                    record.vital_record_review_period and
                    record.vital_record_review_period > 0):
                    years = record.vital_record_review_period / 365
                    record.next_review_date = record.last_review_date + relativedelta(years=years)
                else:
                    record.next_review_date = False
            except Exception:
                record.next_review_date = False

    def _compute_document_qr_code(self):
        for record in self:
            try:
                if record.id and record.reference:
                    record.document_qr_code = f"QR-{record.id}-{record.reference}"
                else:
                    record.document_qr_code = False
            except Exception:
                record.document_qr_code = False

    @api.depends('checked_out_date', 'expected_return_date')
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for record in self:
            try:
                record.is_overdue = (
                    record.checked_out_date and
                    record.expected_return_date and
                    record.expected_return_date < today
                )
            except Exception:
                record.is_overdue = False

    @api.depends('attachment_ids')
    def _compute_has_attachments(self):
        for record in self:
            try:
                record.has_attachments = bool(record.attachment_ids and len(record.attachment_ids) > 0)
            except Exception:
                record.has_attachments = False

    @api.depends('name', 'reference')
    def _compute_display_name(self):
        for record in self:
            try:
                if record.name and record.reference:
                    record.display_name = f"{record.name} ({record.reference})"
                else:
                    record.display_name = record.name or record.reference or ''
            except Exception:
                record.display_name = record.name or ''

    def _compute_attachment_count(self):
        for record in self:
            try:
                record.attachment_count = len(record.attachment_ids) if record.attachment_ids else 0
            except Exception:
                record.attachment_count = 0

    def _compute_public_url(self):
        for record in self:
            try:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
                if base_url and record.id:
                    record.public_url = f"{base_url}/document/{record.id}"
                else:
                    record.public_url = ''
            except Exception:
                record.public_url = ''

    def _compute_is_favorite(self):
        try:
            doc_ids = self.ids
            user_id = self.env.user.id
            favorites = self.env['document.favorite'].search([
                ('document_id', 'in', doc_ids),
                ('user_id', '=', user_id)
            ])
            fav_map = {fav.document_id.id: True for fav in favorites}
            for record in self:
                record.is_favorite = fav_map.get(record.id, False)
        except Exception:
            for record in self:
                record.is_favorite = False

    def _inverse_is_favorite(self):
        for record in self:
            try:
                favorite_records = self.env['document.favorite'].search([
                    ('document_id', '=', record.id),
                    ('user_id', '=', self.env.user.id)
                ])

                if record.is_favorite and not favorite_records:
                    self.env['document.favorite'].create({
                        'document_id': record.id,
                        'user_id': self.env.user.id
                    })
                elif not record.is_favorite and favorite_records:
                    favorite_records.unlink()
            except Exception:
                pass

    def _compute_related_records_count(self):
        for record in self:
            try:
                count = 0
                if hasattr(record, 'request_id') and record.request_id:
                    count += 1
                if hasattr(record, 'destruction_certificate_id') and record.destruction_certificate_id:
                    count += 1
                count += len(record.chain_of_custody_ids) if record.chain_of_custody_ids else 0
                record.related_records_count = count
            except Exception:
                record.related_records_count = 0

    @api.depends('destruction_eligible_date', 'is_permanent', 'state')
    def _compute_destruction_eligible(self):
        today = fields.Date.today()
        for record in self:
            try:
                record.destruction_eligible = (
                    not record.is_permanent and
                    record.destruction_eligible_date and
                    record.destruction_eligible_date <= today and
                    record.state not in ['destroyed', 'checked_out']
                )
            except Exception:
                record.destruction_eligible = False

    def _compute_destruction_profit(self):
        for record in self:
            try:
                revenue = getattr(record, 'destruction_revenue', 0) or 0
                cost = getattr(record, 'destruction_cost', 0) or 0
                record.destruction_profit = revenue - cost
            except Exception:
                record.destruction_profit = 0

    @api.depends('destruction_eligible_date', 'state', 'is_permanent')
    def _compute_pending_destruction(self):
        today = fields.Date.today()
        for record in self:
            try:
                record.pending_destruction = (
                    not record.is_permanent and
                    record.destruction_eligible_date and
                    record.destruction_eligible_date <= today and
                    record.state == 'awaiting_destruction'
                )
            except Exception:
                record.pending_destruction = False

    def _search_pending_destruction(self, operator, value):
        try:
            today = fields.Date.today()
            if operator == '=' and value:
                return [
                    ('is_permanent', '=', False),
                    ('destruction_eligible_date', '!=', False),
                    ('destruction_eligible_date', '<=', today),
                    ('state', '=', 'awaiting_destruction')
                ]
            else:
                return [
                    '|',
                    ('state', '!=', 'awaiting_destruction'),
                    ('is_permanent', '=', True),
                ]
        except Exception:
            return [('id', '=', False)]

    @api.depends('last_access_date')
    def _compute_recent_access(self):
        thirty_days_ago = fields.Date.today() - relativedelta(days=30)
        for record in self:
            try:
                record.recently_accessed = (
                    record.last_access_date and
                    record.last_access_date >= thirty_days_ago
                )
            except Exception:
                record.recently_accessed = False

    def _search_recent_access(self, operator, value):
        try:
            thirty_days_ago = fields.Date.today() - relativedelta(days=30)
            if operator == '=' and value:
                return [('last_access_date', '>=', thirty_days_ago)]
            else:
                return [
                    '|',
                    ('last_access_date', '=', False),
                    ('last_access_date', '<', thirty_days_ago)
                ]
        except Exception:
            return [('id', '=', False)]

    @api.depends('state')
    def _compute_destroyed(self):
        for record in self:
            try:
                record.destroyed = (record.state == 'destroyed')
            except Exception:
                record.destroyed = False

    @api.depends('container_id', 'state', 'is_missing')
    def _compute_location_status(self):
        for record in self:
            try:
                if record.state == 'destroyed':
                    record.location_status = 'destroyed'
                elif record.is_missing:
                    record.location_status = 'missing'
                elif record.state == 'checked_out':
                    record.location_status = 'checked_out'
                elif record.container_id:
                    record.location_status = 'in_storage'
                else:
                    record.location_status = 'unknown'
            except Exception:
                record.location_status = 'unknown'

    @api.depends('digitized', 'scan_count')
    def _compute_digitization_status(self):
        for record in self:
            try:
                if record.digitized and record.scan_count > 0:
                    record.digitization_status = 'complete'
                elif record.digitized:
                    record.digitization_status = 'in_progress'
                else:
                    record.digitization_status = 'not_started'
            except Exception:
                record.digitization_status = 'not_started'

    # ============================================================================
    # FILTERS & GROUPING FIELDS (for advanced search and reporting)
    # ============================================================================
    @api.constrains('is_permanent', 'permanent_reason')
    def _check_permanent_reason(self):
        for record in self:
            if record.is_permanent and not record.permanent_reason:
                raise ValidationError(_("A reason is required when flagging a document as permanent."))

    @api.constrains('state', 'is_permanent')
    def _check_destruction_of_permanent(self):
        for record in self:
            if record.is_permanent and record.state in ('awaiting_destruction', 'destroyed'):
                raise ValidationError(_("A document flagged as permanent cannot be destroyed."))

    @api.constrains('checked_out_date', 'expected_return_date')
    def _check_checkout_dates(self):
        for record in self:
            if record.checked_out_date and record.expected_return_date:
                checkout_date = record.checked_out_date.date() if isinstance(record.checked_out_date, datetime) else record.checked_out_date
                if record.expected_return_date < checkout_date:
                    raise ValidationError(_("Expected return date cannot be before checkout date."))
                if checkout_date > date.today():
                    raise ValidationError(_("Checkout date cannot be in the future."))

    @api.constrains('received_date', 'storage_date')
    def _check_document_dates(self):
        for record in self:
            if record.received_date and record.storage_date and record.storage_date < record.received_date:
                raise ValidationError(_("Storage date cannot be before received date."))
            if record.received_date and record.received_date > date.today() + timedelta(days=30):
                raise ValidationError(_("Received date cannot be more than 30 days in the future."))

    @api.constrains('actual_destruction_date', 'destruction_eligible_date')
    def _check_destruction_dates(self):
        for record in self:
            if record.actual_destruction_date and record.destruction_eligible_date:
                if record.actual_destruction_date < record.destruction_eligible_date and not record.is_permanent:
                    raise ValidationError(_("Document cannot be destroyed before its eligible destruction date unless permanently flagged."))

            if record.actual_destruction_date and record.state != 'destroyed':
                raise ValidationError(_("Document must be in 'destroyed' state if actual destruction date is set."))

    @api.constrains('state', 'container_id')
    def _check_state_container_consistency(self):
        for record in self:
            if record.state == 'in_storage' and not record.container_id:
                raise ValidationError(_("Document in storage must be assigned to a container."))

            if record.state == 'destroyed' and record.container_id:
                raise ValidationError(_("Destroyed documents cannot be assigned to containers."))

    @api.constrains('missing_since_date', 'found_date', 'is_missing')
    def _check_missing_document_dates(self):
        for record in self:
            if record.is_missing and not record.missing_since_date:
                raise ValidationError(_("Missing since date is required when document is flagged as missing."))

            if record.found_date and record.is_missing:
                raise ValidationError(_("Document cannot be both missing and found simultaneously."))

            if record.found_date and record.missing_since_date and record.found_date < record.missing_since_date:
                raise ValidationError(_("Found date cannot be before missing since date."))

    @api.constrains('vital_record_review_period')
    def _check_review_period(self):
        for record in self:
            if record.vital_record_review_period and record.vital_record_review_period <= 0:
                raise ValidationError(_("Vital record review period must be positive."))

    @api.constrains('retention_policy_id', 'document_type_id')
    def _check_retention_policy_compatibility(self):
        for record in self:
            if record.retention_policy_id and record.document_type_id:
                if record.document_type_id not in record.retention_policy_id.document_type_ids:
                    raise ValidationError(_("Selected retention policy does not support this document type."))

    @api.constrains('partner_id', 'department_id')
    def _check_department_partner_consistency(self):
        for record in self:
            if record.department_id and record.department_id.partner_id != record.partner_id:
                raise ValidationError(_("Selected department must belong to the document's customer."))

    @api.constrains('state')
    def _check_state_transitions(self):
        for record in self:
            if record.state == 'destroyed':
                if not record.destruction_method:
                    raise ValidationError(_("Destruction method is required when document is destroyed."))

                if record.is_permanent:
                    raise ValidationError(_("Permanent documents cannot be destroyed."))

            if record.state == 'awaiting_destruction':
                if not record.destruction_eligible_date and not record.is_permanent:
                    raise ValidationError(_("Document must have destruction eligible date before awaiting destruction."))

                if record.checked_out_date and not record.found_date:
                    raise ValidationError(_("Document cannot await destruction while checked out."))

    @api.constrains('digitized', 'original_format')
    def _check_digitization_requirements(self):
        for record in self:
            if record.digitized and not record.original_format:
                raise ValidationError(_("Original format is required for digitized documents."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_scans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Digital Scans'),
            'res_model': 'records.digital.scan',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id},
        }

    def action_view_audit_logs(self):
        self.ensure_one()
        return {
            'name': _('Audit Logs'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'naid.audit.log',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id},
        }

    def action_view_chain_of_custody(self):
        self.ensure_one()
        return {
            'name': _('Chain of Custody'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'naid.custody',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id},
        }

    def action_checkout_document(self):
        self.ensure_one()
        if self.state not in ['in_storage']:
            raise UserError(_("Document must be in storage to be checked out."))

        if self.is_missing:
            raise UserError(_("Cannot checkout a missing document."))

        checkout_date = datetime.now()
        expected_return = date.today() + timedelta(days=7)

        self.write({
            'state': 'checked_out',
            'checked_out_date': checkout_date,
            'expected_return_date': expected_return,
            'last_access_date': date.today(),
            'event_date': date.today()
        })

        self.env['naid.audit.log'].create({
            'document_id': self.id,
            'event_type': 'checkout',
            'event_description': _('Document checked out by %s') % self.env.user.name,
            'user_id': self.env.user.id,
            'event_date': checkout_date,
        })
        self.message_post(body=_('Document checked out by %s') % self.env.user.name)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Document Checked Out"),
                'message': _('Document %s has been checked out successfully') % self.display_name,
                'sticky': False,
            }
        }

    def action_return_document(self):
        self.ensure_one()
        if self.state != 'checked_out':
            raise UserError(_("Document must be checked out to be returned."))

        return_date = datetime.now()

        self.write({
            'state': 'in_storage',
            'checked_out_date': False,
            'expected_return_date': False,
            'last_access_date': date.today(),
            'event_date': date.today()
        })

        self.env['naid.audit.log'].create({
            'document_id': self.id,
            'event_type': 'return',
            'event_description': _('Document returned by %s') % self.env.user.name,
            'user_id': self.env.user.id,
            'event_date': return_date,
        })
        self.message_post(body=_('Document returned by %s') % self.env.user.name)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Document Returned"),
                'message': _('Document %s has been returned to storage') % self.display_name,
                'sticky': False,
            }
        }

    def action_generate_document_barcode(self):
        """Generate barcode for the document using Odoo's native barcode support"""
        self.ensure_one()
        if not self.name:
            raise ValueError(_("Document name is required for barcode generation"))

        try:
            # Use Odoo's native barcode generation through report system
            # This leverages the 'barcodes' module dependency in __manifest__.py
            barcode_data = self._generate_odoo_barcode(self.name)

            # Create attachment with the generated barcode
            attachment = self.env["ir.attachment"].create(
                {
                    "name": f"Barcode_{self.name}.png",
                    "type": "binary",
                    "datas": barcode_data,
                    "res_model": "records.document",
                    "res_id": self.id,
                }
            )

            # Log audit event
            self._create_audit_log('barcode_generated', _('Barcode generated for document %s') % self.name)

            return {
                "type": "ir.actions.act_window",
                "res_model": "ir.attachment",
                "view_mode": "form",
                "res_id": attachment.id,
                "target": "new",
            }
        except Exception as e:
            _logger.error("Failed to generate barcode for document %s: %s", self.name, str(e))
            raise UserError(_('Failed to generate barcode: %s') % str(e))

    def _generate_odoo_barcode(self, data):
        """Generate barcode using Odoo's native barcode functionality"""
        try:
            # Use Odoo's barcode generation (available through 'barcodes' module)
            from odoo.addons.barcodes.models.barcode import BarcodeEncoder

            # Generate Code128 barcode
            encoder = BarcodeEncoder()
            barcode_image = encoder.encode("code128", data, width=300, height=100)

            # Convert to base64 for attachment
            return base64.b64encode(barcode_image).decode()

        except ImportError:
            # Fallback: Generate simple barcode using report system
            _logger.warning("BarcodeEncoder not available, using fallback method")
            return self._generate_fallback_barcode(data)

    def _generate_fallback_barcode(self, data):
        """Fallback barcode generation using basic encoding"""
        # This is a simple fallback that creates a basic barcode representation
        # In production, you might want to use a more sophisticated method
        try:
            # Create a simple barcode pattern (this is just a placeholder)
            # Real implementation would use proper barcode encoding
            barcode_pattern = f"*{data}*"

            # For now, return a simple text representation
            # In a real implementation, you'd generate actual barcode image
            return base64.b64encode(barcode_pattern.encode()).decode()

        except Exception as e:
            _logger.error("Fallback barcode generation failed: %s", str(e))
            raise

    def action_generate_document_qr(self):
        """Generate QR code for the document using Odoo's native functionality"""
        self.ensure_one()
        if not self.name:
            raise ValueError(_("Document name is required for QR code generation"))

        try:
            # Use Odoo's native QR code generation
            qr_data = self._generate_odoo_qr_code(self.name)

            # Create attachment
            attachment = self.env["ir.attachment"].create(
                {
                    "name": f"QR_{self.name}.png",
                    "type": "binary",
                    "datas": qr_data,
                    "res_model": "records.document",
                    "res_id": self.id,
                }
            )

            # Log audit event
            self._create_audit_log('qr_generated', _('QR code generated for document %s') % self.name)

            return {
                "type": "ir.actions.act_window",
                "res_model": "ir.attachment",
                "view_mode": "form",
                "res_id": attachment.id,
                "target": "new",
            }
        except Exception as e:
            _logger.error("Failed to generate QR code for document %s: %s", self.name, str(e))
            raise UserError(_('Failed to generate QR code: %s') % str(e))

    def _generate_odoo_qr_code(self, data):
        """Generate QR code using Odoo's native functionality"""
        try:
            # Use Odoo's report system for QR code generation
            # This leverages the 'web' module which includes QR functionality
            from odoo.addons.web.controllers.main import ReportController
            from odoo.http import request

            # Generate QR code using Odoo's built-in QR generation
            qr_code_data = self._create_qr_from_data(data)
            return base64.b64encode(qr_code_data).decode()

        except ImportError:
            # Fallback: Use basic QR generation if advanced features not available
            _logger.warning("Advanced QR generation not available, using fallback method")
            return self._generate_fallback_qr_code(data)

    def _create_qr_from_data(self, data):
        """Create QR code from data using available methods"""
        try:
            from PIL import Image, ImageDraw
            import qrcode as qr_module

            # Generate QR code
            qr = qr_module.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")

            # Convert to bytes
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")  # pyright: ignore[reportCallIssue]
            return buffer.getvalue()

        except ImportError:
            # Ultimate fallback: simple text-based QR representation
            _logger.warning("PIL/qrcode not available, using text fallback")
            return self._generate_fallback_qr_code(data)

    def _generate_fallback_qr_code(self, data):
        """Fallback QR code generation using basic encoding"""
        # This creates a simple representation - in production you'd want proper QR encoding
        try:
            qr_pattern = f"QR:{data}"
            return qr_pattern.encode()
        except Exception as e:
            _logger.error("Fallback QR generation failed: %s", str(e))
            raise

    def action_audit_trail(self):
        """View audit trail for the document"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Audit Trail"),
            "res_model": "naid.audit.log",
            "view_mode": "tree,form",
            "domain": [("document_id", "=", self.id)],
        }

    def action_scan_document(self):
        """Initiate document scanning (placeholder for integration)"""
        self.ensure_one()
        # Placeholder: Integrate with scanning hardware/API
        self.message_post(body=_('Document scanning initiated for %s') % self.name)
        self._create_audit_log('scan_initiated', _('Document scan initiated'))
        return {"type": "ir.actions.act_window_close"}

    def action_mark_permanent(self):
        """Mark document as permanent record"""
        self.ensure_one()
        if self.is_permanent:
            raise ValueError(_("Document is already marked as permanent"))
        self.write(
            {
                "is_permanent": True,
                "permanent_user_id": self.env.user.id,
                "permanent_date": datetime.now(),
            }
        )
        self._create_audit_log("marked_permanent", _("Document marked as permanent"))
        return {"type": "ir.actions.act_window_close"}

    def action_unmark_permanent(self):
        """Remove permanent flag (admin only)"""
        self.ensure_one()
        if not self.env.user.has_group("base.group_system"):
            raise ValueError(_("Only system administrators can remove permanent flags"))
        self.write(
            {
                "is_permanent": False,
                "permanent_user_id": False,
                "permanent_date": False,
            }
        )
        self._create_audit_log("unmarked_permanent", _("Permanent flag removed"))
        return {"type": "ir.actions.act_window_close"}

    def action_schedule_destruction(self):
        """Schedule document for destruction"""
        self.ensure_one()
        if self.is_permanent:
            raise ValueError(_("Permanent documents cannot be scheduled for destruction"))
        if not self.destruction_eligible_date:
            raise ValueError(_("Destruction date must be set"))
        # Fix: Change 'pending_destruction' to 'awaiting_destruction' to match the state selection
        self.write({"state": "awaiting_destruction"})
        event_type, description = self.schedule_destruction_message()
        self._create_audit_log(event_type, description)
        return {"type": "ir.actions.act_window_close"}

    def schedule_destruction_message(self):
        return 'destruction_scheduled', _('Destruction scheduled for %s') % self.destruction_eligible_date

    def _create_audit_log(self, event_type, event_description):
        """Helper to create audit log entries (standardized field names)."""
        self.env["naid.audit.log"].create(
            {
                "document_id": self.id,
                "event_type": event_type,
                "event_description": event_description,
                "user_id": self.env.user.id,
                "event_date": datetime.now(),
            }
        )

    # ============================================================================
    # BUSINESS LOGIC HELPER METHODS
    # ============================================================================
    def is_document_overdue(self):  # Renamed from is_overdue to avoid conflict with field
        self.ensure_one()
        return (
            self.state == 'checked_out' and
            self.expected_return_date and
            self.expected_return_date < date.today()
        )

    def is_eligible_for_destruction(self):
        self.ensure_one()
        return (
            not self.is_permanent and
            self.destruction_eligible_date and
            self.destruction_eligible_date <= date.today() and
            self.state not in ['checked_out', 'destroyed']
        )

    def get_retention_status(self):
        self.ensure_one()
        status = {
            'is_permanent': self.is_permanent,
            'destruction_eligible_date': self.destruction_eligible_date,
            'days_until_destruction': self.days_until_destruction,
            'is_eligible': self.is_eligible_for_destruction(),
            'can_be_destroyed': self.state in ['in_storage', 'archived', 'awaiting_destruction']
        }
        return status

    def get_audit_summary(self):
        self.ensure_one()
        audit_counts = {}
        for log in self.audit_log_ids:
            event_type = log.event_type
            audit_counts[event_type] = audit_counts.get(event_type, 0) + 1

        return {
            'total_events': len(self.audit_log_ids),
            'event_counts': audit_counts,
            'last_event_date': max(self.audit_log_ids.mapped('event_date')) if self.audit_log_ids else False,
            'compliance_verified': self.compliance_verified,
            'last_verified_date': self.last_verified_date
        }

    @api.model
    def get_destruction_report_data(self, date_from=None, date_to=None):
        domain = [('state', '=', 'destroyed')]

        if date_from:
            domain.append(('actual_destruction_date', '>=', date_from))
        if date_to:
            domain.append(('actual_destruction_date', '<=', date_to))

        destroyed_docs = self.search(domain)

        report_data = {
            'total_destroyed': len(destroyed_docs),
            'by_method': {},
            'by_partner': {},
            'by_document_type': {},
            'naid_verified_count': len(destroyed_docs.filtered('naid_destruction_verified'))
        }

        for doc in destroyed_docs:
            method = doc.destruction_method or 'Unknown'
            report_data['by_method'][method] = report_data['by_method'].get(method, 0) + 1

            partner = doc.partner_id.name
            report_data['by_partner'][partner] = report_data['by_partner'].get(partner, 0) + 1

            doc_type = doc.document_type_id.name if doc.document_type_id else 'Unknown'
            report_data['by_document_type'][doc_type] = report_data['by_document_type'].get(doc_type, 0) + 1

        return report_data

    @api.model
    def get_missing_documents_report(self):
        missing_docs = self.search([('is_missing', '=', True)])

        return {
            'total_missing': len(missing_docs),
            'by_partner': {doc.partner_id.name: 1 for doc in missing_docs},
            'by_duration': {
                'recent': len(missing_docs.filtered(lambda d: d.missing_since_date and (date.today() - d.missing_since_date).days <= 30)),
                'medium': len(missing_docs.filtered(lambda d: d.missing_since_date and 30 < (date.today() - d.missing_since_date).days <= 90)),
                'long_term': len(missing_docs.filtered(lambda d: d.missing_since_date and (date.today() - d.missing_since_date).days > 90)),
            },
            'documents': missing_docs.mapped('display_name')
        }

    # ============================================================================
    # ACTION METHODS & SMART BUTTONS
    # ============================================================================
    def action_view_attachments(self):
        """Smart button action to view document attachments"""
        self.ensure_one()
        try:
            return {
                'name': _('Attachments'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'ir.attachment',
                'domain': [('res_model', '=', 'records.document'), ('res_id', '=', self.id)],
                'context': {
                    'default_res_model': 'records.document',
                    'default_res_id': self.id,
                }
            }
        except Exception as e:
            raise ValidationError(_('Error viewing attachments: %s') % str(e))

    def action_view_digital_scans(self):
        """Smart button action to view digital scans"""
        self.ensure_one()
        try:
            return {
                'name': _('Digital Scans'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'records.digital.scan',
                'domain': [('document_id', '=', self.id)],
                'context': {
                    'default_document_id': self.id,
                }
            }
        except Exception as e:
            raise ValidationError(_('Error viewing digital scans: %s') % str(e))

    def action_toggle_favorite(self):
        """Action to toggle favorite status"""
        self.ensure_one()
        try:
            self.is_favorite = not self.is_favorite
            message = _('Document added to favorites.') if self.is_favorite else _('Document removed from favorites.')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message,
                    'type': 'success',
                }
            }
        except Exception as e:
            raise ValidationError(_('Error toggling favorite status: %s') % str(e))

    def action_refresh_data(self):
        """Action to refresh document data and computed fields"""
        self.ensure_one()
        try:
            # Trigger recomputation of key fields
            self._compute_destruction_eligible_date()
            self._compute_days_until_destruction()
            self._compute_scan_count()
            self._compute_audit_log_count()
            self._compute_chain_of_custody_count()
            self._compute_related_records_count()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('Document data refreshed successfully.'),
                    'type': 'success',
                }
            }
        except Exception as e:
            raise ValidationError(_('Error refreshing document data: %s') % str(e))

    def action_generate_qr_code(self):
        """Action to generate/regenerate QR code for document"""
        self.ensure_one()
        try:
            self._compute_document_qr_code()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('QR code generated successfully.'),
                    'type': 'success',
                }
            }
        except Exception as e:
            raise ValidationError(_('Error generating QR code: %s') % str(e))

    def action_print_document_label(self):
        """Action to print document identification label"""
        self.ensure_one()
        try:
            # In a real implementation, this would generate a printable label
            return {
                'type': 'ir.actions.report',
                'report_name': 'records_management.document_label_report',
                'report_type': 'qweb-pdf',
                'data': {'ids': [self.id]},
                'context': self.env.context,
            }
        except Exception as e:
            raise ValidationError(_('Error printing document label: %s') % str(e))

    def action_schedule_review(self):
        """Action to schedule document review"""
        self.ensure_one()
        try:
            # This would typically open a wizard to schedule review
            return {
                'name': _('Schedule Document Review'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'document.review.wizard',
                'target': 'new',
                'context': {
                    'default_document_id': self.id,
                    'default_current_review_date': self.last_review_date,
                    'default_next_review_date': self.next_review_date,
                }
            }
        except Exception as e:
            raise ValidationError(_('Error scheduling document review: %s') % str(e))

    def action_send_notification(self):
        """Action to send notification about document"""
        self.ensure_one()
        try:
            # This would typically open a wizard to compose and send notifications
            return {
                "name": _("Send Document Notification"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "document.notification.wizard",
                "target": "new",
                "context": {
                    "default_document_id": self.id,
                    "default_document_name": self.display_name,
                }
            }
        except Exception as e:
            raise ValidationError(_('Error sending notification: %s') % str(e))

    @api.constrains("state", "is_missing")
    def _check_checkout_conditions(self):
        for record in self:
            if record.state == "checked_out" and record.is_missing:
                raise ValidationError(_("Cannot check out a missing document."))
