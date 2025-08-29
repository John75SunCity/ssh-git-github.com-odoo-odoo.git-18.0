from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class NaidCompliancePolicy(models.Model):
    _name = 'naid.compliance.policy'
    _description = 'NAID Compliance Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Policy Name', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, help='Order of policy evaluation')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True)

    # Policy classification and type
    policy_type = fields.Selection([
        ('access_control', 'Access Control'),
        ('document_handling', 'Document Handling'),
        ('destruction_process', 'Destruction Process'),
        ('employee_screening', 'Employee Screening'),
        ('facility_security', 'Facility Security'),
        ('equipment_maintenance', 'Equipment Maintenance'),
        ('audit_requirements', 'Audit Requirements'),
        ('data_privacy', 'Data Privacy'),
        ('transportation', 'Transportation'),
        ('incident_response', 'Incident Response'),
    ], string='Policy Type', required=True, tracking=True)

    description = fields.Text(string='Policy Description', required=True)
    mandatory = fields.Boolean(string='Mandatory', default=True, tracking=True)

    # Compliance checking configuration
    automated_check = fields.Boolean(string='Automated Check', default=False, tracking=True)
    check_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('as_needed', 'As Needed'),
    ], string='Check Frequency', tracking=True)

    # Implementation and violation handling
    implementation_notes = fields.Text(string='Implementation Notes')
    violation_consequences = fields.Text(string='Violation Consequences')
    review_frequency_months = fields.Integer(string='Review Frequency (Months)', default=12)

    # Status and tracking
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('under_review', 'Under Review'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True)

    # Relationships
    checklist_ids = fields.One2many('naid.compliance.checklist', 'policy_id', string='Related Checklists')

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('review_frequency_months')
    def _check_review_frequency(self):
        for record in self:
            if record.review_frequency_months and record.review_frequency_months <= 0:
                raise ValidationError(_("Review frequency must be a positive number of months."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate the policy."""
        self.ensure_one()
        self.write({'state': 'active'})
        self.message_post(body=_("Policy activated."))

    def action_archive(self):
        """Archive the policy."""
        self.ensure_one()
        self.write({'state': 'archived', 'active': False})
        self.message_post(body=_("Policy archived."))

    def action_start_review(self):
        """Start a policy review process."""
        self.ensure_one()
        self.write({'state': 'under_review'})
        self.message_post(body=_("Policy review started."))
