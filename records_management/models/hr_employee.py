# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime, timedelta


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
    
    # Phase 3: HR Analytics & Performance Fields
    
    # Performance Analytics
    records_handling_efficiency = fields.Float(
        string='Records Handling Efficiency %',
        compute='_compute_performance_analytics',
        store=True,
        help='Efficiency score for records management tasks'
    )
    
    productivity_score = fields.Float(
        string='Productivity Score',
        compute='_compute_performance_analytics',
        store=True,
        help='Overall productivity assessment (0-100)'
    )
    
    # Training Analytics  
    skill_development_index = fields.Float(
        string='Skill Development Index',
        compute='_compute_training_analytics',
        store=True,
        help='Index measuring skill progression and development'
    )
    
    compliance_training_status = fields.Selection([
        ('up_to_date', 'Up to Date'),
        ('due_soon', 'Due Soon'),
        ('overdue', 'Overdue'),
        ('not_required', 'Not Required')
    ], string='Compliance Training Status',
       compute='_compute_training_analytics',
       store=True,
       help='Current compliance training status')
    
    # Specialization Analytics
    records_specialization_score = fields.Float(
        string='Records Specialization Score',
        compute='_compute_specialization_analytics',
        store=True,
        help='Specialization level in records management'
    )
    
    @api.depends('user_id')
    def _compute_imported_user_count(self):
        """Compute number of users imported by this employee."""
        for employee in self:
            # Implementation will be added when user import model is created
            employee.imported_user_count = 0
    
    @api.depends('records_management_role', 'portal_access_level', 'user_id')
    def _compute_performance_analytics(self):
        """Compute performance analytics for records management"""
        for employee in self:
            # Base efficiency score based on role
            role_efficiency = {
                'manager': 85,      # High responsibility, high efficiency expected
                'supervisor': 80,   # Good efficiency expected
                'operator': 75,     # Standard efficiency
                'viewer': 60        # Limited interaction
            }
            
            base_efficiency = role_efficiency.get(employee.records_management_role, 70)
            
            # Access level factor
            access_factors = {
                'admin': 15,        # Full access suggests higher capability
                'advanced': 10,     # Good access level
                'basic': 0          # Standard access
            }
            
            access_bonus = access_factors.get(employee.portal_access_level, 0)
            
            # User import capability bonus
            if employee.can_import_users:
                access_bonus += 5
            
            # Recent activity bonus (simplified - would track actual activity)
            activity_bonus = 5 if employee.last_import_date else 0
            
            total_efficiency = base_efficiency + access_bonus + activity_bonus
            employee.records_handling_efficiency = min(max(total_efficiency, 0), 100)
            
            # Productivity score based on role and responsibilities
            productivity = employee.records_handling_efficiency
            
            # Role-specific productivity expectations
            if employee.records_management_role == 'manager':
                # Managers should have consistent high productivity
                if productivity >= 90:
                    productivity += 5
                elif productivity < 75:
                    productivity -= 10
            elif employee.records_management_role == 'supervisor':
                # Supervisors need balanced productivity
                if 80 <= productivity <= 95:
                    productivity += 3
            
            employee.productivity_score = min(max(productivity, 0), 100)
    
    @api.depends('records_management_role', 'portal_access_level')
    def _compute_training_analytics(self):
        """Compute training and skill development analytics"""
        for employee in self:
            # Skill development based on role progression
            role_skills = {
                'viewer': 20,       # Basic skills
                'operator': 50,     # Intermediate skills
                'supervisor': 75,   # Advanced skills
                'manager': 90       # Expert skills
            }
            
            base_skill = role_skills.get(employee.records_management_role, 30)
            
            # Access level indicates training completion
            access_training = {
                'basic': 0,
                'advanced': 15,     # Additional training completed
                'admin': 25         # Comprehensive training
            }
            
            training_bonus = access_training.get(employee.portal_access_level, 0)
            
            # Import capability indicates specialized training
            if employee.can_import_users:
                training_bonus += 10
            
            skill_index = base_skill + training_bonus
            employee.skill_development_index = min(skill_index, 100)
            
            # Compliance training status assessment
            # In real implementation, would check actual training records
            if employee.records_management_role in ['manager', 'supervisor']:
                # Higher roles need current compliance training
                if employee.skill_development_index >= 80:
                    employee.compliance_training_status = 'up_to_date'
                elif employee.skill_development_index >= 60:
                    employee.compliance_training_status = 'due_soon'
                else:
                    employee.compliance_training_status = 'overdue'
            elif employee.records_management_role == 'operator':
                # Operators need regular training
                if employee.skill_development_index >= 70:
                    employee.compliance_training_status = 'up_to_date'
                else:
                    employee.compliance_training_status = 'due_soon'
            else:
                # Viewers have minimal requirements
                employee.compliance_training_status = 'not_required'
    
    @api.depends('records_management_role', 'portal_access_level', 'can_import_users')
    def _compute_specialization_analytics(self):
        """Compute records management specialization analytics"""
        for employee in self:
            # Base specialization from role
            role_specialization = {
                'manager': 80,      # High specialization expected
                'supervisor': 65,   # Good specialization
                'operator': 45,     # Moderate specialization
                'viewer': 20        # Basic specialization
            }
            
            base_spec = role_specialization.get(employee.records_management_role, 30)
            
            # Access level indicates deeper system knowledge
            access_specialization = {
                'admin': 15,        # Deep system knowledge
                'advanced': 10,     # Good system knowledge
                'basic': 0          # Standard knowledge
            }
            
            access_spec = access_specialization.get(employee.portal_access_level, 0)
            
            # Special capabilities indicate expertise
            capability_bonus = 0
            if employee.can_import_users:
                capability_bonus += 8  # Specialized skill
            
            # Experience factor (based on import history)
            experience_bonus = 0
            if employee.imported_user_count > 10:
                experience_bonus = 7
            elif employee.imported_user_count > 5:
                experience_bonus = 4
            elif employee.imported_user_count > 0:
                experience_bonus = 2
            
            total_specialization = base_spec + access_spec + capability_bonus + experience_bonus
            employee.records_specialization_score = min(max(total_specialization, 0), 100)
