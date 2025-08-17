# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    Visitor Management Module
    This module provides comprehensive visitor management for the Records Management:
    pass
System. It handles visitor registration, check-in/check-out processes, security
compliance, and audit trails with complete integration to facility access controls.
    Key Features
- Complete visitor lifecycle management
- Security clearance and badge tracking
- NAID compliance audit trails
- Integration with customer records
- Escort and access control management
- Real-time status tracking
    Business Processes
1. Visitor Registration: Schedule visits with proper authorization
2. Check-in Process: Identity verification and badge assignment
3. Facility Access: Controlled access with escort management
4. Check-out Process: Badge return and exit confirmation
5. Compliance Tracking: Complete audit trails for security compliance""":"
Author: Records Management System""
Version: 18.0.6.0.0""
License: LGPL-3""
    import logging""
    from odoo import models, fields, api, _""
    from odoo.exceptions import ValidationError""
    _logger = logging.getLogger(__name__)""
    class Visitor(models.Model):""
""
        Visitor Management""
    Track visitors to the records management facility with complete""
        security compliance and audit trail capabilities.""
    ""
    _name = "visitor"
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "visitor"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "visitor"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Visitor Management'"
    _inherit = ['mail.thread', 'mail.activity.mixin']"
    _order = 'visit_date desc, name'"
    _rec_name = "name"
""
        # ============================================================================ """"
    # CORE IDENTIFICATION FIELDS"""""
        # ============================================================================ """"
    name = fields.Char("""""
        string='Visitor Name',"
        required=True,""
        tracking=True,""
        index=True,""
        help="Full name of the visitor"
    ""
    description = fields.Text(""
        string='Visit Details',"
        tracking=True,""
        help="Detailed description of the visit purpose"
    ""
    active = fields.Boolean(""
        string='Active',"
        default=True,""
        tracking=True,""
        help="Active status of visitor record"
    ""
""
        # ============================================================================ """"
    # FRAMEWORK FIELDS"""""
        # ============================================================================ """"
    company_id = fields.Many2one("""""
        'res.company',"
        string='Company',"
        default=lambda self: self.env.company,""
        required=True,""
        help="Company where visit is taking place"
    ""
    user_id = fields.Many2one(""
        'res.users',"
        string='Host/Responsible User',"
        default=lambda self: self.env.user,""
        tracking=True,""
        help="User responsible for this visitor":
    ""
""
        # ============================================================================ """"
    # VISITOR INFORMATION"""""
        # ============================================================================ """"
    visitor_company = fields.Char("""""
        string='Visitor Company',"
        tracking=True,""
        help="Company or organization the visitor represents"
    ""
    phone = fields.Char(""
        string='Phone Number',"
        tracking=True,""
        help="Contact phone number"
    ""
    email = fields.Char(""
        string='Email',"
        tracking=True,""
        help="Contact email address"
    ""
""
        # Identification""
    ,""
    id_type = fields.Selection([))""
        ('drivers_license', "Driver's License"),'
        ('passport', 'Passport'),"
        ('state_id', 'State ID'),"
        ('company_id', 'Company ID'),"
        ('other', 'Other')"
    ""
""
    id_number = fields.Char(""
        string='ID Number',"
        tracking=True,""
        help="Identification number or reference"
    ""
""
        # ============================================================================ """"
    # VISIT DETAILS"""""
        # ============================================================================ """"
    visit_date = fields.Date("""""
        string='Visit Date',"
        default=fields.Date.today,""
        required=True,""
        tracking=True,""
        index=True,""
        help="Scheduled date of visit"
    ""
    check_in_time = fields.Datetime(""
        string='Check-in Time',"
        tracking=True,""
        help="Actual check-in time"
    ""
    check_out_time = fields.Datetime(""
        string='Check-out Time',"
        tracking=True,""
        help="Actual check-out time"
    ""
""
    ,""
    visit_purpose = fields.Selection([))""
        ('customer_visit', 'Customer Visit'),"
        ('audit', 'Audit'),"
        ('inspection', 'Inspection'),"
        ('maintenance', 'Maintenance'),"
        ('delivery', 'Delivery'),"
        ('pickup', 'Pickup'),"
        ('meeting', 'Meeting'),"
        ('naid_inspection', 'NAID Inspection'),"
        ('compliance_review', 'Compliance Review'),"
        ('other', 'Other')"
    ""
        help="Primary purpose of the visit"
""
    # ============================================================================ """"
        # LOCATION ACCESS"""""
    # ============================================================================ """"
    areas_accessed = fields.Text("""""
        string='Areas Accessed',"
        tracking=True,""
        help="List of facility areas visited"
    ""
    escort_required = fields.Boolean(""
        string='Escort Required',"
        default=True,""
        tracking=True,""
        help="Whether visitor requires an escort"
    ""
    escort_assigned_id = fields.Many2one(""
        'res.users',"
        string='Assigned Escort',"
        tracking=True,""
        help="Staff member assigned to escort visitor"
    ""
""
        # ============================================================================ """"
    # STATUS MANAGEMENT"""""
        # ============================================================================ """"
    ,"""""
    status = fields.Selection([))""
        ('scheduled', 'Scheduled'),"
        ('checked_in', 'Checked In'),"
        ('in_facility', 'In Facility'),"
        ('checked_out', 'Checked Out'),"
        ('no_show', 'No Show')"
    ""
        help="Current status of the visit"
""
    # ============================================================================ """"
        # RELATIONSHIP FIELDS"""""
    # ============================================================================ """"
    partner_id = fields.Many2one("""""
        "res.partner",
        string="Related Customer",
        ,""
    domain=[("is_company", "= """", True))"
        tracking=True,""
        help=""""Customer or partner associated with this visit"
    ""
""
        # ============================================================================ """"
    # SECURITY AND COMPLIANCE"""""
        # ============================================================================ """"
    background_check = fields.Boolean("""""
        string='Background Check Required',"
        tracking=True,""
        help="Whether background check is required"
    ""
    background_check_passed = fields.Boolean(""
        string='Background Check Passed',"
        tracking=True,""
        help="Whether background check was successfully completed"
    ""
    safety_briefing = fields.Boolean(""
        string='Safety Briefing Given',"
        tracking=True,""
        help="Whether safety briefing was provided"
    ""
""
        # Badge information""
    badge_number = fields.Char(""
        string='Visitor Badge Number',"
        tracking=True,""
        help="Number of visitor badge assigned"
    ""
    badge_returned = fields.Boolean(""
        string='Badge Returned',"
        tracking=True,""
        help="Whether visitor badge was returned"
    ""
""
        # NAID Compliance""
    naid_compliance_verified = fields.Boolean(""
        string='NAID Compliance Verified',"
        tracking=True,""
        help="Whether NAID compliance requirements were verified"
    ""
    ,""
    access_level = fields.Selection([))""
        ('public', 'Public Areas Only'),"
        ('restricted', 'Restricted Areas'),"
        ('secure', 'Secure Areas'),"
        ('vault', 'Vault Access')"
    ""
        help="Level of facility access granted"
""
    # ============================================================================ """"
        # DOCUMENTATION"""""
    # ============================================================================ """"
    notes = fields.Text("""""
        string='Visit Notes',"
        tracking=True,""
        help="General notes about the visit"
    ""
    security_notes = fields.Text(""
        string='Security Notes',"
        tracking=True,""
        help="Security-related observations and notes"
    ""
""
        # ============================================================================ """"
    # COMPUTED FIELDS"""""
        # ============================================================================ """"
    visit_duration = fields.Float("""""
    string='Visit Duration (Hours)',"
        compute='_compute_visit_duration',"
        store=True,""
        help="Duration of visit in hours"
    ""
    display_name = fields.Char(""
        string='Display Name',"
        compute='_compute_display_name',"
        store=True,""
        help="Display name for visitor record":
    ""
""
        # ============================================================================ """"
    # MAIL THREAD FRAMEWORK FIELDS"""""
        # ============================================================================ """"
    activity_ids = fields.One2many("""""
        "mail.activity",
        "res_id",
        string="Activities",
        ,""
    domain=lambda self: [("res_model", "= """", self._name)),"
    ""
    message_follower_ids = fields.One2many(""
        """"mail.followers",
        "res_id",
        string="Followers",
        ,""
    domain=lambda self: [("res_model", "= """", self._name)),"
    ""
    message_ids = fields.One2many(""
        """"mail.message",
        "res_id",
        string="Messages",
        ,""
    domain=lambda self: [("model", "= """", self._name))"
    context = fields.Char(string='"""
""""
        """Compute visit duration in hours"""
    """
"""    def _compute_display_name(self):"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        """Compute display name"""
""""
""""
""""
        """Check in visitor"""
""""
""""
    """    def action_enter_facility(self):"
        """Mark visitor as entered facility"""
""""
""""
    """"
        """Check out visitor"""
""""
""""
    """    def action_mark_no_show(self):"
        """Mark visitor as no show"""
""""
""""
    """"
        """Assign visitor badge"""
""""
""""
    """    def action_return_badge(self):"
        """Mark badge as returned"""
""""
""""
""""
        """Generate unique visitor badge number"""
        return sequence or f"VB{self.id:06d}"
""
    def _create_audit_log(self, event_type):""
        """Create audit log entry for visitor activity"""
""""
""""
"""                'description': f"Visitor {self.name} - {event_type}","
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
    def get_visit_summary(self):""
        """Get visit summary for reporting"""
""""
"""
        """Validate visit times"""
    """"
"""    def _check_background_verification(self):"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        """Validate background check requirements"""
""""
""""
""""
        """Ensure badge numbers are unique"""
"""                    ('badge_number', '= """', record.badge_number),""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
                    ('"""id', '!= """
                    ('"""badge_returned', '= """
"""                    raise ValidationError(_('"""
"""
"""    def get_active_visitors(self):"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        """Get currently active visitors in facility"""
"""            ('visit_date', '= """
""""
    """"
""""""
        """Get visitors who haven't checked out"""
"""            ('visit_date', '<= """', yesterday),""
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
            ('"""
    """    def send_checkout_reminder(self):"
        """Send checkout reminder for overdue visitors"""
"""
""""
    """"
""""