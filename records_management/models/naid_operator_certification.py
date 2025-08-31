from odoo import models, fields, api

class NAIDOperatorCertification(models.Model):
    _name = 'naid.operator.certification'
    _description = 'NAID Operator Certification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Certification Name', required=True, tracking=True)
    operator_id = fields.Many2one('res.users', string='Operator', required=True, tracking=True)
    certification_type = fields.Selection(
        [
            ("aaa", "NAID AAA"),
            ("aa", "NAID AA"),
            ("a", "NAID A"),
            ("plant_based", "Plant-Based Destruction"),
            ("offsite", "Mobile Destruction"),
            ("hard_drive", "Hard Drive Destruction"),
            ("other", "Other"),
        ],
        string="Certification Type",
        required=True,
        default="aaa",
        tracking=True,
    )

    # Certification details
    certificate_number = fields.Char(string='Certificate Number', required=True, tracking=True)
    issue_date = fields.Date(string='Issue Date', required=True, tracking=True)
    expiry_date = fields.Date(string='Expiry Date', required=True, tracking=True)
    issuing_authority = fields.Char(string='Issuing Authority', default='NAID', tracking=True)

    # Status and validity
    status = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked')
    ], string='Status', default='active', tracking=True, compute='_compute_status', store=True)

    # Additional information
    scope_of_certification = fields.Text(string='Scope of Certification')
    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', 'naid_certification_attachment_rel', 'certification_id', 'attachment_id', string='Certification Documents')
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.depends('expiry_date')
    def _compute_status(self):
        for record in self:
            if record.expiry_date and record.expiry_date < fields.Date.context_today(self):
                record.status = 'expired'
            elif record.status == 'expired' and record.expiry_date >= fields.Date.context_today(self):
                record.status = 'active'
