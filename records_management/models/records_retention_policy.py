from odoo import models, fields, api, _

class RecordsRetentionPolicy(models.Model):
    _name = 'records.retention.policy'
    _description = 'Document Retention Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']

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
    # Note: activity_ids, message_follower_ids, message_ids provided by mixins
    action = fields.Selection([('archive', 'Archive'), ('destroy', 'Destroy'), ('review', 'Review')], string='Action')
    compliance_officer = fields.Many2one('res.users', string='Compliance Officer')
    legal_reviewer = fields.Many2one('res.users', string='Legal Reviewer')
    review_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], string='Review Frequency', default='yearly')
    notification_enabled = fields.Boolean('Notifications Enabled', default=True)
    priority = fields.Selection([('low', 'Low'), ('normal', 'Normal'), ('high', 'High')], string='Priority', default='normal')

    # Missing fields referenced in views
    destruction_method = fields.Selection([
        ('secure_shredding', 'Secure Shredding'),
        ('incineration', 'Incineration'),
        ('pulping', 'Pulping'),
        ('digital_deletion', 'Digital Deletion'),
        ('degaussing', 'Degaussing')
    ], string='Destruction Method', default='secure_shredding')
    compliance_rate = fields.Float('Compliance Rate (%)', compute='_compute_compliance_rate', store=True)
    
    # Missing fields referenced in views
    exception_count = fields.Integer('Exception Count', compute='_compute_exception_count', store=True)
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Risk Level', default='low')
    
    # Version history tracking
    version_history_ids = fields.One2many('records.policy.version', 'policy_id', string='Version History')
        'records.policy.version', 'policy_id', string='Version History'
    )
    
    # Missing fields referenced in views - added for comprehensive coverage
    changed_by = fields.Many2one('res.users', string='Changed By', 
                                 help='User who last modified this policy version',
                                 default=lambda self: self.env.user)
    is_current_version = fields.Boolean(string='Is Current Version', default=True,
                                        help='Indicates if this is the current active version of the policy')
    
    # Analytics fields
    policy_effectiveness_score = fields.Float(
        'Policy Effectiveness Score', compute='_compute_analytics', store=True
    )
    destruction_efficiency_rate = fields.Float(
        'Destruction Efficiency Rate', compute='_compute_analytics', store=True  
    )
    policy_risk_score = fields.Float(
        'Policy Risk Score', compute='_compute_analytics', store=True
    )

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
    version_history_ids = fields.One2many('records.policy.version', 'policy_id', string='Version History')'records.policy.version', 'policy_id', string='Version History')
    approval_workflow_id = fields.Many2one('records.approval.workflow', string='Approval Workflow')
    stakeholder_notification = fields.Boolean('Stakeholder Notification Required', default=True)
    risk_assessment_required = fields.Boolean('Risk Assessment Required', default=False)
    risk_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], string='Risk Level', default='medium')
    impact_assessment = fields.Text('Impact Assessment')
    mitigation_measures = fields.Text('Risk Mitigation Measures')
    exception_count = fields.Integer('Exception Count', compute='_compute_exception_count')
    violation_count = fields.Integer('Violation Count', compute='_compute_violation_count')

    # Phase 3: Analytics & Computed Fields (11 fields)
    policy_effectiveness_score = fields.Float(
        string='Policy Effectiveness (%)',
        compute='_compute_retention_analytics',
        store=True,
        help='Overall policy effectiveness score based on compliance and adoption'
    )
    compliance_adherence_rate = fields.Float(
        string='Compliance Adherence (%)',
        compute='_compute_retention_analytics',
        store=True,
        help='Percentage of documents following this policy correctly'
    )
    document_coverage_percentage = fields.Float(
        string='Document Coverage (%)',
        compute='_compute_retention_analytics',
        store=True,
        help='Percentage of applicable documents covered by this policy'
    )
    average_retention_duration = fields.Float(
        string='Avg Retention (Days)',
        compute='_compute_retention_analytics',
        store=True,
        help='Average actual retention duration for documents under this policy'
    )
    destruction_efficiency_rate = fields.Float(
        string='Destruction Efficiency (%)',
        compute='_compute_retention_analytics',
        store=True,
        help='Efficiency of document destruction process'
    )
    policy_risk_score = fields.Float(
        string='Policy Risk Score (0-10)',
        compute='_compute_retention_analytics',
        store=True,
        help='Risk assessment score for this retention policy'
    )
    storage_cost_impact = fields.Float(
        string='Storage Cost Impact ($)',
        compute='_compute_retention_analytics',
        store=True,
        help='Estimated monthly storage cost impact of this policy'
    )
    automation_utilization = fields.Float(
        string='Automation Utilization (%)',
        compute='_compute_retention_analytics',
        store=True,
        help='Percentage of policy actions that are automated'
    )
    legal_compliance_confidence = fields.Float(
        string='Legal Compliance Confidence (%)',
        compute='_compute_retention_analytics',
        store=True,
        help='Confidence level in legal compliance of this policy'
    )
    policy_performance_insights = fields.Text(
        string='Performance Insights',
        compute='_compute_retention_analytics',
        store=True,
        help='AI-generated insights about policy performance'
    )
    analytics_computation_date = fields.Datetime(
        string='Analytics Updated',
        compute='_compute_retention_analytics',
        store=True,
        help='Last analytics computation timestamp'
    )
    
    # Missing technical and activity fields