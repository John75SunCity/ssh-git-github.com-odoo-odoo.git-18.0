# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class HrEmployee(models.Model):
    """Updated HR Employee for user access imports."""
    _inherit = 'hr.employee'

    # Portal user import fields
    can_import_users = fields.Boolean(
        string='Can Import Portal Users',
        help='Allow this employee to import users via portal'
    )
    
    portal_access_level = fields.Selection([
        ('basic', 'Basic Access'),
        ('advanced', 'Advanced Access'),
        ('admin', 'Admin Access'),
    ], string='Portal Access Level', default='basic')
    
    records_management_role = fields.Selection([
        ('viewer', 'Viewer'),
        ('operator', 'Operator'),
        ('supervisor', 'Supervisor'),
        ('manager', 'Manager'),
    ], string='Records Management Role', default='viewer')
    
    # User import tracking
    imported_user_count = fields.Integer(
        string='Imported Users Count',
        compute='_compute_imported_user_count'
    )
    
    last_import_date = fields.Datetime(string='Last Import Date')
    
    @api.depends('user_id')
    def _compute_imported_user_count(self):
        """Compute number of users imported by this employee."""
        for employee in self:
            # Implementation will be added when user import model is created
            employee.imported_user_count = 0
