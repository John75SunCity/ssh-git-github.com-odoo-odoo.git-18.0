from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class NaidRiskAssessment(models.Model):
    _name = 'naid.risk.assessment'
    _description = 'NAID Risk Assessment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'risk_level desc, assessment_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Risk Title', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    active = fields.Boolean(string='Active', default=True)
    
    assessment_date = fields.Date(string='Assessment Date', required=True, default=fields.Date.context_today, tracking=True)
    assessor_id = fields.Many2one('res.users', string='Assessor', default=lambda self: self.env.user, required=True, tracking=True)
    
    risk_category = fields.Selection([
        ('physical_security', 'Physical Security'),
        ('information_security', 'Information Security'),
        ('personnel_security', 'Personnel Security'),
        ('operational', 'Operational'),
        ('compliance', 'Compliance'),
    ], string='Risk Category', required=True, tracking=True)
    
    risk_description = fields.Text(string='Risk Description', required=True)
    
    impact_level = fields.Selection([
        ('1', 'Low'),
        ('2', 'Medium'),
        ('3', 'High'),
        ('4', 'Critical')
    ], string='Impact Level', required=True, tracking=True, default='2')
    
    probability = fields.Selection([
        ('1', 'Rare'),
        ('2', 'Unlikely'),
        ('3', 'Possible'),
        ('4', 'Likely'),
        ('5', 'Certain')
    ], string='Probability', required=True, tracking=True, default='3')
    
    risk_score = fields.Integer(string='Risk Score', compute='_compute_risk_score', store=True, readonly=True)
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Risk Level', compute='_compute_risk_level', store=True, readonly=True)
    
    mitigation_plan_id = fields.Many2one('naid.compliance.action.plan', string='Mitigation Action Plan', readonly=True)
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('identified', 'Identified'),
        ('in_mitigation', 'In Mitigation'),
        ('mitigated', 'Mitigated'),
        ('accepted', 'Risk Accepted'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', readonly=True, tracking=True)
    
    review_date = fields.Date(string='Next Review Date', tracking=True)

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('impact_level', 'probability')
    def _compute_risk_score(self):
        for record in self:
            if record.impact_level and record.probability:
                record.risk_score = int(record.impact_level) * int(record.probability)
            else:
                record.risk_score = 0

    @api.depends('risk_score')
    def _compute_risk_level(self):
        for record in self:
            if record.risk_score >= 15:
                record.risk_level = 'critical'
            elif record.risk_score >= 9:
                record.risk_level = 'high'
            elif record.risk_score >= 4:
                record.risk_level = 'medium'
            else:
                record.risk_level = 'low'

    @api.constrains('assessment_date', 'review_date')
    def _check_dates(self):
        for record in self:
            if record.review_date and record.assessment_date and record.review_date < record.assessment_date:
                raise ValidationError(_("The next review date cannot be before the assessment date."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        self.ensure_one()
        self.write({'status': 'identified'})
        self.message_post(body=_("Risk assessment confirmed and moved to 'Identified' state."))

    def action_create_mitigation_plan(self):
        self.ensure_one()
        action_plan = self.env['naid.compliance.action.plan'].create({
            'name': _("Mitigation for Risk: %s") % self.name,
            'description': self.risk_description,
            'priority': '3' if self.risk_level == 'critical' else '2',
            'due_date': self.review_date or fields.Date.add(fields.Date.context_today(self), months=1),
            'responsible_user_id': self.assessor_id.id,
            'res_model': self._name,
            'res_id': self.id,
        })
        self.write({
            'mitigation_plan_id': action_plan.id,
            'status': 'in_mitigation',
        })
        self.message_post(body=_("Mitigation action plan created by %s.") % self.env.user.name)
        return {
            'name': _('Mitigation Action Plan'),
            'type': 'ir.actions.act_window',
            'res_model': 'naid.compliance.action.plan',
            'view_mode': 'form',
            'res_id': action_plan.id,
            'target': 'current',
        }

    def action_accept_risk(self):
        self.ensure_one()
        if self.risk_level in ('high', 'critical'):
            raise ValidationError(_("High and Critical risks cannot be accepted without a mitigation plan or explicit manager approval."))
        self.write({'status': 'accepted'})
        self.message_post(body=_("Risk accepted by %s.") % self.env.user.name)

    def action_reset_to_draft(self):
        self.ensure_one()
        if self.mitigation_plan_id:
            raise ValidationError(_("Cannot reset to draft as a mitigation plan is already linked."))
        self.write({'status': 'draft'})
        self.message_post(body=_("Risk assessment reset to draft."))
