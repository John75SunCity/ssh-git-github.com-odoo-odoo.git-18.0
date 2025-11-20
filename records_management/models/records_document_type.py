import logging
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class RecordsDocumentType(models.Model):
    _name = 'records.document.type'
    _description = 'Records Document Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS - Core Information
    # ============================================================================
    name = fields.Char(string="Document Type Name", required=True, tracking=True)
    code = fields.Char(string="Code", required=True, copy=False, readonly=True, default=lambda self: "New")
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('deprecated', 'Deprecated'),
        ('archived', 'Archived'),
    ], string="Status", default='draft', required=True, tracking=True)

    category = fields.Selection([
        ('financial', 'Financial'),
        ('legal', 'Legal'),
        ('hr', 'Human Resources'),
        ('medical', 'Medical'),
        ('compliance', 'Compliance'),
        ('government', 'Government'),
        ('corporate', 'Corporate'),
        ('technical', 'Technical'),
        ('operational', 'Operational'),
        ('other', 'Other'),
    ], string="Category", required=True, default='other', tracking=True)

    # ============================================================================
    # FIELDS - Hierarchy and Relations
    # ============================================================================
    parent_type_id = fields.Many2one(comodel_name='records.document.type', string="Parent Type", ondelete='cascade')
    child_type_ids = fields.One2many(comodel_name='records.document.type', inverse_name='parent_type_id', string="Child Types")
    document_ids = fields.One2many(comodel_name='records.document', inverse_name='document_type_id', string="Documents")
    container_ids = fields.One2many(comodel_name='records.container', inverse_name='document_type_id', string="Containers")
    retention_rule_ids = fields.One2many(comodel_name='records.retention.rule', inverse_name='document_type_id', string="Retention Rules")

    # ============================================================================
    # FIELDS - Security & Compliance
    # ============================================================================
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal Use Only'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
        ('top_secret', 'Top Secret'),
    ], string="Confidentiality Level", default='internal', required=True, tracking=True)

    naid_compliance = fields.Boolean(string="NAID AAA Compliance Required", default=True, help="Ensures NAID standards are met for destruction.")
    hipaa_protected = fields.Boolean(string="HIPAA Protected Health Information (PHI)", help="Indicates if the document type contains PHI.")
    sox_compliance = fields.Boolean(string="SOX Compliance Required", help="Sarbanes-Oxley compliance requirements apply.")
    gdpr_applicable = fields.Boolean(string="GDPR Data Subject", help="Indicates if the document type contains personal data under GDPR.")
    regulatory_requirements = fields.Text(string="Specific Regulatory Requirements")

    # ============================================================================
    # FIELDS - Retention & Destruction
    # ============================================================================
    default_retention_years = fields.Integer(string="Default Retention (Years)", default=7, help="Default retention period if no policy is set.")
    requires_legal_hold = fields.Boolean(string="Subject to Legal Hold", help="If checked, documents of this type can be placed on legal hold.")
    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('pulping', 'Pulping'),
        ('incineration', 'Incineration'),
        ('digital_wipe', 'Digital Wipe'),
    ], string="Default Destruction Method", default='shredding')

    # ============================================================================
    # FIELDS - Physical & Handling
    # ============================================================================
    max_box_weight = fields.Float(string="Max Box Weight (lbs)", default=50.0, help="Maximum allowed weight for a standard box of this document type.")
    storage_requirements = fields.Text(string="Storage Requirements", help="Special storage conditions, e.g., climate control.")
    handling_instructions = fields.Text(string="Handling Instructions")

    # ============================================================================
    # FIELDS - Configuration
    # ============================================================================
    approval_required = fields.Boolean(string="Approval Required for Changes", default=False)
    indexing_required = fields.Boolean(string="Indexing Required", default=True)
    barcode_required = fields.Boolean(string="Barcode Required", default=True)
    digital_copy_required = fields.Boolean(string="Digital Copy Required", help="A digital scan must be created for documents of this type.")
    encryption_required = fields.Boolean(string="Encryption Required", help="Digital copies must be encrypted.")
    retention_policy_id = fields.Many2one(comodel_name='records.retention.policy', string='Retention Policy', help="Default retention policy for this document type")

    # ============================================================================
    # FIELDS - Computed & Analytics
    # ============================================================================
    document_count = fields.Integer(compute='_compute_related_counts', string="Document Count", store=True)
    child_count = fields.Integer(compute='_compute_related_counts', string="Child Type Count", store=True)
    container_count = fields.Integer(compute='_compute_related_counts', string="Container Count", store=True)
    effective_retention_years = fields.Integer(compute='_compute_effective_retention', string="Effective Retention (Years)", store=True)

    # ============================================================================
    # FIELDS - Additional Unique Fields (Consolidated and Cleaned)
    # ============================================================================
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer')
    department_id = fields.Many2one(comodel_name='records.department', string='Customer Department')
    category_id = fields.Many2one(comodel_name='records.category', string='Record Category')
    retention_type = fields.Selection([('permanent', 'Permanent'), ('temporary', 'Temporary')], string='Retention Type')
    retention_event = fields.Selection([('creation', 'Creation Date'), ('end_of_year', 'End of Fiscal Year'), ('last_activity', 'Last Activity Date')], string='Retention Event')

    # Legal Hold Management
    is_legal_hold = fields.Boolean(string='Legal Hold')
    legal_hold_reason = fields.Text(string='Legal Hold Reason')

    # Action Management
    next_action_date = fields.Date(string='Next Action Date')
    next_action = fields.Selection([('review', 'Review'), ('destroy', 'Destroy')], string='Next Action')
    destruction_approver_ids = fields.Many2many('res.users', 'document_type_destruction_approver_rel', 'document_type_id', 'user_id', string='Destruction Approvers')

    # Configuration
    is_default = fields.Boolean(string='Is Default Type')
    audit_log_ids = fields.One2many(comodel_name='records.audit.log', inverse_name='document_type_id', string='Audit Logs')
    related_regulation = fields.Char(string='Related Regulation')
    storage_location_id = fields.Many2one(comodel_name='stock.location', string='Storage Location', domain="[('usage', '=', 'internal')]")

    # Template System
    is_template = fields.Boolean(string='Is Template')
    template_id = fields.Many2one(comodel_name='records.document.type', string='Template')
    type_level = fields.Integer(string='Type Level', compute='_compute_type_level', store=True)

    # Geographic Scope
    is_global = fields.Boolean(string='Is Global')
    country_ids = fields.Many2many('res.country', 'document_type_country_rel', 'document_type_id', 'country_id', string='Applicable Countries')
    state_ids = fields.Many2many('res.country.state', 'document_type_state_rel', 'document_type_id', 'state_id', string='Applicable States')
    tag_ids = fields.Many2many('records.tag', 'document_type_tag_rel', 'document_type_id', 'tag_id', string='Tags')

    # Priority and Review
    priority = fields.Selection([('0', 'Low'), ('1', 'Medium'), ('2', 'High')], string='Priority')
    review_cycle = fields.Integer(string='Review Cycle (days)')
    last_review_date = fields.Date(string='Last Review Date')
    last_review_by_id = fields.Many2one(comodel_name='res.users', string='Last Reviewed By')
    next_review_date = fields.Date(string='Next Review Date')
    next_reviewer_id = fields.Many2one(comodel_name='res.users', string='Next Reviewer')

    # Approval Workflow
    is_approved = fields.Boolean(string='Is Approved')
    approved_by_id = fields.Many2one(comodel_name='res.users', string='Approved By')
    approval_date = fields.Date(string='Approval Date')
    rejection_reason = fields.Text(string='Rejection Reason')
    is_rejected = fields.Boolean(string='Is Rejected')
    rejected_by_id = fields.Many2one(comodel_name='res.users', string='Rejected By')
    rejection_date = fields.Date(string='Rejection Date')

    # Status Tracking (Simplified)
    is_pending_approval = fields.Boolean(string='Pending Approval')
    is_pending_review = fields.Boolean(string='Pending Review')
    is_under_legal_hold = fields.Boolean(string='Under Legal Hold')
    is_expired = fields.Boolean(string='Is Expired')
    expiration_date = fields.Date(string='Expiration Date')
    is_overdue = fields.Boolean(string='Is Overdue')
    overdue_days = fields.Integer(string='Overdue Days')

    # Compliance Tracking
    is_compliant = fields.Boolean(string='Is Compliant')
    compliance_status = fields.Selection([('compliant', 'Compliant'), ('non_compliant', 'Non-Compliant'), ('unknown', 'Unknown')], string='Compliance Status')
    compliance_notes = fields.Text(string='Compliance Notes')
    compliance_check_date = fields.Date(string='Compliance Check Date')
    compliance_checker_id = fields.Many2one(comodel_name='res.users', string='Compliance Checker')

    # Version Management (Simplified)
    is_versioned = fields.Boolean(string='Is Versioned')
    version = fields.Integer(string='Version')
    is_latest_version = fields.Boolean(string='Is Latest Version')
    superseded_by_id = fields.Many2one(comodel_name='records.document.type', string='Superseded By')
    supersede_id = fields.Many2one(comodel_name='records.document.type', string='Supersede')

    # Effective Dates
    effective_date = fields.Date(string='Effective Date')
    ineffective_date = fields.Date(string='Ineffective Date')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('document_ids', 'child_type_ids', 'container_ids')
    def _compute_related_counts(self):
        for record in self:
            record.document_count = len(record.document_ids)
            record.child_count = len(record.child_type_ids)
            record.container_count = len(record.container_ids)

    @api.depends('retention_policy_id.retention_years', 'default_retention_years')
    def _compute_effective_retention(self):
        for record in self:
            if record.retention_policy_id:
                record.effective_retention_years = record.retention_policy_id.retention_years
            else:
                record.effective_retention_years = record.default_retention_years or 0

    @api.depends('parent_type_id')
    def _compute_type_level(self):
        """Compute the hierarchical level of the document type."""
        for record in self:
            level = 0
            parent = record.parent_type_id
            while parent and level < 10:  # Prevent infinite loops
                level += 1
                parent = parent.parent_type_id
            record.type_level = level

    # ============================================================================
    # ORM OVERRIDES (CRUD)
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('records.document.type') or _('New')
            if vals.get("confidentiality_level") in ["restricted", "top_secret"]:
                vals["encryption_required"] = True
        records = super().create(vals_list)
        for record in records:
            record.message_post(body=_("Document type '%s' created.") % record.name)
        return records

    def write(self, vals):
        if "state" in vals:
            for record in self:
                # Only validate if state is actually changing
                if record.state != vals["state"]:
                    record._validate_state_transition(vals["state"])
        if vals.get("confidentiality_level") in ["restricted", "top_secret"]:
            vals["encryption_required"] = True
        res = super().write(vals)
        if 'retention_policy_id' in vals or 'default_retention_years' in vals:
            self.action_handle_retention_changes()
        return res

    def unlink(self):
        for record in self:
            if record.document_ids:
                raise UserError(_("Cannot delete document type '%s' as it is used by %d documents. Please archive it instead.") % (record.name, record.document_count))
            if record.child_type_ids:
                raise UserError(_("Cannot delete document type '%s' as it has child types. Please reassign them first.") % record.name)
        return super().unlink()

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        self.ensure_one()
        self.write({"state": "active", "active": True})
        self.message_post(body=_("Document type activated."))

    def action_deprecate(self):
        self.ensure_one()
        self.write({"state": "deprecated"})
        self.message_post(body=_("Document type deprecated. No new documents of this type can be created."))

    def action_archive(self):
        self.ensure_one()
        if self.document_ids.filtered(lambda d: d.active):
            raise UserError(_("Cannot archive type '%s' with active documents.") % self.name)
        self.write({"active": False, "state": "archived"})

    def action_view_documents(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Documents for %s") % self.name,
            "res_model": "records.document",
            "view_mode": "tree,form,kanban",
            "domain": [("document_type_id", "=", self.id)],
            "context": {"default_document_type_id": self.id},
        }

    def action_handle_retention_changes(self):
        """Handle retention policy changes and notify affected documents."""
        self.ensure_one()
        if self.document_count > 0:
            message = _("Retention policy change for document type '%s' affects %d existing documents.") % (self.name, self.document_count)
            self.message_post(body=message)
            _logger.warning("Retention policy changed for %s affecting %d documents", self.name, self.document_count)

    # ============================================================================
    # BUSINESS LOGIC & VALIDATION
    # ============================================================================
    def get_retention_date(self, creation_date):
        self.ensure_one()
        if not creation_date or not self.effective_retention_years:
            return None

        # Convert date to datetime if needed for calculation
        if isinstance(creation_date, str):
            creation_date = datetime.strptime(creation_date, '%Y-%m-%d').date()
        elif isinstance(creation_date, datetime):
            creation_date = creation_date.date()

        # Calculate retention end date by adding years (approximating with 365 days per year)
        retention_days = self.effective_retention_years * 365
        retention_date = creation_date + timedelta(days=retention_days)

        return retention_date

    def is_eligible_for_destruction(self, document_date):
        self.ensure_one()
        retention_end_date = self.get_retention_date(document_date)
        return retention_end_date and fields.Date.today() >= retention_end_date

    def _validate_state_transition(self, new_state):
        self.ensure_one()
        valid_transitions = {
            'draft': ['active', 'archived'],
            'active': ['deprecated', 'archived'],
            'deprecated': ['archived'],
            'archived': ['active'],
        }
        if self.state in valid_transitions and new_state not in valid_transitions.get(self.state, []):
            raise UserError(_("Invalid state transition from '%s' to '%s'.") % (self.state, new_state))

    @api.constrains('default_retention_years')
    def _check_retention_years(self):
        for record in self:
            if record.default_retention_years < 0:
                raise ValidationError(_("Default retention years cannot be negative."))
            if record.default_retention_years > 100:
                raise ValidationError(_("Default retention years cannot exceed 100 years for practical purposes."))

    @api.constrains('parent_type_id')
    def _check_parent_type_recursion(self):
        if not self._check_m2o_recursion('parent_type_id'):
            raise ValidationError(_('You cannot create recursive document types.'))

    @api.constrains('max_box_weight')
    def _check_max_box_weight(self):
        for record in self:
            if record.max_box_weight < 0:
                raise ValidationError(_("Maximum box weight cannot be negative."))

    @api.constrains('confidentiality_level', 'encryption_required')
    def _check_security_consistency(self):
        for record in self:
            if record.confidentiality_level in ["restricted", "top_secret"] and not record.encryption_required:
                raise ValidationError(_("Documents with '%s' confidentiality must have encryption required.") % record.confidentiality_level)
