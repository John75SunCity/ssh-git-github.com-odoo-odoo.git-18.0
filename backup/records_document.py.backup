# -*- coding: utf-8 -*-

Records Document Management Module

This module provides comprehensive document management functionality for the Records Management:
    pass
System. It implements enterprise-grade document lifecycle tracking, metadata management,
and integration with containers, locations, and retention policies.

Key Features
- Document lifecycle management from creation to destruction
- Permanent flag system for legal holds and compliance requirements:
- Retention policy integration with automated compliance tracking
- Container and location relationship management
- Customer document ownership and access control
- State management for document status tracking:
- Integration with audit trails and compliance frameworks

Business Processes
1. Document Creation: Register documents with proper metadata and relationships
2. Lifecycle Tracking: Monitor document status through various lifecycle stages
3. Permanent Flagging: Apply legal holds and permanent retention flags
4. Retention Management: Enforce retention policies and destruction schedules
5. Location Tracking: Track physical and logical document locations
6. Compliance Reporting: Generate reports for audit and regulatory requirements:
Workflow States
- Active: Document is actively managed and accessible
- Archived: Document is archived but still accessible
- Flagged: Document has permanent flag applied (legal hold)
- Destroyed: Document has been permanently destroyed

Technical Implementation
- Mail thread integration for comprehensive audit trails:
- Proper Many2one/One2many relationships with containers and locations
- Computed fields for retention and destruction date calculations:
- Validation methods ensuring data integrity and business rule compliance
- Integration with NAID compliance and audit logging systems

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from odoo import _, api, fields, models

from odoo.exceptions import UserError, ValidationError


