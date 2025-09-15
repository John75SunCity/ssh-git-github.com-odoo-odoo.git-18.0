from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class RecordsUserInvitationWizard(models.TransientModel):
    """
    Wizard for inviting users to the Records Management system.
    
    This wizard handles user invitation emails, access permission setup,
    and department assignment for new Records Management users.
    """
    
    _name = 'records.user.invitation.wizard'
    _description = 'Records Management User Invitation Wizard'

    # Invitation Details
    email = fields.Char(
        string='Email Address',
        required=True,
        help='Email address of the person to invite'
    )
    
    name = fields.Char(
        string='Full Name',
        required=True,
        help='Full name of the person to invite'
    )
    
    department_id = fields.Many2one(
        comodel_name='records.department',
        string='Department',
        required=True,
        help='Department to assign the user to'
    )
    
    # Access Level
    access_level = fields.Selection([
        ('user', 'Records User'),
        ('manager', 'Records Manager'),
        ('admin', 'System Administrator')
    ], string='Access Level', required=True, default='user')
    
    # Additional Permissions
    naid_security_clearance = fields.Selection([
        ('level_1', 'Level 1 - Basic Access'),
        ('level_2', 'Level 2 - Standard Access'),
        ('level_3', 'Level 3 - Full Access')
    ], string='NAID Security Clearance', default='level_1')
    
    key_management_level = fields.Selection([
        ('none', 'No Key Access'),
        ('basic', 'Basic Keys'),
        ('department', 'Department Keys'),
        ('master', 'Master Keys')
    ], string='Key Management Level', default='none')
    
    # Portal Access
    create_portal_user = fields.Boolean(
        string='Create Portal User',
        default=True,
        help='Create portal access for external users'
    )
    
    # Custom Message
    invitation_message = fields.Text(
        string='Custom Message',
        help='Additional message to include in the invitation email'
    )
    
    # Expiration
    invitation_expires = fields.Date(
        string='Invitation Expires',
        default=lambda self: fields.Date.today() + fields.timedelta(days=7),
        help='Date when invitation expires'
    )

    @api.onchange('access_level')
    def _onchange_access_level(self):
        """Update default permissions based on access level"""
        if self.access_level == 'user':
            self.naid_security_clearance = 'level_1'
            self.key_management_level = 'basic'
        elif self.access_level == 'manager':
            self.naid_security_clearance = 'level_2'
            self.key_management_level = 'department'
        elif self.access_level == 'admin':
            self.naid_security_clearance = 'level_3'
            self.key_management_level = 'master'

    @api.constrains('email')
    def _check_email(self):
        """Validate email format"""
        for wizard in self:
            if wizard.email and '@' not in wizard.email:
                raise ValidationError(_("Please enter a valid email address."))

    def action_send_invitation(self):
        """Send the user invitation"""
        self.ensure_one()
        
        # Check if user already exists
        existing_user = self.env['res.users'].search([('email', '=', self.email)], limit=1)
        if existing_user:
            raise UserError(_("A user with email %s already exists.") % self.email)
        
        # Create user account
        user_vals = {
            'name': self.name,
            'login': self.email,
            'email': self.email,
            'active': True,
            'groups_id': self._get_user_groups(),
        }
        
        if self.create_portal_user:
            user_vals['groups_id'].append((4, self.env.ref('base.group_portal').id))
        
        new_user = self.env['res.users'].create(user_vals)
        
        # Create employee record if HR module is available
        if hasattr(self.env, 'hr.employee'):
            employee_vals = {
                'name': self.name,
                'work_email': self.email,
                'user_id': new_user.id,
                'department_id': self.department_id.hr_department_id.id if hasattr(self.department_id, 'hr_department_id') else False,
                'records_department_id': self.department_id.id,
                'naid_security_clearance': self.naid_security_clearance,
                'key_management_level': self.key_management_level,
            }
            self.env['hr.employee'].create(employee_vals)
        
        # Create invitation record for tracking
        invitation_vals = {
            'email': self.email,
            'name': self.name,
            'department_id': self.department_id.id,
            'access_level': self.access_level,
            'user_id': new_user.id,
            'invited_by': self.env.user.id,
            'invitation_date': fields.Datetime.now(),
            'expires_date': self.invitation_expires,
            'status': 'sent'
        }
        
        if hasattr(self.env, 'records.user.invitation'):
            invitation = self.env['records.user.invitation'].create(invitation_vals)
        
        # Send invitation email
        self._send_invitation_email(new_user)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Invitation Sent'),
                'message': _('User invitation has been sent to %s.') % self.email,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _get_user_groups(self):
        """Get appropriate user groups based on access level"""
        groups = []
        
        if self.access_level == 'user':
            groups.append((4, self.env.ref('records_management.group_records_user').id))
        elif self.access_level == 'manager':
            groups.extend([
                (4, self.env.ref('records_management.group_records_user').id),
                (4, self.env.ref('records_management.group_records_manager').id)
            ])
        elif self.access_level == 'admin':
            groups.extend([
                (4, self.env.ref('records_management.group_records_user').id),
                (4, self.env.ref('records_management.group_records_manager').id),
                (4, self.env.ref('base.group_system').id)
            ])
        
        return groups
    
    def _send_invitation_email(self, user):
        """Send the invitation email to the new user"""
        template = self.env.ref('records_management.email_template_user_invitation', False)
        
        if template:
            # Use email template if available
            ctx = {
                'user_name': self.name,
                'department_name': self.department_id.name,
                'access_level': self.access_level,
                'invitation_message': self.invitation_message or '',
                'expires_date': self.invitation_expires,
                'login_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            }
            template.with_context(ctx).send_mail(user.id, force_send=True)
        else:
            # Fallback email
            self._send_fallback_invitation_email(user)
    
    def _send_fallback_invitation_email(self, user):
        """Send a basic invitation email if no template is available"""
        subject = _('Invitation to Records Management System')
        
        body = f"""
        <p>Dear {self.name},</p>
        
        <p>You have been invited to join the Records Management System with the following details:</p>
        
        <ul>
            <li><strong>Department:</strong> {self.department_id.name}</li>
            <li><strong>Access Level:</strong> {self.access_level}</li>
            <li><strong>Security Clearance:</strong> {self.naid_security_clearance}</li>
        </ul>
        
        <p>Your login credentials:</p>
        <ul>
            <li><strong>Email/Login:</strong> {self.email}</li>
            <li><strong>Temporary Password:</strong> Please contact your administrator</li>
        </ul>
        
        <p>Please log in to the system using the link below:</p>
        <p><a href="{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web/login">Access Records Management System</a></p>
        
        {f"<p><strong>Additional Message:</strong><br/>{self.invitation_message}</p>" if self.invitation_message else ""}
        
        <p>This invitation expires on {self.invitation_expires}.</p>
        
        <p>If you have any questions, please contact your system administrator.</p>
        
        <p>Welcome to the team!</p>
        """
        
        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': self.email,
            'email_from': self.env.user.email,
        }
        
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
