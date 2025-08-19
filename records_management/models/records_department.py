from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsDepartment(models.Model):
    _name = 'records.department'
    _description = 'Customer Department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partner_id, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Department Name', required=True, tracking=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, ondelete='cascade', tracking=True)
    billing_contact_ids = fields.One2many('records.department.billing.contact', 'department_id', string="Billing Contacts")
    container_ids = fields.One2many('records.container', 'department_id', string="Containers")
    document_ids = fields.One2many('records.document', 'department_id', string="Documents")

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # ANALYTICS
    # ============================================================================
    container_count = fields.Integer(compute='_compute_counts', string="Container Count", store=True)
    document_count = fields.Integer(compute='_compute_counts', string="Document Count", store=True)

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('name_partner_uniq', 'unique(name, partner_id, company_id)', 'The department name must be unique per customer.'),
    ]

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id:
                record.display_name = f"{record.partner_id.name} - {record.name}"
            else:
                record.display_name = record.name

    @api.depends('container_ids', 'document_ids')
    def _compute_counts(self):
        for record in self:
            record.container_count = len(record.container_ids)
            record.document_count = len(record.document_ids)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft departments can be activated."))
        self.write({'state': 'active'})
        self.message_post(body=_("Department activated."))

    def action_archive(self):
        self.ensure_one()
        if self.container_count > 0 or self.document_count > 0:
            raise UserError(_("Cannot archive a department that still has active containers or documents."))
        self.write({'state': 'archived', 'active': False})
        self.message_post(body=_("Department archived."))

    def action_view_containers(self):
        self.ensure_one()
        return {
            'name': _('Containers'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.container',
            'view_mode': 'tree,form,kanban',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id, 'default_partner_id': self.partner_id.id}
        }

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form,kanban',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id, 'default_partner_id': self.partner_id.id}
        }
