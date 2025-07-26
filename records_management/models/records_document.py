from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import hashlib

class RecordsDocument(models.Model):
    _name = 'records.document'
    _description = 'Document Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name'

    # Core fields
    name = fields.Char('Document Reference', required=True)
    box_id = fields.Many2one(
        'records.box', string='Box', required=True,
        index=True, domain="[('state', '=', 'active')]"
    )
    location_id = fields.Many2one(
        related='box_id.location_id', string='Storage Location', store=True
    )

    # Document metadata
    document_type_id = fields.Many2one(
        'records.document.type', string='Document Type'
    )
    date = fields.Date('Document Date', default=fields.Date.context_today)
    description = fields.Html('Description')
    tags = fields.Many2many('records.tag', 
                           relation='records_document_tag_rel',
                           column1='document_id',
                           column2='tag_id',
                           string='Tags')

    # Date tracking fields
    created_date = fields.Date(
        'Created Date', 
        help='Date when the document was originally created'
    )
    received_date = fields.Date(
        'Received Date',
        help='Date when the document was received by the organization'
    )
    storage_date = fields.Date(
        'Storage Date',
        help='Date when the document was placed in storage'
    )
    last_access_date = fields.Date(
        'Last Access Date',
        help='Date when the document was last accessed'
    )

    # Document classification fields
    document_category = fields.Selection([
        ('financial', 'Financial Records'),
        ('legal', 'Legal Documents'),
        ('personnel', 'Personnel Files'),
        ('operational', 'Operational Records'),
        ('compliance', 'Compliance Documents'),
        ('contracts', 'Contracts & Agreements'),
        ('correspondence', 'Correspondence'),
        ('other', 'Other')
    ], string='Document Category', default='other')

    media_type = fields.Selection([
        ('paper', 'Paper'),
        ('digital', 'Digital'),
        ('microfilm', 'Microfilm'),
        ('microfiche', 'Microfiche'),
        ('magnetic_tape', 'Magnetic Tape'),
        ('optical_disc', 'Optical Disc'),
        ('other', 'Other')
    ], string='Media Type', default='paper')

    original_format = fields.Selection([
        ('letter', 'Letter Size (8.5x11)'),
        ('legal', 'Legal Size (8.5x14)'),
        ('ledger', 'Ledger Size (11x17)'),
        ('a4', 'A4 Size'),
        ('a3', 'A3 Size'),
        ('custom', 'Custom Size'),
        ('digital_file', 'Digital File'),
        ('bound_volume', 'Bound Volume'),
        ('other', 'Other')
    ], string='Original Format', default='letter')

    digitized = fields.Boolean(
        'Digitized',
        default=False,
        help='Whether this document has been digitized'
    )

    # Retention details
    retention_policy_id = fields.Many2one(
        'records.retention.policy', string='Retention Policy'
    )
    retention_date = fields.Date(
        'Retention Date',
        compute='_compute_retention_date', store=True
    )
    expiry_date = fields.Date(
        'Expiry Date',
        help='Date when the document expires and should be reviewed for destruction'
    )
    destruction_eligible_date = fields.Date(
        'Destruction Eligible Date',
        compute='_compute_destruction_eligible_date',
        store=True,
        help='Date when the document becomes eligible for destruction based on retention policy'
    )
    days_to_retention = fields.Integer(
        'Days until destruction', compute='_compute_days_to_retention'
    )
    days_until_destruction = fields.Integer(
        'Days Until Destruction', 
        compute='_compute_days_until_destruction',
        help='Number of days until the document is eligible for destruction'
    )

    # Relations
    partner_id = fields.Many2one('res.partner', string='Related Partner')
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain="[('is_company', '=', True)]",
        index=True
    )
    customer_inventory_id = fields.Many2one(
        'customer.inventory.report',
        string='Customer Inventory Report',
        ondelete='cascade'
    )
    department_id = fields.Many2one(
        'records.department', string='Department', index=True
    )
    container_id = fields.Many2one(
        'box.contents', string='File Folder/Container',
        help='The file folder or container within the box where this document is filed'
    )
    user_id = fields.Many2one(
        'res.users', string='Responsible'
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )

    # File management
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments'
    )
    attachment_count = fields.Integer(
        'Document Attachments Count', compute='_compute_attachment_count'
    )
    
    # Digital document fields
    file_format = fields.Char(
        string='File Format',
        help='Digital file format (e.g., PDF, DOC, JPG)'
    )
    file_size = fields.Float(
        string='File Size (MB)',
        help='Size of the digital file in megabytes'
    )
    scan_date = fields.Datetime(
        string='Scan Date',
        help='Date when the document was digitally scanned'
    )
    signature_verified = fields.Boolean(
        string='Signature Verified',
        default=False,
        help='Whether digital signatures have been verified'
    )
    
    # Audit and custody tracking relationships
    audit_log_ids = fields.One2many(
        'records.audit.log',
        'document_id',
        string='Audit Log Entries',
        help='Audit trail entries for this document'
    )
    chain_of_custody_ids = fields.One2many(
        'records.chain.of.custody',
        'document_id',
        string='Chain of Custody Entries',
        help='Chain of custody entries for this document'
    )
    
    # Computed audit and custody tracking
    audit_trail_count = fields.Integer(
        string='Audit Trail Count',
        compute='_compute_audit_trail_count',
        help='Number of audit trail entries for this document'
    )
    chain_of_custody_count = fields.Integer(
        string='Chain of Custody Count',
        compute='_compute_chain_of_custody_count',
        help='Number of chain of custody entries for this document'
    )

    # Billing fields
    storage_fee = fields.Float(
        string='Storage Fee',
        digits='Product Price',
        help='Monthly storage fee for this document'
    )

    # Status fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('stored', 'Stored'),
        ('retrieved', 'Retrieved'),
        ('returned', 'Returned'),
        ('archived', 'Archived'),
        ('destroyed', 'Destroyed')
    ], string='Status', default='draft')
    checkout_status = fields.Selection([
        ('in_box', 'In Box'),
        ('checked_out', 'Checked Out'),
        ('destroyed', 'Destroyed'),
        ('lost', 'Lost')
    ], string='Checkout Status', default='in_box', tracking=True,
       help='Current checkout status of this document')
    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('pulping', 'Pulping'),
        ('incineration', 'Incineration'),
        ('disintegration', 'Disintegration')
    ], string='Destruction Method')
    active = fields.Boolean(default=True)

    # Security fields
    hashed_content = fields.Char('Content Hash', readonly=True)
    permanent_flag = fields.Boolean(
        'Permanent Record', 
        default=False,
        help="When checked, this document is marked as permanent and excluded from destruction schedules. "
             "Only administrators can remove this flag."
    )
    permanent_flag_set_by = fields.Many2one(
        'res.users', 
        string='Permanent Flag Set By',
        readonly=True,
        help="User who marked this document as permanent"
    )
    permanent_flag_set_date = fields.Datetime(
        'Permanent Flag Set Date',
        readonly=True,
        help="Date and time when permanent flag was set"
    )

    # Related One2many fields for document tracking
    audit_trail_ids = fields.One2many('records.audit.log', 'document_id', string='Audit Trail')
    digital_copy_ids = fields.One2many('records.digital.copy', 'document_id', string='Digital Copies')
    
    # Missing technical and audit fields from view references
    action_type = fields.Selection([
        ('created', 'Created'),
        ('modified', 'Modified'),
        ('accessed', 'Accessed'),
        ('moved', 'Moved'),
        ('destroyed', 'Destroyed')
    ], string='Action Type', help='Type of action performed on document')
    arch = fields.Text(string='View Architecture', help='XML view architecture definition')
    compliance_verified = fields.Boolean(string='Compliance Verified', default=False,
                                        help='Indicates if compliance has been verified')
    context = fields.Text(string='Context', help='View context information')
    event_date = fields.Date(string='Event Date', help='Date when event occurred')
    event_type = fields.Char(string='Event Type', help='Type of event recorded')
    help = fields.Text(string='Help', help='Help text for this record')
    location = fields.Char(string='Location', help='Physical location reference')
    model = fields.Char(string='Model', help='Model name for technical references')
    notes = fields.Text(string='Notes', help='Additional notes or comments')
    res_model = fields.Char(string='Resource Model', help='Resource model name')
    resolution = fields.Text(string='Resolution', help='Resolution or outcome of event')
    responsible_person = fields.Many2one('res.users', string='Responsible Person',
                                        help='Person responsible for this document')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View', help='Search view reference')
    storage_location = fields.Char(string='Storage Location', help='Physical storage location identifier')
    timestamp = fields.Datetime(string='Timestamp', help='Event timestamp')
    view_mode = fields.Char(string='View Mode', help='View mode configuration')

    # Destruction related fields (referenced in views)
    destruction_date = fields.Date('Destruction Date')
    destruction_certificate_id = fields.Many2one('ir.attachment', string='Destruction Certificate')
    naid_destruction_verified = fields.Boolean('NAID Destruction Verified', default=False)
    destruction_authorized_by = fields.Many2one('res.users', string='Destruction Authorized By')
    destruction_witness = fields.Many2one('res.users', string='Destruction Witness')
    destruction_facility = fields.Char('Destruction Facility')
    destruction_notes = fields.Text('Destruction Notes')

    # Compute methods
    @api.depends('date', 'retention_policy_id',
                 'retention_policy_id.retention_years')
    def _compute_retention_date(self):
        for doc in self:
            if (doc.date and doc.retention_policy_id and
                    doc.retention_policy_id.retention_years):
                years = doc.retention_policy_id.retention_years
            else:
                doc.retention_date = False

    @api.depends('retention_date')
    def _compute_destruction_eligible_date(self):
        """Calculate destruction eligible date - typically same as retention date."""
        for doc in self:
            # Destruction eligible date is typically the same as retention date
            # unless there are special business rules
            doc.destruction_eligible_date = doc.retention_date

    @api.depends('retention_date')
    def _compute_days_to_retention(self):
        today = fields.Date.today()
        for doc in self:
            if doc.retention_date:
                delta = (doc.retention_date - today).days
                doc.days_to_retention = max(0, delta)
            else:
                doc.days_to_retention = 0

    @api.depends('destruction_eligible_date')
    def _compute_days_until_destruction(self):
        """Calculate days until destruction eligible date."""
        for doc in self:
            if doc.destruction_eligible_date:
                delta = (doc.destruction_eligible_date - today).days
                doc.days_until_destruction = max(0, delta)
            else:
                doc.days_until_destruction = 0

    # Phase 1 Critical Fields - Added by automated script
    
    @api.depends()
    def _compute_attachment_count(self):
        """Compute the number of attachments for this document"""
        for record in self:
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'records.document'),
                ('res_id', '=', record.id)
            ])
            record.attachment_count = len(attachments)
    
    @api.depends('audit_log_ids')
    def _compute_audit_trail_count(self):
        """Compute number of audit trail entries."""
        for record in self:
            # This would typically link to an audit log model
            record.audit_trail_count = len(record.audit_log_ids) if hasattr(record, 'audit_log_ids') else 0
    
    @api.depends('chain_of_custody_ids')
    def _compute_chain_of_custody_count(self):
        """Compute number of chain of custody entries."""
        for record in self:
            # This would typically link to a chain of custody model
            record.chain_of_custody_count = len(record.chain_of_custody_ids) if hasattr(record, 'chain_of_custody_ids') else 0