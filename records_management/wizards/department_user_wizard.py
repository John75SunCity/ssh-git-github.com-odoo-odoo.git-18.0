# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class DepartmentUserWizard(models.TransientModel):
    _name = 'department.user.wizard'
    _description = 'Create Portal User for Department'

    department_id = fields.Many2one('records.department', string='Department', required=True)
    company_partner_id = fields.Many2one('res.partner', string='Company', related='department_id.partner_id', readonly=True)

    # User details
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Last Name', required=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')

    # Access level
    portal_access_level = fields.Selection([
        ('department_user', 'Portal Department User'),
        ('department_admin', 'Portal Department Admin'),
        ('company_admin', 'Portal Company Admin'),
    ], string='Access Level', default='department_user', required=True)

    def action_create_portal_user(self):
        """Create individual contact under company and portal user"""
        self.ensure_one()

        # Validate email is unique
        existing_user = self.env['res.users'].search([('login', '=', self.email)], limit=1)
        if existing_user:
            raise UserError(_('A user with email %s already exists!') % self.email)

        # Create individual contact record under the company
        partner_vals = {
            'name': f"{self.first_name} {self.last_name}",
            'parent_id': self.company_partner_id.id,  # Link to company as child contact
            'type': 'contact',
            'email': self.email,
            'phone': self.phone,
            'mobile': self.mobile,
            'is_company': False,
            'company_type': 'person',
            'portal_access_level': self.portal_access_level,
        }

        contact_partner = self.env['res.partner'].create(partner_vals)

        # Create portal user linked to individual contact
        user_vals = {
            'name': f"{self.first_name} {self.last_name}",
            'login': self.email,
            'email': self.email,
            'partner_id': contact_partner.id,  # Link to individual contact, NOT company
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        }

        new_user = self.env['res.users'].with_context(no_reset_password=True).create(user_vals)

        # Apply portal access level groups
        contact_partner.portal_access_level = self.portal_access_level
        contact_partner._apply_portal_groups()

        # Add user to department
        if self.department_id.user_ids:
            self.department_id.write({'user_ids': [(4, new_user.id)]})
        else:
            self.department_id.user_ids = [(4, new_user.id)]

        # Send portal invitation
        new_user.partner_id.signup_prepare()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Portal User Created'),
                'message': _('Portal user %s created successfully. Invitation email will be sent.') % new_user.name,
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