class RecordsDocument(models.Model):

        Core Records Document Model

    Represents individual documents within the records management system.
        Provides document lifecycle tracking, metadata management, and
    integration with containers, locations, and retention policies.


    _name = "records.document"
    _description = "Records Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name, create_date desc"
    _rec_name = "name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Document Name",
        required=True,
        tracking=True,
        index=True,
        help="Name or title of the document"
    
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
    
    active = fields.Boolean(
        string="Active", default=True, help="Whether this document is active"
    
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        index=True,
        help="Customer who owns this document"
    
    customer_inventory_id = fields.Many2one(
        "customer.inventory",
        string="Customer Inventory",
        help="Customer inventory record for this document",:
    

        # ============================================================================
    # DOCUMENT DETAILS
        # ============================================================================
    document_type_id = fields.Many2one(
        "records.document.type",
        string="Document Type",
        tracking=True,
        help="Type/category of the document",
    
    description = fields.Text(
        string="Description",
        help="Detailed description of the document",
    
    reference = fields.Char(
        string="Reference Number",
        help="External reference or ID number",
    

        # ============================================================================
    # CUSTOMER AND RELATIONSHIPS
        # ============================================================================
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        help="Customer who owns this document",
    
    container_id = fields.Many2one(
        "records.container",
        string="Container",
        help="Container where this document is stored",
    
    location_id = fields.Many2one(
        "records.location",
        string="Location",
        help="Physical location of the document",
    
    
        # Document Retrieval Items (inverse relationship)
    retrieval_item_ids = fields.One2many(
        "document.retrieval.item", "document_id",
        string="Document Retrieval Items",
        help="Retrieval items that reference this document"
    
    
    temp_inventory_id = fields.Many2one(
        "temp.inventory",
        string="Temporary Inventory",
        help="Temporary inventory location for this document",:
    
    lot_id = fields.Many2one(
        "stock.lot",
        string="Stock Lot",
        help="Associated stock lot for tracking",:
    

        # ============================================================================
    # RETENTION AND LIFECYCLE MANAGEMENT
        # ============================================================================
    retention_policy_id = fields.Many2one(
        "records.retention.policy",
        string="Retention Policy",
        tracking=True,
        help="Retention policy governing this document",
    

        # ============================================================================
    # PERMANENT FLAG FIELDS
        # ============================================================================
    permanent_flag = fields.Boolean(
        string="Permanent Flag",
        default=False,
        tracking=True,
        help="Whether this document has a permanent retention flag applied",
    
    permanent_flag_reason = fields.Selection(
        []
            ("legal_hold", "Legal Hold"),
            ("litigation", "Litigation Support"),
            ("audit_requirement", "Audit Requirement"),
            ("compliance", "Regulatory Compliance"),
            ("historical", "Historical Significance"),
            ("business_critical", "Business Critical"),
            ("custom", "Custom Reason"),
        
        string="Permanent Flag Reason",
        tracking=True,
        help="Reason for applying the permanent flag",:
    
    permanent_flag_date = fields.Datetime(
        string="Permanent Flag Date",
        tracking=True,
        help="Date when the permanent flag was applied",
    
    permanent_flag_user_id = fields.Many2one(
        "res.users",
        string="Flagged By",
        tracking=True,
        help="User who applied the permanent flag",
    

        # ============================================================================
    # STATE MANAGEMENT
        # ============================================================================
    state = fields.Selection(
        []
            ("active", "Active"),
            ("archived", "Archived"),
            ("flagged", "Permanent Flag"),
            ("destroyed", "Destroyed"),
        
        string="Document Status",
        default="active",
        tracking=True,
        help="Current status of the document",
    

        # ============================================================================
    # DATE FIELDS
        # ============================================================================
    received_date = fields.Date(
        string="Received Date",
        default=fields.Date.today,
        tracking=True,
        help="Date when the document was received"
    
    creation_date = fields.Date(
        string="Creation Date",
        default=fields.Date.today,
        tracking=True,
        help="Date when the document record was created"
    
    destruction_eligible_date = fields.Date(
        string="Destruction Eligible Date",
        compute="_compute_destruction_eligible_date",
        store=True,
        help="Date when document becomes eligible for destruction":
    

        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS (REQUIRED)
        # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities"),
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

        # Added by Safe Business Fields Fixer
    digitized = fields.Boolean(string="Digitized", default=False)

        # Added by Safe Business Fields Fixer
    digital_scan_ids = fields.One2many("records.digital.scan", "document_id", string="Digital Scans")

        # Added by Safe Business Fields Fixer
    chain_of_custody_ids = fields.One2many("records.chain.of.custody", "document_id", string="Chain of Custody")

        # Added by Safe Business Fields Fixer
    audit_trail_ids = fields.One2many("naid.audit.log", "document_id", string="Audit Trail")

        # Added by Safe Business Fields Fixer
    compliance_verified = fields.Boolean(string="Compliance Verified", default=False)

        # Added by Safe Business Fields Fixer
    destruction_authorized_by = fields.Many2one("res.users", string="Destruction Authorized By")

        # Added by Safe Business Fields Fixer
    destruction_date = fields.Datetime(string="Destruction Date")

        # Added by Safe Business Fields Fixer
    destruction_method = fields.Char(string="Destruction Method")

        # Added by Safe Business Fields Fixer
    naid_destruction_verified = fields.Boolean(string="NAID Destruction Verified", default=False),
    action_audit_trail = fields.Char(string='Action Audit Trail'),
    action_download = fields.Char(string='Action Download'),
    action_mark_permanent = fields.Char(string='Action Mark Permanent'),
    action_scan_document = fields.Char(string='Action Scan Document'),
    action_schedule_destruction = fields.Char(string='Action Schedule Destruction'),
    action_type = fields.Selection([], string='Action Type')  # TODO: Define selection options
    action_unmark_permanent = fields.Char(string='Action Unmark Permanent'),
    action_view_chain_of_custody = fields.Char(string='Action View Chain Of Custody'),
    audit = fields.Char(string='Audit'),
    audit_trail_count = fields.Integer(string='Audit Trail Count', compute='_compute_audit_trail_count', store=True),
    button_box = fields.Char(string='Button Box'),
    card = fields.Char(string='Card'),
    chain_of_custody_count = fields.Integer(string='Chain Of Custody Count', compute='_compute_chain_of_custody_count', store=True),
    context = fields.Char(string='Context'),
    created_date = fields.Date(string='Created Date'),
    custody_chain = fields.Char(string='Custody Chain'),
    days_until_destruction = fields.Char(string='Days Until Destruction'),
    department_id = fields.Many2one('department', string='Department Id'),
    destroyed = fields.Char(string='Destroyed'),
    destruction = fields.Char(string='Destruction'),
    destruction_certificate_id = fields.Many2one('destruction.certificate', string='Destruction Certificate Id'),
    destruction_due = fields.Char(string='Destruction Due'),
    destruction_facility = fields.Char(string='Destruction Facility'),
    destruction_notes = fields.Char(string='Destruction Notes'),
    destruction_this_month = fields.Char(string='Destruction This Month'),
    destruction_witness = fields.Char(string='Destruction Witness'),
    details = fields.Char(string='Details'),
    digital = fields.Char(string='Digital'),
    document_category = fields.Char(string='Document Category'),
    event_date = fields.Date(string='Event Date'),
    event_type = fields.Selection([], string='Event Type')  # TODO: Define selection options
    file_format = fields.Char(string='File Format'),
    file_size = fields.Char(string='File Size'),
    group_by_container = fields.Char(string='Group By Container'),
    group_by_customer = fields.Char(string='Group By Customer'),
    group_by_destruction = fields.Char(string='Group By Destruction'),
    group_by_state = fields.Selection([], string='Group By State')  # TODO: Define selection options
    group_by_type = fields.Selection([], string='Group By Type')  # TODO: Define selection options
    help = fields.Char(string='Help'),
    last_access_date = fields.Date(string='Last Access Date'),
    location = fields.Char(string='Location'),
    media_type = fields.Selection([], string='Media Type')  # TODO: Define selection options
    non_permanent = fields.Char(string='Non Permanent'),
    notes = fields.Char(string='Notes'),
    original_format = fields.Char(string='Original Format'),
    pending_destruction = fields.Char(string='Pending Destruction'),
    permanent = fields.Char(string='Permanent'),
    permanent_flag_set_by = fields.Char(string='Permanent Flag Set By'),
    permanent_flag_set_date = fields.Date(string='Permanent Flag Set Date'),
    recent_access = fields.Char(string='Recent Access'),
    res_model = fields.Char(string='Res Model'),
    resolution = fields.Char(string='Resolution'),
    responsible_person = fields.Char(string='Responsible Person'),
    scan_date = fields.Date(string='Scan Date'),
    search_view_id = fields.Many2one('search.view', string='Search View Id'),
    signature_verified = fields.Boolean(string='Signature Verified', default=False),
    storage_date = fields.Date(string='Storage Date'),
    storage_location = fields.Char(string='Storage Location'),
    timestamp = fields.Char(string='Timestamp'),
    view_mode = fields.Char(string='View Mode')

    @api.depends('audit_trail_ids')
    def _compute_audit_trail_count(self):
        for record in self:
            record.audit_trail_count = len(record.audit_trail_ids)

    @api.depends('chain_of_custody_ids')
    def _compute_chain_of_custody_count(self):
        for record in self:
            record.chain_of_custody_count = len(record.chain_of_custody_ids)

    # ============================================================================
        # COMPUTE METHODS
    # ============================================================================
    @api.depends('received_date', 'retention_policy_id', 'retention_policy_id.retention_years')
    def _compute_destruction_eligible_date(self):
        """Compute when document becomes eligible for destruction""":
        for record in self:
            if record.received_date and record.retention_policy_id and record.retention_policy_id.retention_years:
                years = record.retention_policy_id.retention_years
                record.destruction_eligible_date = record.received_date.replace(year=record.received_date.year + years)
            else:
                record.destruction_eligible_date = False

    @api.depends('permanent_flag')
    def _compute_state_from_flag(self):
        """Update state based on permanent flag status"""
        for record in self:
            if record.permanent_flag and record.state != 'destroyed':
                record.state = 'flagged'

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_archive_document(self):
        """Archive the document"""

        self.ensure_one()
        if self.permanent_flag:
            raise UserError(_("Cannot archive document with permanent flag applied"))
        self.write({"state": "archived"})
        self.message_post(body=_("Document archived by %s", self.env.user.name))

    def action_activate_document(self):
        """Activate the document"""

        self.ensure_one()
        self.write({"state": "active"})
        self.message_post(body=_("Document activated by %s", self.env.user.name))

    def action_flag_permanent(self):
        """Apply permanent flag to document - opens wizard"""

        self.ensure_one()
        return {}
            'type': 'ir.actions.act_window',
            'name': _('Apply Permanent Flag'),
            'res_model': 'records.permanent.flag.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {}
                'default_document_ids': [(6, 0, [self.id])],
                'default_operation_type': 'apply',
            
        

    def action_remove_permanent_flag(self):
        """Remove permanent flag from document"""

        self.ensure_one()
        if not self.permanent_flag:
            raise UserError(_("Document does not have a permanent flag applied"))

        self.write({)}
            'permanent_flag': False,
            'permanent_flag_reason': False,
            'permanent_flag_date': False,
            'permanent_flag_user_id': False,
            'state': 'active',
        
        self.message_post(body=_("Permanent flag removed by %s", self.env.user.name))

    def action_view_audit_trail(self):
        """View document audit trail"""

        self.ensure_one()
        return {}
            'type': 'ir.actions.act_window',
            'name': _('Document Audit Trail'),
            'res_model': 'mail.message',
            'view_mode': 'tree,form',
            'domain': [('res_id', '=', self.id), ('model', '=', 'records.document')],
            'context': {'default_res_id': self.id, 'default_model': 'records.document'},
        

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains("state", "permanent_flag")
    def _check_state_transitions(self):
        """Validate state transitions and permanent flag consistency"""
        for record in self:
            if record.state == "destroyed" and record.permanent_flag:
                raise ValidationError(_("Cannot destroy document with permanent flag applied"))

            if record.permanent_flag and record.state not in ['flagged', 'active']:
                raise ValidationError(_("Documents with permanent flags must be in 'Active' or 'Flagged' state"))

    @api.constrains('permanent_flag', 'permanent_flag_reason')
    def _check_permanent_flag_reason(self):
        """Ensure permanent flag has a reason when applied"""
        for record in self:
            if record.permanent_flag and not record.permanent_flag_reason:
                raise ValidationError(_("Permanent flag reason is required when flag is applied"))

    # ============================================================================
        # LIFECYCLE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Enhanced create method with audit trail"""
        documents = super().create(vals_list)
        for document in documents:
            document.message_post(body=_("Document created by %s", self.env.user.name))
        return documents

    def write(self, vals):
        """Enhanced write method with audit trail for critical changes""":
        result = super().write(vals)

        # Log critical field changes
        critical_fields = ['state', 'permanent_flag', 'permanent_flag_reason', 'retention_policy_id']
        changed_fields = [field for field in critical_fields if field in vals]:
        if changed_fields:
            for record in self:
                changes = []
                for field in changed_fields:
                    field_label = record._fields[field].string
                    if field in ['state', 'permanent_flag_reason']:
                        old_value = dict(record._fields[field].selection).get(vals[field]) if vals[field] else 'None':
                        changes.append(_("%s changed to %s", field_label, old_value))
                    elif field == 'permanent_flag':
                        changes.append(_("%s: %s", field_label, 'Applied' if vals[field] else 'Removed')):
                    else:
                        changes.append(_("%s updated", field_label))

                if changes:
                    record.message_post(body=_("Document updated by %s: %s", self.env.user.name, ', '.join(changes)))

        return result

