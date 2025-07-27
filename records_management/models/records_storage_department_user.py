# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsStorageDepartmentUser(models.Model):
    """
    Model for tracking users assigned to storage departments.
    Links users to specific departments for access control and tracking.
    """
    _name = 'records.storage.department.user'
    _description = 'Storage Department User Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'user_id'
    _order = 'department_id, user_id'

    # Core fields
    user_id = fields.Many2one('res.users', string='User', required=True, tracking=True)
    department_id = fields.Many2one('records.department', string='Department', required=True, tracking=True)
    
    # Role and permissions
    role = fields.Selection([
        ('viewer', 'Viewer',
        ('user', 'User'), 
        ('admin', 'Administrator')
    
    # Status fields), string="Selection Field"
    active = fields.Boolean(string='Active', default=True, tracking=True)
    date_assigned = fields.Date(string='Date Assigned', default=fields.Date.today, tracking=True)
    date_removed = fields.Date(string='Date Removed', tracking=True)
    
    # Access permissions
    can_view_documents = fields.Boolean(string='Can View Documents', default=True)
    can_create_requests = fields.Boolean(string='Can Create Requests', default=True)
    can_approve_requests = fields.Boolean(string='Can Approve Requests', default=False)
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company
    
    # Computed fields
    user_name = fields.Char(related='user_id.name', string='User Name', readonly=True)
    department_name = fields.Char(related='department_id.name', string='Department Name', readonly=True)
    
    @api.constrains('user_id', 'department_id')
    def _check_unique_user_department(self):
        """Ensure user is not assigned to the same department multiple times"""
        for record in self:
            existing = self.search\([
                ('user_id', '=', record.user_id.id),
                ('department_id', '=', record.department_id.id),
                ('active', '=', True),
                ('id', '!=', record.id)])
            ]
            if existing:
                raise ValidationError(_('User %s is already assigned to department %s') % 
                                    (record.user_id.name, record.department_id.name)
    
    def action_activate(self):
        """Activate user assignment"""
        self.write({'active': True, 'date_removed': False})
    
    def action_deactivate(self):
        """Deactivate user assignment"""
        self.write({'active': False, 'date_removed': fields.Date.today()})
