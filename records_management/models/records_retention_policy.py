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

    def action_deactivate_policy(self):
        """Deactivate the retention policy"""
        self.ensure_one()
        self.policy_status = 'inactive'
        return True

    def action_view_documents(self):
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
