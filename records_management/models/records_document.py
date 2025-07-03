from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class RecordsDocument(models.Model):
    _name = 'records.document'
    _description = 'Document Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name'
    
    name = fields.Char('Document Reference', required=True, tracking=True)
    box_id = fields.Many2one('records.box', string='Box', required=True,
                            tracking=True, index=True,
                            domain="[('state', '=', 'active')]")
    location_id = fields.Many2one(related='box_id.location_id', 
                                 string='Storage Location', store=True)
    
    # Document metadata
    document_type_id = fields.Many2one('records.document.type', string='Document Type')
    date = fields.Date('Document Date', default=fields.Date.context_today)
    description = fields.Html('Description')
    tags = fields.Many2many('records.tag', string='Tags')
    
    # Retention details
    retention_policy_id = fields.Many2one('records.retention.policy', string='Retention Policy')
    retention_date = fields.Date('Retention Date', tracking=True, 
                                compute='_compute_retention_date', store=True)
    days_to_retention = fields.Integer('Days until destruction', compute='_compute_days_to_retention')
    
    # Relations
    partner_id = fields.Many2one('res.partner', string='Related Partner')
    user_id = fields.Many2one('res.users', string='Responsible', tracking=True)
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company)
    
    # File management
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    attachment_count = fields.Integer('Attachment Count', compute='_compute_attachment_count')
    
    # Status fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('stored', 'Stored'),
        ('retrieved', 'Retrieved'),
        ('returned', 'Returned'),
        ('destroyed', 'Destroyed')
    ], string='Status', default='draft', tracking=True)
    active = fields.Boolean(default=True)
    
    @api.depends('date', 'retention_policy_id', 'retention_policy_id.retention_years')
    def _compute_retention_date(self):
        for doc in self:
            if doc.date and doc.retention_policy_id and doc.retention_policy_id.retention_years:
                years = doc.retention_policy_id.retention_years
                doc.retention_date = fields.Date.add(doc.date, years=years)
            else:
                doc.retention_date = False
    
    @api.depends('retention_date')
    def _compute_days_to_retention(self):
        today = fields.Date.today()
        for doc in self:
            if doc.retention_date:
                delta = (doc.retention_date - today).days
                doc.days_to_retention = max(0, delta)
            else:
                doc.days_to_retention = 0
    
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)
    
    @api.onchange('box_id')
    def _onchange_box_id(self):
        if self.box_id and self.box_id.document_count >= self.box_id.capacity:
            return {
                'warning': {
                    'title': _("Box is at capacity"),
                    'message': _("This box is already at or exceeding its capacity.")
                }
            }
    
    def action_store(self):
        self.write({'state': 'stored'})
    
    def action_retrieve(self):
        self.write({'state': 'retrieved'})
    
    def action_return(self):
        self.write({'state': 'returned'})
    
    def action_destroy(self):
        self.write({'state': 'destroyed'})
    
    def action_view_attachments(self):
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
            'context': {'default_res_model': 'records.document', 'default_res_id': self.id},
        }


class RecordsDocumentType(models.Model):
    _name = 'records.document.type'
    _description = 'Document Type'
    
    name = fields.Char('Type Name', required=True)
    code = fields.Char('Code')
    retention_policy_id = fields.Many2one('records.retention.policy', string='Default Retention Policy')
    active = fields.Boolean(default=True)