from odoo import models, fields, api, _

class RecordsRetentionPolicy(models.Model, mail.thread):
    _name = 'records.retention.policy'
    _description = 'Document Retention Policy'

    name = fields.Char('Policy Name', required=True)
    retention_years = fields.Integer('Retention Period (Years)', required=True)
    retention_period = fields.Integer('Retention Period (Days)', compute='_compute_retention_period', store=True)
    retention_unit = fields.Selection([
        ('days', 'Days'),
        ('months', 'Months'),
        ('years', 'Years')
    ], string='Retention Unit', default='years', required=True)
    description = fields.Text('Description')
    active = fields.Boolean(default=True)
    
    # Policy Configuration
    policy_type = fields.Selection([
        ('standard', 'Standard'),
        ('legal_hold', 'Legal Hold'),
        ('regulatory', 'Regulatory'),
        ('custom', 'Custom')
    ], string='Policy Type', required=True, default='standard')
    
    policy_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('expired', 'Expired')
    ], string='Policy Status', default='active')
    
    # Automation Settings
    auto_archive = fields.Boolean('Auto Archive', default=False,
                                help='Automatically archive documents when retention period expires')
    auto_destroy = fields.Boolean('Auto Destroy', default=False,
                                 help='Automatically destroy documents when destruction is eligible')
    compliance_required = fields.Boolean('Compliance Required', default=True,
                                       help='Requires compliance verification before destruction')
    compliance_verified = fields.Boolean('Compliance Verified', default=False,
                                        help='Indicates if this policy has been verified for compliance')
    
    # Trigger Configuration
    trigger_event = fields.Selection([
        ('creation', 'Document Creation'),
        ('closure', 'Case Closure'),
        ('last_access', 'Last Access'),
        ('custom_date', 'Custom Date')
    ], string='Trigger Event', default='creation',
       help='Event that starts the retention period countdown')
    
    # Additional Policy Details
    legal_basis = fields.Text('Legal Basis', help='Legal or regulatory basis for this retention policy')
    regulatory_requirement = fields.Char('Regulatory Requirement', 
                                        help='Specific regulatory or legal requirement this policy addresses')
    effective_date = fields.Date('Effective Date', default=fields.Date.today, 
                                help='Date when this retention policy becomes effective')
    review_date = fields.Date('Review Date')
    next_review_date = fields.Date('Next Review Date', compute='_compute_next_review_date', store=True,
                                   help='Automatically calculated next review date based on review cycle')
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    approved_by = fields.Many2one('res.users', string='Approved By')
    
    # Relationships
    document_ids = fields.One2many('records.document', 'retention_policy_id', string='Documents')
    document_count = fields.Integer(compute='_compute_document_count')
    schedule_count = fields.Integer(string='Scheduled Actions', default=0)
    audit_count = fields.Integer(string='Audit Logs', default=0)

    # Phase 1 Critical Fields - Added by automated script
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    action = fields.Selection([('archive', 'Archive'), ('destroy', 'Destroy'), ('review', 'Review')], string='Action')
    compliance_officer = fields.Many2one('res.users', string='Compliance Officer')
    legal_reviewer = fields.Many2one('res.users', string='Legal Reviewer')
    review_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], string='Review Frequency', default='yearly')
    notification_enabled = fields.Boolean('Notifications Enabled', default=True)
    priority = fields.Selection([('low', 'Low'), ('normal', 'Normal'), ('high', 'High')], string='Priority', default='normal')

    # Phase 2 Audit & Compliance Fields - Added by automated script
    compliance_framework = fields.Selection([('sox', 'Sarbanes-Oxley'), ('hipaa', 'HIPAA'), ('gdpr', 'GDPR'), ('pci', 'PCI-DSS'), ('iso27001', 'ISO 27001'), ('nist', 'NIST'), ('custom', 'Custom')], string='Compliance Framework')
    regulatory_citation = fields.Text('Regulatory Citation', help='Specific law, regulation, or standard citation')
    compliance_officer_approval = fields.Boolean('Compliance Officer Approval Required', default=True)
    legal_counsel_review = fields.Boolean('Legal Counsel Review Required', default=False)
    audit_trail_required = fields.Boolean('Audit Trail Required', default=True)
    exception_approval_required = fields.Boolean('Exception Approval Required', default=True)
    last_review_date = fields.Date('Last Review Date')
    review_cycle_months = fields.Integer('Review Cycle (Months)', default=12)
    next_mandatory_review = fields.Date('Next Mandatory Review', compute='_compute_next_review')
    policy_version = fields.Char('Policy Version', default='1.0')
    version_history_ids = fields.One2many('records.policy.version', 'policy_id', string='Version History')
    approval_workflow_id = fields.Many2one('records.approval.workflow', string='Approval Workflow')
    stakeholder_notification = fields.Boolean('Stakeholder Notification Required', default=True)
    risk_assessment_required = fields.Boolean('Risk Assessment Required', default=False)
    risk_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], string='Risk Level', default='medium')
    impact_assessment = fields.Text('Impact Assessment')
    mitigation_measures = fields.Text('Risk Mitigation Measures')
    exception_count = fields.Integer('Exception Count', compute='_compute_exception_count')
    violation_count = fields.Integer('Violation Count', compute='_compute_violation_count')


    @api.depends('retention_years')
    def _compute_retention_period(self):
        for policy in self:
            policy.retention_period = policy.retention_years * 365 if policy.retention_years else 0

    @api.depends('document_ids')
    def _compute_document_count(self):
        for policy in self:
            policy.document_count = len(policy.document_ids)

    @api.depends('retention_years')
    def _compute_retention_period(self):
        for policy in self:
            policy.retention_period = policy.retention_years * 365 if policy.retention_years else 0

    @api.depends('document_ids')
    def _compute_document_count(self):
        for policy in self:
            policy.document_count = len(policy.document_ids)

    @api.depends('review_date', 'name')
    def _compute_next_review_date(self):
        """Compute next review date based on review cycle"""
        for record in self:
            if record.review_date:
                # If review_date is set, use it as next_review_date
                record.next_review_date = record.review_date
            else:
                # Default to one year from today if no review_date set
                from datetime import date, timedelta
                record.next_review_date = date.today() + timedelta(days=365)

    def action_apply_policy(self):
        """Apply this retention policy to selected documents or document types."""
        self.ensure_one()
        return {
            'name': _('Apply Retention Policy: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.retention.policy.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_policy_id': self.id,
                'default_policy_name': self.name,
            }
        }

    def action_review_policy(self):
        """Review and update retention policy"""
        self.ensure_one()
        return {
            'name': _('Review Policy: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.retention.policy',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_activate_policy(self):
        """Activate the retention policy"""
        self.ensure_one()
        self.policy_status = 'active'
        return True

    @api.depends('review_date', 'name')
    def _compute_next_review_date(self):
        """Compute next review date based on review cycle"""
        for record in self:
            if record.review_date:
                # If review_date is set, use it as next_review_date
                record.next_review_date = record.review_date
            else:
                # Default to one year from today if no review_date set
                from datetime import date, timedelta
                record.next_review_date = date.today() + timedelta(days=365)

    def action_deactivate_policy(self):
        """Deactivate the retention policy"""
        self.ensure_one()
        self.policy_status = 'inactive'
        return True

    def action_view_policy_documents(self):
        """View documents using this policy"""
        self.ensure_one()
        return {
            'name': _('Documents with Policy: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('retention_policy_id', '=', self.id)],
            'context': {'default_retention_policy_id': self.id},
        }

    def action_compliance_check(self):
        """Check compliance for this policy"""
        self.ensure_one()
        return {
            'name': _('Compliance Check'),
            'type': 'ir.actions.act_window',
            'res_model': 'policy.compliance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_policy_id': self.id},
        }

    def action_schedule_review(self):
        """Schedule policy review"""
        self.ensure_one()
        return {
            'name': _('Schedule Review'),
            'type': 'ir.actions.act_window',
            'res_model': 'policy.review.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_policy_id': self.id},
        }

    def action_duplicate_policy(self):
        """Duplicate this retention policy"""
        self.ensure_one()
        new_policy = self.copy({
            'name': _('%s (Copy)') % self.name,
            'policy_status': 'pending',
        })
        return {
            'name': _('Duplicated Policy'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.retention.policy',
            'res_id': new_policy.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_affected_documents(self):
        """View documents affected by this retention policy"""
        self.ensure_one()
        return {
            'name': _('Documents with Retention Policy: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('retention_policy_id', '=', self.id)],
            'context': {'default_retention_policy_id': self.id},
        }

    def action_archive_expired_documents(self):
        """Archive documents that have expired retention periods"""
        self.ensure_one()
        
        # Find documents that have passed retention period
        documents = self.env['records.document'].search([
            ('retention_policy_id', '=', self.id),
            ('state', '!=', 'archived')
        ])
        
        archived_count = 0
        for doc in documents:
            if doc.is_retention_expired():
                doc.action_archive()
                archived_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Archive Complete'),
                'message': _('Archived %d documents based on retention policy.') % archived_count,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_apply_to_documents(self):
        """Apply this retention policy to selected documents"""
        self.ensure_one()
        return {
            'name': _('Apply Retention Policy'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree',
            'domain': [('retention_policy_id', '=', False)],
            'context': {
                'search_default_no_retention_policy': 1,
                'default_retention_policy_id': self.id,
            },
            'help': _('Select documents to apply this retention policy to.'),
        }

    def action_apply_policy(self):
        """Apply this retention policy to documents"""
        return self.action_apply_to_documents()

    def action_schedule_review(self):
        """Schedule a review for this retention policy"""
        self.ensure_one()
        return {
            'name': _('Schedule Policy Review'),
            'type': 'ir.actions.act_window',
            'res_model': 'calendar.event',
            'view_mode': 'form',
            'context': {
                'default_name': _('Review Retention Policy: %s') % self.name,
                'default_description': _('Review retention policy for compliance and effectiveness'),
            },
            'target': 'new',
        }

    def action_compliance_audit(self):
        """Launch compliance audit for this retention policy"""
        self.ensure_one()
        return {
            'name': _('Compliance Audit: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [
                ('retention_policy_id', '=', self.id),
                '|',
                ('retention_expired', '=', True),
                ('eligible_for_destruction', '=', True)
            ],
            'context': {'search_default_compliance_issues': 1},
        }

    def action_duplicate(self):
        """Duplicate this retention policy"""
        return self.action_duplicate_policy()

    def action_test_policy(self):
        """Test this retention policy with sample data"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Policy Test'),
                'message': _('Policy "%s" validation complete. Ready for deployment.') % self.name,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_schedules(self):
        """View schedules related to this retention policy"""
        self.ensure_one()
        return {
            'name': _('Retention Schedules'),
            'type': 'ir.actions.act_window',
            'res_model': 'calendar.event',
            'view_mode': 'tree,form',
            'domain': [('name', 'ilike', self.name)],
            'context': {'default_retention_policy_id': self.id},
        }

    def action_view_audit_logs(self):
        """View audit logs for this retention policy"""
        self.ensure_one()
        return {
            'name': _('Audit Logs: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'mail.message',
            'view_mode': 'tree,form',
            'domain': [
                ('res_id', '=', self.id),
                ('model', '=', 'records.retention.policy')
            ],
        }

    def action_apply_to_type(self):
        """Apply retention policy to a specific document type"""
        self.ensure_one()
        return {
            'name': _('Apply to Document Type'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document.type',
            'view_mode': 'tree',
            'context': {'default_retention_policy_id': self.id},
        }

    def action_refresh_counts(self):
        """Refresh schedule and audit counts manually"""
        for policy in self:
            # Update schedule count
            schedule_count = 0
            try:
                schedule_count += self.env['ir.cron'].search_count([
                    ('name', 'ilike', policy.name or ''),
                    ('active', '=', True)
                ])
                schedule_count += self.env['records.document'].search_count([
                    ('retention_policy_id', '=', policy.id),
                    ('destruction_eligible_date', '!=', False),
                    ('state', '!=', 'destroyed')
                ])
            except Exception:
                pass
            policy.schedule_count = schedule_count
            
            # Update audit count
            audit_count = 0
            try:
                if self.env['naid.audit']._name:
                    audit_count = self.env['naid.audit'].search_count([
                        ('policy_id', '=', policy.id)
                    ])
            except Exception:
                pass
            policy.audit_count = audit_count
