# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MobileBinKeyWizard(models.TransientModel):
    """
    Mobile Bin Key Wizard - Manages mobile access keys for bin operations.
    Provides functionality for generating, validating, and managing temporary
    access keys for mobile devices accessing shredding bins and containers.
    """
    _name = 'mobile.bin.key.wizard'
    _description = 'Mobile Bin Key Wizard'

    # Basic Information
    name = fields.Char(
        string='Key Generation Request',
        default='Mobile Bin Key Request',
        readonly=True
    )
    
    # User and Device Information
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True,
        help="User requesting mobile access key"
    )
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        related='user_id.employee_id',
        store=True,
        help="Employee record for the user"
    )
    
    device_id = fields.Char(
        string='Device ID',
        required=True,
        help="Unique identifier for the mobile device"
    )
    
    device_name = fields.Char(
        string='Device Name',
        help="Human-readable name for the device (e.g., 'John's iPhone')"
    )
    
    # Access Configuration
    access_type = fields.Selection([
        ('bin_scan', 'Bin Scanning'),
        ('container_access', 'Container Access'),
        ('audit_trail', 'Audit Trail'),
        ('full_mobile', 'Full Mobile Access'),
    ], string='Access Type', required=True, default='bin_scan',
       help="Type of mobile access being requested")
    
    # Target Resources
    bin_ids = fields.Many2many(
        'shredding.service.bin',
        string='Authorized Bins',
        help="Specific bins this key can access (leave empty for all authorized bins)"
    )
    
    location_ids = fields.Many2many(
        'records.location',
        string='Authorized Locations',
        help="Locations where this mobile key is valid"
    )
    
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        help="Department scope for access"
    )
    
    # Key Configuration
    key_duration = fields.Selection([
        ('1_hour', '1 Hour'),
        ('4_hours', '4 Hours'),
        ('8_hours', '8 Hours'),
        ('24_hours', '24 Hours'),
        ('7_days', '7 Days'),
        ('30_days', '30 Days'),
        ('custom', 'Custom Duration'),
    ], string='Key Duration', default='8_hours', required=True,
       help="How long the mobile key should remain valid")
    
    custom_duration_hours = fields.Integer(
        string='Custom Duration (Hours)',
        help="Custom duration in hours (only used if 'Custom Duration' is selected)"
    )
    
    # Security Settings
    require_pin = fields.Boolean(
        string='Require PIN',
        default=True,
        help="Require PIN entry for key usage"
    )
    
    pin_code = fields.Char(
        string='PIN Code',
        size=6,
        help="4-6 digit PIN code for additional security"
    )
    
    allow_offline = fields.Boolean(
        string='Allow Offline Usage',
        default=False,
        help="Allow key to work when device is offline"
    )
    
    single_use = fields.Boolean(
        string='Single Use Key',
        default=False,
        help="Key expires after first use"
    )
    
    # Generated Key Information
    generated_key = fields.Char(
        string='Generated Key',
        readonly=True,
        help="The generated mobile access key"
    )
    
    qr_code = fields.Binary(
        string='QR Code',
        readonly=True,
        help="QR code for easy mobile key setup"
    )
    
    # Validity Information
    valid_from = fields.Datetime(
        string='Valid From',
        default=fields.Datetime.now,
        required=True
    )
    
    valid_until = fields.Datetime(
        string='Valid Until',
        required=True
    )
    
    # Status and Usage
    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ], string='State', default='draft', readonly=True)
    
    usage_count = fields.Integer(
        string='Usage Count',
        default=0,
        readonly=True,
        help="Number of times this key has been used"
    )
    
    last_used = fields.Datetime(
        string='Last Used',
        readonly=True
    )
    
    # Restrictions and Notes
    restrictions = fields.Text(
        string='Access Restrictions',
        help="Additional restrictions or notes for this mobile key"
    )
    
    notes = fields.Text(
        string='Notes',
        help="Additional notes or comments"
    )
    
    @api.onchange('key_duration')
    def _onchange_key_duration(self):
        """Calculate valid_until based on duration"""
        if self.key_duration and self.key_duration != 'custom':
            duration_map = {
                '1_hour': 1,
                '4_hours': 4,
                '8_hours': 8,
                '24_hours': 24,
                '7_days': 168,  # 7 * 24
                '30_days': 720,  # 30 * 24
            }
            
            if self.key_duration in duration_map:
                hours = duration_map[self.key_duration]
                self.valid_until = fields.Datetime.now() + \
                    fields.Datetime.from_string('1970-01-01 00:00:00').replace(hour=hours)
    
    @api.onchange('custom_duration_hours')
    def _onchange_custom_duration(self):
        """Update valid_until for custom duration"""
        if self.key_duration == 'custom' and self.custom_duration_hours:
            from datetime import timedelta
            self.valid_until = fields.Datetime.now() + timedelta(hours=self.custom_duration_hours)
    
    @api.onchange('require_pin', 'pin_code')
    def _onchange_pin_requirements(self):
        """Validate PIN code format"""
        if self.require_pin and self.pin_code:
            if not self.pin_code.isdigit() or len(self.pin_code) < 4 or len(self.pin_code) > 6:
                return {
                    'warning': {
                        'title': _('Invalid PIN'),
                        'message': _('PIN must be 4-6 digits')
                    }
                }
    
    def action_generate_key(self):
        """Generate the mobile access key"""
        self.ensure_one()
        
        # Validate requirements
        if not self.device_id:
            raise UserError(_("Device ID is required"))
        
        if not self.valid_until or self.valid_until <= fields.Datetime.now():
            raise UserError(_("Valid until date must be in the future"))
        
        if self.require_pin and not self.pin_code:
            raise UserError(_("PIN code is required when PIN authentication is enabled"))
        
        # Generate unique key
        import secrets
        import string
        
        # Create a secure random key
        alphabet = string.ascii_letters + string.digits
        key_length = 32
        self.generated_key = ''.join(secrets.choice(alphabet) for _ in range(key_length))
        
        # Generate QR code (simulated - in real implementation would use qrcode library)
        self._generate_qr_code()
        
        # Update state
        self.state = 'generated'
        
        # Create audit log
        self._create_audit_log('key_generated')
        
        # Send notification to user
        self._send_key_notification()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Key Generated'),
                'message': _('Mobile access key generated successfully'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _generate_qr_code(self):
        """Generate QR code for the mobile key"""
        # In a real implementation, this would use a QR code library
        # For now, we'll create a placeholder
        key_data = {
            'key': self.generated_key,
            'user': self.user_id.login,
            'valid_until': self.valid_until.isoformat(),
            'access_type': self.access_type,
        }
        
        # This would generate actual QR code binary data
        self.qr_code = b"QR_CODE_PLACEHOLDER_DATA"
    
    def action_activate_key(self):
        """Activate the generated key"""
        self.ensure_one()
        
        if self.state != 'generated':
            raise UserError(_("Only generated keys can be activated"))
        
        if self.valid_until <= fields.Datetime.now():
            raise UserError(_("Cannot activate an expired key"))
        
        self.state = 'active'
        self._create_audit_log('key_activated')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Key Activated'),
                'message': _('Mobile access key is now active'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_revoke_key(self):
        """Revoke the mobile key"""
        self.ensure_one()
        
        if self.state in ['expired', 'revoked']:
            raise UserError(_("Key is already inactive"))
        
        self.state = 'revoked'
        self._create_audit_log('key_revoked')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Key Revoked'),
                'message': _('Mobile access key has been revoked'),
                'type': 'info',
                'sticky': False,
            }
        }
    
    def action_extend_validity(self):
        """Extend the validity period of the key"""
        self.ensure_one()
        
        if self.state not in ['generated', 'active']:
            raise UserError(_("Only generated or active keys can be extended"))
        
        # Open wizard to select new expiration
        return {
            'type': 'ir.actions.act_window',
            'name': _('Extend Key Validity'),
            'res_model': 'mobile.bin.key.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_extend_mode': True}
        }
    
    def _create_audit_log(self, action):
        """Create audit log entry"""
        try:
            self.env['naid.audit.log'].create({
                'name': _('Mobile Key %s - %s') % (action.title(), self.device_name or self.device_id),
                'action': 'mobile_key_%s' % action,
                'user_id': self.env.user.id,
                'notes': _('Mobile key %s for device %s, access type: %s') % (
                    action, self.device_id, self.access_type
                ),
                'audit_date': fields.Datetime.now(),
            })
        except Exception:
            # Continue if audit logging fails
            pass
    
    def _send_key_notification(self):
        """Send notification email with key details"""
        try:
            template = self.env.ref('records_management.mobile_key_notification_template', False)
            if template:
                template.send_mail(self.id)
        except Exception:
            # Continue if email sending fails
            pass
    
    @api.model
    def cleanup_expired_keys(self):
        """Cleanup expired keys (called by scheduled action)"""
        expired_keys = self.search([
            ('state', 'in', ['generated', 'active']),
            ('valid_until', '<', fields.Datetime.now())
        ])
        
        for key in expired_keys:
            key.state = 'expired'
            key._create_audit_log('key_expired')
        
        return True
