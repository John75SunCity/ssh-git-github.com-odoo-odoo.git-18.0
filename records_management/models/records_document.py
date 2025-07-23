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
    tags = fields.Many2many('records.tag', string='Tags')

    # Date tracking fields
    created_date = fields.Date(
        'Created Date', 
        default=fields.Date.context_today,
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
    department_id = fields.Many2one(
        'records.department', string='Department', index=True
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
    chain_of_custody_ids = fields.One2many(
        'records.chain.of.custody', 'document_id',
        string='Chain of Custody Records'
    )
    audit_trail_ids = fields.One2many(
        'records.audit.trail', 'document_id',
        string='Audit Trail Records'
    )
    digital_copy_ids = fields.One2many(
        'records.digital.copy', 'document_id',
        string='Digital Copies'
    )

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
                doc.retention_date = fields.Date.add(doc.date, years=years)
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
        today = fields.Date.today()
        for doc in self:
            if doc.destruction_eligible_date:
                delta = (doc.destruction_eligible_date - today).days
                doc.days_until_destruction = max(0, delta)
            else:
                doc.days_until_destruction = 0

    # Phase 1 Critical Fields - Added by automated script
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    audit_trail_count = fields.Integer('Audit Trail Count', compute='_compute_audit_trail_count')
    chain_of_custody_count = fields.Integer('Chain of Custody Count', compute='_compute_chain_of_custody_count')
    file_format = fields.Char('File Format')
    file_size = fields.Float('File Size (MB)')
    scan_date = fields.Datetime('Scan Date')
    signature_verified = fields.Boolean('Signature Verified', default=False)

    # Phase 2 Audit & Compliance Fields - Added by automated script
    audit_log_ids = fields.One2many('records.audit.log', 'document_id', string='Audit Logs')
    last_audit_date = fields.Datetime('Last Audit Date', readonly=True)
    audit_required = fields.Boolean('Audit Required', default=False)
    audit_frequency = fields.Selection([('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], string='Audit Frequency')
    compliance_status = fields.Selection([('compliant', 'Compliant'), ('non_compliant', 'Non-Compliant'), ('pending_review', 'Pending Review')], string='Compliance Status', default='pending_review')
    compliance_notes = fields.Text('Compliance Notes')
    regulatory_classification = fields.Selection([('public', 'Public'), ('confidential', 'Confidential'), ('restricted', 'Restricted'), ('classified', 'Classified')], string='Regulatory Classification')
    data_subject_request = fields.Boolean('Data Subject Request', default=False, help='GDPR/Privacy related document')
    retention_hold = fields.Boolean('Retention Hold', default=False, help='Legal hold preventing destruction')
    legal_review_required = fields.Boolean('Legal Review Required', default=False)
    legal_review_date = fields.Date('Legal Review Date')
    legal_reviewer_id = fields.Many2one('res.users', string='Legal Reviewer')
    access_log_ids = fields.One2many('records.access.log', 'document_id', string='Access Logs')
    encryption_required = fields.Boolean('Encryption Required', default=False)
    encryption_status = fields.Selection([('none', 'Not Encrypted'), ('in_transit', 'Encrypted in Transit'), ('at_rest', 'Encrypted at Rest'), ('both', 'Fully Encrypted')], string='Encryption Status', default='none')
    access_level = fields.Selection([('public', 'Public'), ('internal', 'Internal'), ('restricted', 'Restricted'), ('confidential', 'Confidential')], string='Access Level', default='internal')
    authorized_users = fields.Many2many('res.users', string='Authorized Users')
    authorized_groups = fields.Many2many('res.groups', string='Authorized Groups')
    custody_log_ids = fields.One2many('records.chain.custody', 'document_id', string='Chain of Custody')
    current_custodian_id = fields.Many2one('res.users', string='Current Custodian')
    custody_verified = fields.Boolean('Custody Verified', default=False)
    custody_verification_date = fields.Datetime('Custody Verification Date')

    # Phase 3: Analytics & Computed Fields (10 fields)
    access_frequency = fields.Float(
        string='Access Frequency (per month)',
        compute='_compute_document_analytics',
        store=True,
        help='Average number of times document is accessed per month'
    )
    storage_efficiency = fields.Float(
        string='Storage Efficiency Score',
        compute='_compute_document_analytics',
        store=True,
        help='Efficiency score based on access vs storage cost'
    )
    compliance_risk_score = fields.Float(
        string='Compliance Risk Score',
        compute='_compute_document_analytics', 
        store=True,
        help='Risk score for compliance violations (0-100)'
    )
    retention_status = fields.Selection([
        ('active', 'Active Storage'),
        ('pending_review', 'Pending Review'),
        ('eligible_destruction', 'Eligible for Destruction'),
        ('permanent', 'Permanent Retention')
    ], string='Retention Status', compute='_compute_document_analytics', store=True)
    value_assessment = fields.Float(
        string='Document Value Score',
        compute='_compute_document_analytics',
        store=True,
        help='Assessed value of document for business operations'
    )
    digitization_priority = fields.Selection([
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('critical', 'Critical Priority')
    ], string='Digitization Priority', compute='_compute_document_analytics', store=True)
    aging_analysis = fields.Integer(
        string='Days Since Creation',
        compute='_compute_document_analytics',
        store=True,
        help='Number of days since document was created'
    )
    predicted_destruction_date = fields.Date(
        string='Predicted Destruction Date',
        compute='_compute_document_analytics',
        store=True,
        help='AI-predicted destruction date based on patterns'
    )
    document_health_score = fields.Float(
        string='Document Health Score',
        compute='_compute_document_analytics',
        store=True,
        help='Overall health score considering all factors'
    )
    analytics_insights = fields.Text(
        string='Analytics Insights',
        compute='_compute_document_analytics',
        store=True,
        help='AI-generated insights about this document'
    )


    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    def _compute_audit_trail_count(self):
        """Compute count of audit trail entries for this document"""
        for doc in self:
            # Count related audit trail records when audit model exists
            audit_count = 0
            try:
                if hasattr(self.env, 'records.audit.log'):
                    audit_count = self.env['records.audit.log'].search_count([
                        ('document_id', '=', doc.id)
                    ])
            except Exception:
                pass
            doc.audit_trail_count = audit_count

    def _compute_chain_of_custody_count(self):
        """Compute count of chain of custody entries for this document"""
        for doc in self:
            # Count related chain of custody records when model exists
            custody_count = 0
            try:
                if hasattr(self.env, 'records.chain.of.custody'):
                    custody_count = self.env['records.chain.of.custody'].search_count([
                        ('document_id', '=', doc.id)
                    ])
            except Exception:
                pass
            doc.chain_of_custody_count = custody_count

    @api.depends('created_date', 'last_access_date', 'retention_policy_id', 'document_category', 'digitized')
    def _compute_document_analytics(self):
        """Compute advanced analytics and business intelligence for documents"""
        for doc in self:
            # Calculate aging analysis
            if doc.created_date:
                doc.aging_analysis = (fields.Date.today() - doc.created_date).days
            else:
                doc.aging_analysis = 0
            
            # Access frequency calculation (simplified)
            if doc.last_access_date and doc.created_date:
                days_since_creation = (fields.Date.today() - doc.created_date).days
                if days_since_creation > 0:
                    # Simplified frequency calculation
                    doc.access_frequency = 30.0 / max(days_since_creation, 1)
                else:
                    doc.access_frequency = 1.0
            else:
                doc.access_frequency = 0.1  # Low frequency if never accessed
            
            # Storage efficiency (access frequency vs storage cost)
            storage_cost_per_day = 0.10  # $0.10 per day
            if doc.access_frequency > 0:
                doc.storage_efficiency = min(100, (doc.access_frequency / storage_cost_per_day) * 10)
            else:
                doc.storage_efficiency = 5.0  # Low efficiency for never-accessed docs
            
            # Compliance risk score
            risk_score = 0
            if doc.aging_analysis > 2555:  # 7 years
                risk_score += 30
            if not doc.retention_policy_id:
                risk_score += 40
            if not doc.digitized:
                risk_score += 20
            if doc.document_category == 'legal':
                risk_score += 10  # Legal docs have higher risk
            doc.compliance_risk_score = min(100, risk_score)
            
            # Retention status assessment
            if doc.aging_analysis > 2555:  # 7+ years
                doc.retention_status = 'eligible_destruction'
            elif doc.aging_analysis > 2190:  # 6+ years
                doc.retention_status = 'pending_review'
            elif doc.document_category == 'legal':
                doc.retention_status = 'permanent'
            else:
                doc.retention_status = 'active'
            
            # Document value assessment
            value_score = 50  # Base value
            if doc.document_category == 'legal':
                value_score += 30
            elif doc.document_category == 'financial':
                value_score += 25
            elif doc.document_category == 'contract':
                value_score += 20
            
            if doc.access_frequency > 1.0:
                value_score += 20
            if doc.digitized:
                value_score += 10
            
            doc.value_assessment = min(100, value_score)
            
            # Digitization priority
            if not doc.digitized:
                if doc.access_frequency > 2.0:
                    doc.digitization_priority = 'critical'
                elif doc.document_category in ['legal', 'financial']:
                    doc.digitization_priority = 'high'
                elif doc.access_frequency > 0.5:
                    doc.digitization_priority = 'medium'
                else:
                    doc.digitization_priority = 'low'
            else:
                doc.digitization_priority = 'low'  # Already digitized
            
            # Predicted destruction date
            if doc.retention_policy_id and hasattr(doc.retention_policy_id, 'retention_years'):
                years_to_add = getattr(doc.retention_policy_id, 'retention_years', 7)
                if doc.created_date:
                    from datetime import timedelta
                    doc.predicted_destruction_date = doc.created_date + timedelta(days=years_to_add * 365)
                else:
                    doc.predicted_destruction_date = False
            else:
                # Default 7-year retention
                if doc.created_date:
                    from datetime import timedelta
                    doc.predicted_destruction_date = doc.created_date + timedelta(days=7 * 365)
                else:
                    doc.predicted_destruction_date = False
            
            # Document health score (overall assessment)
            health_score = 100
            health_score -= doc.compliance_risk_score * 0.4  # Risk impacts health
            if not doc.digitized:
                health_score -= 15
            if doc.access_frequency < 0.1:
                health_score -= 10  # Unused documents
            if not doc.retention_policy_id:
                health_score -= 20
            
            doc.document_health_score = max(0, health_score)
            
            # Analytics insights (AI-style recommendations)
            insights = []
            
            if doc.compliance_risk_score > 70:
                insights.append("🚨 High compliance risk - review immediately")
            
            if doc.digitization_priority == 'critical':
                insights.append("📱 Critical for digitization - high access frequency")
            
            if doc.storage_efficiency < 20:
                insights.append("💰 Low storage efficiency - consider archiving")
            
            if doc.aging_analysis > 2555:
                insights.append("⏰ Eligible for destruction review")
            
            if doc.value_assessment > 80:
                insights.append("💎 High-value document - ensure protection")
            
            if not insights:
                insights.append("✅ Document in good standing")
            
            doc.analytics_insights = " | ".join(insights)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate content hash."""
        records = super().create(vals_list)
        for record in records:
            record._generate_content_hash()
        return records

    def write(self, vals):
        """Override write to protect permanent flag security."""
        # Check if someone is trying to modify permanent_flag directly
        if 'permanent_flag' in vals:
            # Only allow through internal _set_permanent_flag method or if user is admin
            frame = self.env.context.get('_permanent_flag_internal_call', False)
            if not frame and not self.env.user.has_group('base.group_system'):
                # For non-admins trying to unset permanent flag
                if any(record.permanent_flag and not vals['permanent_flag'] for record in self):
                    raise ValidationError(_(
                        'Only administrators can remove the permanent flag from documents. '
                        'Use the "Remove Permanent Flag" action with password verification.'
                    ))
        
        return super().write(vals)

    def _set_permanent_flag(self, permanent=True):
        """Internal method to set/unset permanent flag with audit trail."""
        # Set context flag to allow write override
        self_with_context = self.with_context(_permanent_flag_internal_call=True)
        
        for record in self_with_context:
            if permanent:
                record.write({
                    'permanent_flag': True,
                    'permanent_flag_set_by': self.env.user.id,
                    'permanent_flag_set_date': fields.Datetime.now()
                })
                # Log the action
                record.message_post(
                    body=_('Document marked as PERMANENT by %s. This document is now excluded from destruction schedules.') % self.env.user.name,
                    message_type='notification'
                )
            else:
                record.write({
                    'permanent_flag': False,
                    'permanent_flag_set_by': False,
                    'permanent_flag_set_date': False
                })
                # Log the action
                record.message_post(
                    body=_('PERMANENT flag removed by administrator %s. Document can now be included in destruction schedules.') % self.env.user.name,
                    message_type='notification'
                )

    def _generate_content_hash(self):
        """Generate a hash of the document content for security tracking."""
        for record in self:
            content_str = f"{record.name}_{record.description or ''}_{record.date or ''}"
            record.hashed_content = hashlib.sha256(content_str.encode()).hexdigest()[:16]

    # Onchange methods
    @api.onchange('box_id')
    def _onchange_box_id(self):
        """Ensure customer_id and department_id are always consistent with the selected box."""
        if self.box_id:
            self.customer_id = self.box_id.customer_id
            self.department_id = self.box_id.department_id
        else:
            self.customer_id = False
            self.department_id = False

    # Constraint methods
    @api.constrains('box_id', 'barcode')
    def _check_refiles_restriction(self):
        """Ensure only file folders can be placed in refiles locations."""
        for document in self:
            if document.box_id and document.box_id.location_id and document.barcode:
                location = document.box_id.location_id
                if location.location_type == 'refiles':
                    # Only 7-digit and 14-digit barcodes allowed in refiles
                    barcode_length = len(str(document.barcode))
                    if barcode_length not in [7, 14]:
                        raise ValidationError(_(
                            'Only file folders (7-digit or 14-digit barcodes) can be '
                            'placed in refiles locations. Document barcode %s (%d digits) '
                            'is not allowed in location %s.'
                        ) % (document.barcode, barcode_length, location.name))

    @api.model
    def classify_document_type(self, barcode):
        """Classify document type based on barcode length."""
        if not barcode:
            return None
            
        length = len(str(barcode))
        classification = {
            7: 'permanent_filefolder',
            10: 'shred_bin_item',
            14: 'temporary_filefolder'  # Portal-created, needs reassignment
        }
        return classification.get(length)

    def action_reassign_temp_folders(self):
        """Action to reassign temporary file folders to permanent locations."""
        temp_folders = self.filtered(lambda d: len(str(d.barcode)) == 14 if d.barcode else False)
        if not temp_folders:
            raise ValidationError(_('No temporary file folders (14-digit barcodes) found in selection'))
        
        return {
            'name': _('Reassign Temporary File Folders'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document.reassign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_ids': [(6, 0, temp_folders.ids)],
            }
        }

    # Action methods for workflow buttons
    def action_store(self):
        """Store the document in the designated location."""
        for record in self:
            if record.state == 'draft':
                record.state = 'stored'
        return True

    def action_retrieve(self):
        """Retrieve the document from storage."""
        for record in self:
            if record.state in ('stored', 'returned'):
                record.state = 'retrieved'
        return True

    def action_return(self):
        """Return the document to storage."""
        for record in self:
            if record.state == 'retrieved':
                record.state = 'returned'
        return True

    def action_destroy(self):
        """Mark the document as destroyed (NAID compliance)."""
        for record in self:
            if record.state in ('stored', 'returned'):
                record.state = 'destroyed'
                # Set default destruction method if not already set
                if not record.destruction_method:
                    record.destruction_method = 'shredding'
        return True

    def action_preview(self):
        """Preview the document attachment if available."""
        self.ensure_one()
        if self.attachment_ids:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self.attachment_ids[0].id}?download=false',
                'target': 'new',
            }
        return False

    def action_schedule_destruction(self):
        """Schedule the document for destruction."""
        for record in self:
            # Check if document is marked as permanent
            if record.permanent_flag:
                raise ValidationError(_(
                    'Document "%s" is marked as PERMANENT and cannot be scheduled for destruction. '
                    'Only administrators can remove the permanent flag.'
                ) % record.name)
            
            if record.state == 'archived':
                # Set retention date for destruction scheduling
                if not record.retention_date:
                    record.retention_date = fields.Date.today()
        return True

    def action_view_attachments(self):
        """View all attachments for this document."""
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            },
        }

    def action_mark_permanent(self):
        """Mark documents as permanent with password verification."""
        if not self:
            return
            
        # Open wizard for password verification
        return {
            'name': _('Mark as Permanent - Security Verification'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.permanent.flag.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_ids': [(6, 0, self.ids)],
                'default_action_type': 'mark'
            }
        }

    def action_unmark_permanent(self):
        """Remove permanent flag - admin only with password verification."""
        if not self:
            return
            
        # Check if user is admin
        if not self.env.user.has_group('base.group_system'):
            raise ValidationError(_(
                'Only administrators can remove the permanent flag from documents.'
            ))
            
        # Open wizard for password verification
        return {
            'name': _('Remove Permanent Flag - Admin Security Verification'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.permanent.flag.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_ids': [(6, 0, self.ids)],
                'default_action_type': 'unmark'
            }
        }

    def action_view_chain_of_custody(self):
        """View chain of custody records for this document."""
        self.ensure_one()
        return {
            'name': _('Chain of Custody: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.chain.of.custody',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id},
        }

    def action_scan_document(self):
        """Action to scan or upload images of documents."""
        self.ensure_one()
        return {
            'name': _('Scan/Image Document: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('res_model', '=', 'records.document'), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': 'records.document',
                'default_res_id': self.id,
                'default_name': 'Scan - %s' % self.name,
            },
        }

    def action_audit_trail(self):
        """View audit trail for this document."""
        self.ensure_one()
        return {
            'name': _('Audit Trail: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.audit.trail',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id},
        }

    @api.model
    def get_documents_eligible_for_destruction(self, exclude_permanent=True):
        """Get documents that are eligible for destruction, excluding permanent ones by default."""
        domain = [
            ('state', 'in', ['stored', 'archived']),
            ('retention_date', '<=', fields.Date.today())
        ]
        
        if exclude_permanent:
            domain.append(('permanent_flag', '=', False))
        
        return self.search(domain)

    @api.model
    def get_shred_rotation_documents(self, customer_id=None):
        """Get documents for customer shred rotation, excluding permanent documents."""
        domain = [
            ('permanent_flag', '=', False),  # Always exclude permanent documents
            ('state', 'in', ['stored', 'archived']),
            ('retention_date', '<=', fields.Date.today())
        ]
        
        if customer_id:
            domain.append(('customer_id', '=', customer_id))
        
        return self.search(domain)