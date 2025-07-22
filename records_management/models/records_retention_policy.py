from odoo import models, fields, api

class RecordsRetentionPolicy(models.Model):
    _name = 'records.retention.policy'
    _description = 'Document Retention Policy'

    name = fields.Char('Policy Name', required=True)
    retention_years = fields.Integer('Retention Period (Years)', required=True)
    retention_period = fields.Integer('Retention Period (Days)', compute='_compute_retention_period', store=True)
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
    review_date = fields.Date('Next Review Date')
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    approved_by = fields.Many2one('res.users', string='Approved By')
    
    # Relationships
    document_ids = fields.One2many('records.document', 'retention_policy_id', string='Documents')
    document_count = fields.Integer(compute='_compute_document_count')

    @api.depends('retention_years')
    def _compute_retention_period(self):
        for policy in self:
            policy.retention_period = policy.retention_years * 365 if policy.retention_years else 0

    @api.depends('document_ids')
    def _compute_document_count(self):
        for policy in self:
            policy.document_count = len(policy.document_ids)
