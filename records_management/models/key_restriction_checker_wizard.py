from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
import logging

_logger = logging.getLogger(__name__)

class KeyRestrictionCheckerWizard(models.TransientModel):
    """
    Wizard for checking key restrictions and access permissions.
    
    This wizard validates whether a user has proper authorization to access
    specific keys, containers, or restricted areas based on their clearance level.
    """
    
    _name = 'key.restriction.checker.wizard'
    _description = 'Key Restriction Checker Wizard'

    # User/Employee Information
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
        help='Employee requesting key access'
    )
    
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User Account',
        related='employee_id.user_id',
        readonly=True
    )
    
    # Key/Access Information
    key_type = fields.Selection([
        ('master', 'Master Key'),
        ('department', 'Department Key'),
        ('container', 'Container Key'),
        ('location', 'Location Key'),
        ('special', 'Special Access Key'),
        ('emergency', 'Emergency Key')
    ], string='Key Type', required=True)
    
    key_identifier = fields.Char(
        string='Key Identifier',
        required=True,
        help='Key number, barcode, or identifier'
    )
    
    # Access Context
    requested_location_id = fields.Many2one(
        comodel_name='records.location',
        string='Requested Location',
        help='Location where key access is requested'
    )
    
    requested_department_id = fields.Many2one(
        comodel_name='records.department',
        string='Requested Department',
        help='Department for which access is requested'
    )
    
    container_id = fields.Many2one(
        comodel_name='records.container',
        string='Container',
        help='Specific container requiring access'
    )
    
    # Request Details
    access_reason = fields.Selection([
        ('retrieval', 'Document Retrieval'),
        ('storage', 'Document Storage'),
        ('maintenance', 'Maintenance Work'),
        ('audit', 'Audit/Inspection'),
        ('emergency', 'Emergency Access'),
        ('other', 'Other')
    ], string='Access Reason', required=True, default='retrieval')
    
    detailed_reason = fields.Text(
        string='Detailed Reason',
        help='Provide detailed explanation for key access request'
    )
    
    # Time-based Restrictions
    requested_start_time = fields.Datetime(
        string='Requested Start Time',
        default=fields.Datetime.now,
        required=True
    )
    
    requested_end_time = fields.Datetime(
        string='Requested End Time',
        help='When access should expire (leave empty for indefinite)'
    )
    
    # Computed Fields - Employee Clearance
    employee_clearance_level = fields.Selection(
        related='employee_id.naid_security_clearance',
        string='Employee Clearance Level',
        readonly=True
    )
    
    employee_certification_status = fields.Selection(
        related='employee_id.certification_status',
        string='Certification Status',
        readonly=True
    )
    
    employee_department_id = fields.Many2one(
        related='employee_id.department_id',
        string='Employee Department',
        readonly=True
    )
    
    # Results
    access_granted = fields.Boolean(
        string='Access Granted',
        compute='_compute_access_decision',
        store=True
    )
    
    restriction_reason = fields.Text(
        string='Restriction Reason',
        compute='_compute_access_decision',
        store=True,
        help='Reason why access was denied'
    )
    
    supervisor_approval_required = fields.Boolean(
        string='Supervisor Approval Required',
        compute='_compute_access_decision',
        store=True
    )
    
    override_available = fields.Boolean(
        string='Override Available',
        compute='_compute_access_decision',
        store=True
    )

    @api.depends('employee_id', 'key_type', 'requested_location_id', 'requested_department_id', 
                 'container_id', 'access_reason', 'requested_start_time', 'requested_end_time')
    def _compute_access_decision(self):
        """Compute whether access should be granted based on restrictions"""
        for wizard in self:
            wizard.access_granted = False
            wizard.restriction_reason = ""
            wizard.supervisor_approval_required = False
            wizard.override_available = False
            
            if not wizard.employee_id:
                wizard.restriction_reason = "No employee specified"
                continue
            
            # Check basic employee status
            if not wizard.employee_id.active:
                wizard.restriction_reason = "Employee is inactive"
                continue
            
            # Check certification status
            if wizard.employee_certification_status not in ['certified', 'provisional']:
                wizard.restriction_reason = "Employee lacks required certification"
                wizard.supervisor_approval_required = True
                continue
            
            # Check clearance level for different key types
            clearance_requirements = {
                'master': 'level_3',
                'department': 'level_2',
                'container': 'level_1',
                'location': 'level_1',
                'special': 'level_3',
                'emergency': 'level_2'
            }
            
            required_clearance = clearance_requirements.get(wizard.key_type, 'level_1')
            employee_clearance = wizard.employee_clearance_level or 'none'
            
            # Clearance hierarchy check
            clearance_hierarchy = {
                'none': 0,
                'level_1': 1,
                'level_2': 2,
                'level_3': 3
            }
            
            if clearance_hierarchy.get(employee_clearance, 0) < clearance_hierarchy.get(required_clearance, 0):
                wizard.restriction_reason = f"Insufficient clearance level. Required: {required_clearance}, Employee has: {employee_clearance}"
                wizard.supervisor_approval_required = True
                continue
            
            # Department-based restrictions
            if wizard.requested_department_id and wizard.employee_department_id:
                if wizard.requested_department_id.id != wizard.employee_department_id.id:
                    # Check if employee has cross-department access
                    if not wizard._check_cross_department_access():
                        wizard.restriction_reason = "Cross-department access not authorized"
                        wizard.supervisor_approval_required = True
                        continue
            
            # Time-based restrictions
            if wizard.requested_end_time and wizard.requested_start_time:
                if wizard.requested_end_time <= wizard.requested_start_time:
                    wizard.restriction_reason = "Invalid time range"
                    continue
            
            # Emergency access special rules
            if wizard.access_reason == 'emergency':
                wizard.access_granted = True
                wizard.override_available = True
                continue
            
            # Location-based restrictions
            if wizard.requested_location_id:
                if not wizard._check_location_access():
                    wizard.restriction_reason = "Location access restricted"
                    wizard.supervisor_approval_required = True
                    continue
            
            # Container-specific restrictions
            if wizard.container_id:
                if not wizard._check_container_access():
                    wizard.restriction_reason = "Container access restricted"
                    wizard.supervisor_approval_required = True
                    continue
            
            # If all checks pass
            wizard.access_granted = True
    
    def _check_cross_department_access(self):
        """Check if employee has authorization for cross-department access"""
        # This would check employee's additional permissions or roles
        # For now, return False (no cross-department access by default)
        return False
    
    def _check_location_access(self):
        """Check location-specific access restrictions"""
        if not self.requested_location_id:
            return True
        
        # Check if location has specific access restrictions
        location = self.requested_location_id
        
        # Example: Some locations might require special clearance
        restricted_locations = location.search([('name', 'ilike', 'vault'), 
                                               ('name', 'ilike', 'secure'),
                                               ('name', 'ilike', 'restricted')])
        
        if location.id in restricted_locations.ids:
            if self.employee_clearance_level != 'level_3':
                return False
        
        return True
    
    def _check_container_access(self):
        """Check container-specific access restrictions"""
        if not self.container_id:
            return True
        
        container = self.container_id
        
        # Check if container requires special access
        if hasattr(container, 'access_level'):
            required_level = container.access_level
            employee_level = self.employee_clearance_level or 'none'
            
            clearance_hierarchy = {
                'none': 0,
                'level_1': 1,
                'level_2': 2,
                'level_3': 3
            }
            
            if clearance_hierarchy.get(employee_level, 0) < clearance_hierarchy.get(required_level, 0):
                return False
        
        return True

    def action_grant_access(self):
        """Grant key access if authorized"""
        self.ensure_one()
        
        if not self.access_granted and not self.override_available:
            raise AccessError(_("Access cannot be granted: %s") % self.restriction_reason)
        
        # Create access log entry
        access_log_vals = {
            'employee_id': self.employee_id.id,
            'key_type': self.key_type,
            'key_identifier': self.key_identifier,
            'location_id': self.requested_location_id.id if self.requested_location_id else False,
            'department_id': self.requested_department_id.id if self.requested_department_id else False,
            'container_id': self.container_id.id if self.container_id else False,
            'access_reason': self.access_reason,
            'detailed_reason': self.detailed_reason,
            'start_time': self.requested_start_time,
            'end_time': self.requested_end_time,
            'granted_by': self.env.user.id,
            'access_granted': True
        }
        
        # Create access log (if model exists)
        if hasattr(self.env, 'key.access.log'):
            access_log = self.env['key.access.log'].create(access_log_vals)
        
        # Send notification if required
        if self.supervisor_approval_required:
            self._notify_supervisor_override()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Access Granted'),
                'message': _('Key access has been granted to %s.') % self.employee_id.name,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_deny_access(self):
        """Deny key access"""
        self.ensure_one()
        
        # Create denial log entry
        access_log_vals = {
            'employee_id': self.employee_id.id,
            'key_type': self.key_type,
            'key_identifier': self.key_identifier,
            'access_reason': self.access_reason,
            'detailed_reason': self.detailed_reason,
            'denied_by': self.env.user.id,
            'denial_reason': self.restriction_reason,
            'access_granted': False
        }
        
        # Create access log (if model exists)
        if hasattr(self.env, 'key.access.log'):
            access_log = self.env['key.access.log'].create(access_log_vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Access Denied'),
                'message': _('Key access denied: %s') % self.restriction_reason,
                'type': 'warning',
                'sticky': True,
            }
        }
    
    def _notify_supervisor_override(self):
        """Notify supervisor about access override"""
        if not self.employee_id.parent_id:
            return
        
        # Create activity for supervisor
        self.employee_id.parent_id.activity_schedule(
            'records_management.mail_activity_key_override',
            note=f"Key access override granted for {self.employee_id.name}\n"
                 f"Key Type: {self.key_type}\n"
                 f"Reason: {self.detailed_reason}",
            user_id=self.employee_id.parent_id.user_id.id if self.employee_id.parent_id.user_id else self.env.user.id
        )
