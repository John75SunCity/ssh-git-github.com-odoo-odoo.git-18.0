# -*- coding: utf-8 -*-
from odoo import models, fields, api, _



class RecordsPortalUserInvitationWizard(models.TransientModel):
    """Wizard for inviting new users to access records management portal"""
    _name = 'records.portal.user.invitation.wizard'
    _description = 'Records Portal User Invitation Wizard'

    # Customer context
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    department_id = fields.Many2one('records.department', string='Department')

    # Invitation details
    email = fields.Char(string='Email Address', required=True)
    name = fields.Char(string='Full Name', required=True)
    phone = fields.Char(string='Phone Number')

    # Access level
    access_level = fields.Selection([
        ('view', 'View Only'),
        ('request', 'View & Request'),
        ('manage', 'Department Manager')
    ], string='Access Level', default='view', required=True)

    # Portal access
    create_portal_user = fields.Boolean(string='Create Portal User', default=True)
    send_invitation_email = fields.Boolean(string='Send Invitation Email', default=True)

    # Message
    invitation_message = fields.Text(string='Invitation Message',
                                default="You have been invited to access our Records Management Portal.")

    def action_send_invitation(self):
        """Send invitation to user"""

        self.ensure_one()

        # Create or find partner
        partner = self.env['res.partner'].search([('email', '=', self.email)], limit=1)
        if not partner:
            partner = self.env['res.partner'].create({
                'name': self.name,
                'email': self.email,
                'phone': self.phone,
                'is_company': False,
                'customer_rank': 1
            })

        # Create department user record
        if self.department_id:
            dept_user = self.env['records.storage.department.user'].create({
                'user_id': partner.id,
                'department_id': self.department_id.id,
                'access_level': self.access_level,
                'active': True
            })

        # Create portal user if requested
        if self.create_portal_user:
            portal_wizard = self.env['portal.wizard'].create({
                'user_ids': [(0, 0, {
                    'partner_id': partner.id,
                    'email': self.email,
                    'in_portal': True
                })]
            })
            portal_wizard.action_apply()

        # Send invitation email if requested
        if self.send_invitation_email:
            template = self.env.ref('records_management.email_template_user_invitation', False)
            if template:
                template.send_mail(partner.id, force_send=True)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Invitation Sent'),
                'message': _('User invitation has been sent successfully.'),
                'type': 'success'
            }
        }

class RecordsBulkUserImport(models.TransientModel):
    """Wizard for bulk importing users from CSV/Excel"""
    _name = 'records.bulk.user.import'
    _description = 'Records Bulk User Import'

    # Import file
    import_file = fields.Binary(string='Import File', required=True, help='CSV or Excel file with user data')
    filename = fields.Char(string='Filename')
    file_type = fields.Selection([
        ('csv', 'CSV File'),
        ('excel', 'Excel File')
    ], string='File Type', compute='_compute_file_type', store=True)

    # Import options
    customer_id = fields.Many2one('res.partner', string='Default Customer', required=True)
    department_id = fields.Many2one('records.department', string='Default Department')
    default_access_level = fields.Selection([
        ('view', 'View Only'),
        ('request', 'View & Request'),
        ('manage', 'Department Manager')
    ], string='Default Access Level', default='view')

    # Processing options
    create_missing_departments = fields.Boolean(string='Create Missing Departments', default=True)
    send_invitation_emails = fields.Boolean(string='Send Invitation Emails', default=False)
    skip_duplicates = fields.Boolean(string='Skip Duplicate Emails', default=True)

    # Results
    import_summary = fields.Text(string='Import Summary', readonly=True)
    imported_count = fields.Integer(string='Successfully Imported', readonly=True)
    error_count = fields.Integer(string='Errors', readonly=True)

    @api.depends('filename')
    def _compute_file_type(self):
        for record in self:
            if record.filename:
                if record.filename.lower().endswith('.csv'):
                    record.file_type = 'csv'
                elif record.filename.lower().endswith(('.xlsx', '.xls')):
                    record.file_type = 'excel'
                else:
                    record.file_type = 'csv'  # Default
            else:
                record.file_type = 'csv'

    def action_import_users(self):
        """Process the bulk import"""

        self.ensure_one()

        # This would contain the actual import logic
        # For now, return a placeholder
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import Processing'),
                'message': _('Bulk import functionality will be implemented in the next phase.'),
                'type': 'info'
            }
        }
