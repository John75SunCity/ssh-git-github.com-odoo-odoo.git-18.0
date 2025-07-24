from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsLocation(models.Model):
    _name = 'records.location'
    _description = 'Records Storage Location'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    code = fields.Char('Location Code', required=False, index=True, help='Short code for this location (for barcode, reference, etc.)')
    name = fields.Char('Location Name', required=True)
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', recursive=True, store=True)
    parent_id = fields.Many2one('records.location', 'Parent Location', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('records.location', 'parent_id', 'Child Locations')

    # Location Type for Business Operations
    location_type = fields.Selection([
        ('aisles', 'Aisles - Standard File Boxes (Type 01)'),
        ('pallets', 'Pallets - Standard File Boxes (Type 01)'),
        ('vault', 'Vault - Specialty Boxes (Type 06)'),
        ('map', 'Map Storage - Map Boxes (Type 03)'),
        ('oversize', 'Oversize - Odd-Shaped Boxes (Type 04)'),
        ('refiles', 'Refiles - Staging for Returns/Put-Away'),
    ], string='Location Type', required=True, default='aisles',
       help="""Location type determines what kind of boxes can be stored:
       • Aisles/Pallets: Standard file boxes (Type 01) - monthly rent
       • Vault: Specialty boxes (Type 06) - secure storage
       • Map: Map boxes (Type 03) - oversized maps/plans
       • Oversize: Odd-shaped boxes (Type 04) - temporary storage during split
       • Refiles: Staging area for returned files before put-away""")

    box_ids = fields.One2many('records.box', 'location_id', string='Boxes')
    box_count = fields.Integer('Physical Box Count', compute='_compute_box_count', compute_sudo=False,
                              help="Actual number of boxes physically stored in this location")
    capacity = fields.Integer('Maximum Box Capacity', help="Maximum number of boxes this location can hold")
    current_utilization = fields.Float('Utilization %', compute='_compute_current_utilization', store=True, compute_sudo=False,
                                      help="Percentage of capacity utilized (box_count / capacity * 100) - shows storage efficiency")
    available_utilization = fields.Float('Available %', compute='_compute_available_utilization', store=True, compute_sudo=False,
                                         help="Percentage of capacity available (100 - current_utilization) - shows remaining space")
    available_spaces = fields.Integer('Available Spaces', compute='_compute_available_spaces', store=True, compute_sudo=False,
                                     help="Number of open spaces available (capacity - box_count) - actual quantity available")

    active = fields.Boolean(default=True)
    note = fields.Text('Notes')
    description = fields.Text(
        'Description',
        help='Detailed description of the location and its contents'
    )
    access_instructions = fields.Text(
        'Access Instructions',
        help='Instructions for accessing this location (keys, codes, etc.)'
    )
    security_level = fields.Selection([
        ('low', 'Low - General Access'),
        ('medium', 'Medium - Restricted Access'),
        ('high', 'High - Secure Access'),
        ('maximum', 'Maximum - Vault Access')
    ], string='Security Level', default='medium')

    # Phase 1 Critical Fields - Added by automated script
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    customer_id = fields.Many2one('res.partner', string='Customer')
    state = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], string='State', default='active')
    storage_date = fields.Date('Storage Date')

    # Phase 2 Audit & Compliance Fields - Added by automated script
    security_audit_ids = fields.One2many('records.security.audit', 'location_id', string='Security Audits')
    last_security_audit = fields.Date('Last Security Audit')
    security_certification = fields.Selection([('none', 'None'), ('basic', 'Basic Security'), ('enhanced', 'Enhanced Security'), ('maximum', 'Maximum Security')], string='Security Certification', default='basic')
    access_control_system = fields.Boolean('Access Control System', default=False)
    surveillance_system = fields.Boolean('Surveillance System', default=False)
    alarm_system = fields.Boolean('Alarm System', default=False)
    fire_detection_system = fields.Boolean('Fire Detection System', default=False)
    environmental_controls_verified = fields.Boolean('Environmental Controls Verified', default=False)
    temperature_controlled = fields.Boolean('Temperature Controlled', default=False)
    humidity_controlled = fields.Boolean('Humidity Controlled', default=False)
    pest_control_program = fields.Boolean('Pest Control Program', default=False)
    hazmat_compliance = fields.Boolean('HAZMAT Compliance', default=False)
    inspection_required = fields.Boolean('Regular Inspection Required', default=True)
    inspection_frequency = fields.Selection([('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly')], string='Inspection Frequency', default='monthly')
    last_inspection_date = fields.Date('Last Inspection Date')
    next_inspection_date = fields.Date('Next Inspection Date', compute='_compute_next_inspection')
    inspection_log_ids = fields.One2many('records.location.inspection', 'location_id', string='Inspection Log')
    compliance_violations_count = fields.Integer('Compliance Violations', compute='_compute_violations_count')

    # Phase 3: Analytics & Computed Fields (10 fields)
    space_utilization_efficiency = fields.Float(
        string='Space Efficiency (%)',
        compute='_compute_location_analytics',
        store=True,
        help='Space utilization efficiency rating'
    )
    storage_density_score = fields.Float(
        string='Storage Density Score',
        compute='_compute_location_analytics',
        store=True,
        help='Storage density optimization score (0-100)'
    )
    access_frequency_rating = fields.Float(
        string='Access Frequency Rating',
        compute='_compute_location_analytics',
        store=True,
        help='How frequently this location is accessed'
    )
    security_effectiveness = fields.Float(
        string='Security Effectiveness (%)',
        compute='_compute_location_analytics',
        store=True,
        help='Overall security system effectiveness'
    )
    operational_cost_per_box = fields.Float(
        string='Cost per Box ($/month)',
        compute='_compute_location_analytics',
        store=True,
        help='Monthly operational cost per box stored'
    )
    environmental_compliance_score = fields.Float(
        string='Environmental Score (%)',
        compute='_compute_location_analytics',
        store=True,
        help='Environmental controls compliance score'
    )
    storage_turnover_rate = fields.Float(
        string='Turnover Rate (%)',
        compute='_compute_location_analytics',
        store=True,
        help='Storage turnover rate indicating activity level'
    )
    risk_assessment_level = fields.Float(
        string='Risk Level (0-10)',
        compute='_compute_location_analytics',
        store=True,
        help='Comprehensive risk assessment score'
    )
    location_performance_summary = fields.Text(
        string='Performance Summary',
        compute='_compute_location_analytics',
        store=True,
        help='AI-generated performance insights'
    )
    analytics_last_computed = fields.Datetime(
        string='Analytics Updated',
        compute='_compute_location_analytics',
        store=True,
        help='Last analytics computation timestamp'
    )
    
    # Technical View Fields (for XML view inheritance and processing)
    arch = fields.Text(string='View Architecture', help='XML view architecture definition')
    context = fields.Text(string='Context', help='View context information')
    help = fields.Text(string='Help', help='Help text for this record')
    model = fields.Char(string='Model', help='Model name for technical references')
    res_model = fields.Char(string='Resource Model', help='Resource model name')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View', help='Search view reference')
    view_mode = fields.Char(string='View Mode', help='View mode configuration')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for location in self:
            if location.parent_id:
                location.complete_name = '%s / %s' % (location.parent_id.complete_name, location.name)
            else:
                location.complete_name = location.name

    @api.depends('box_ids')
    def _compute_box_count(self):
        for location in self:
            location.box_count = len(location.box_ids)

    @api.depends('box_ids', 'capacity')
    def _compute_current_utilization(self):
        """Calculate utilization percentage for storage efficiency analysis"""
        for location in self:
            if location.capacity and location.capacity > 0:
                location.current_utilization = (len(location.box_ids) / location.capacity) * 100
            else:
                location.current_utilization = 0.0

    @api.depends('current_utilization')
    def _compute_available_utilization(self):
        """Calculate available percentage (inverse of utilization)"""
        for location in self:
            location.available_utilization = 100.0 - location.current_utilization

    @api.depends('box_ids', 'capacity')
    def _compute_available_spaces(self):
        """Calculate number of available spaces (quantity based)"""
        for location in self:
            if location.capacity and location.capacity > 0:
                location.available_spaces = location.capacity - len(location.box_ids)
            else:
                location.available_spaces = 0

    @api.depends('box_ids', 'capacity', 'location_type', 'security_level',
                 'temperature_controlled', 'humidity_controlled', 'surveillance_system', 'access_control_system')
    def _compute_location_analytics(self):
        """Compute comprehensive analytics for storage locations"""
        for location in self:
            # Update timestamp
            location.analytics_last_computed = fields.Datetime.now()
            
            # Space utilization efficiency
            if location.capacity and location.capacity > 0:
                utilization = location.current_utilization
                if utilization <= 60:
                    location.space_utilization_efficiency = utilization + 20  # Bonus for not overpacking
                elif utilization <= 85:
                    location.space_utilization_efficiency = 100  # Optimal range
                else:
                    location.space_utilization_efficiency = max(70, 120 - utilization)  # Penalty for overpacking
            else:
                location.space_utilization_efficiency = 50.0  # No capacity defined
            
            # Storage density score
            box_count = len(location.box_ids)
            if box_count > 0 and location.capacity:
                density_ratio = box_count / location.capacity
                if density_ratio <= 0.85:  # Optimal density
                    location.storage_density_score = 95.0
                elif density_ratio <= 1.0:  # Full but manageable
                    location.storage_density_score = 85.0
                else:  # Overcrowded
                    location.storage_density_score = max(50, 85 - (density_ratio - 1.0) * 50)
            else:
                location.storage_density_score = 75.0
            
            # Access frequency rating (based on location type)
            type_access_map = {
                'refiles': 95.0,  # High access for staging
                'aisles': 80.0,   # Regular access
                'pallets': 70.0,  # Medium access
                'vault': 40.0,    # Low access - secure
                'map': 50.0,      # Occasional access
                'oversize': 85.0  # Temporary high access
            }
            location.access_frequency_rating = type_access_map.get(location.location_type, 65.0)
            
            # Security effectiveness
            security_score = 30.0  # Base score
            
            if location.access_control_system:
                security_score += 20.0
            if location.surveillance_system:
                security_score += 20.0
            if location.alarm_system:
                security_score += 15.0
            if location.fire_detection_system:
                security_score += 10.0
            
            # Security level bonus
            level_bonus = {
                'low': 0,
                'medium': 5,
                'high': 10,
                'maximum': 15
            }
            security_score += level_bonus.get(location.security_level, 0)
            
            location.security_effectiveness = min(100, security_score)
            
            # Operational cost per box
            base_cost = 5.0  # Base monthly cost per box
            
            # Adjust by location type
            type_cost_map = {
                'vault': 15.0,     # Premium storage
                'aisles': 5.0,     # Standard
                'pallets': 4.0,    # Efficient
                'map': 8.0,        # Specialized
                'oversize': 10.0,  # Temporary premium
                'refiles': 3.0     # Staging area
            }
            
            location.operational_cost_per_box = type_cost_map.get(location.location_type, base_cost)
            
            # Environmental compliance score
            env_score = 60.0  # Base score
            
            if location.temperature_controlled:
                env_score += 15.0
            if location.humidity_controlled:
                env_score += 15.0
            if location.pest_control_program:
                env_score += 10.0
            
            location.environmental_compliance_score = min(100, env_score)
            
            # Storage turnover rate (simulated based on location type)
            turnover_map = {
                'refiles': 150.0,  # Very high turnover
                'oversize': 100.0, # High turnover (temporary)
                'aisles': 25.0,    # Normal turnover
                'pallets': 20.0,   # Lower turnover
                'map': 10.0,       # Low turnover
                'vault': 5.0       # Very low turnover
            }
            location.storage_turnover_rate = turnover_map.get(location.location_type, 20.0)
            
            # Risk assessment level (0-10, lower is better)
            risk_score = 3.0  # Base risk
            
            # Increase risk for overcrowding
            if location.current_utilization > 90:
                risk_score += 2.0
            
            # Decrease risk for good security
            if location.security_effectiveness > 80:
                risk_score -= 1.0
            
            # Type-specific risks
            if location.location_type == 'oversize':
                risk_score += 1.0  # Temporary storage has higher risk
            elif location.location_type == 'vault':
                risk_score -= 0.5  # Secure storage has lower risk
            
            location.risk_assessment_level = max(0, min(10, risk_score))
            
            # Performance summary
            insights = []
            
            if location.space_utilization_efficiency > 90:
                insights.append("✅ Excellent space utilization")
            elif location.space_utilization_efficiency < 70:
                insights.append("⚠️ Poor space utilization - optimize layout")
            
            if location.current_utilization > 95:
                insights.append("🚨 Location overcrowded - expansion needed")
            elif location.current_utilization < 40:
                insights.append("📊 Underutilized - consider consolidation")
            
            if location.security_effectiveness < 70:
                insights.append("🔒 Security improvements recommended")
            else:
                insights.append("🛡️ Good security measures in place")
            
            if location.risk_assessment_level > 7:
                insights.append("⚠️ High risk level - immediate attention required")
            
            if location.environmental_compliance_score > 85:
                insights.append("🌡️ Excellent environmental controls")
            
            if not insights:
                insights.append("📈 All metrics within acceptable ranges")
            
            location.location_performance_summary = "\n".join(insights)

    def action_view_boxes(self):
        self.ensure_one()
        return {
            'name': _('Boxes'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.box',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id},
        }

    def action_location_report(self):
        """Generate a utilization and capacity report for this location."""
        self.ensure_one()
        return {
            'name': _('Location Report: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.location.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_location_id': self.id,
                'default_location_name': self.name,
                'default_include_child_locations': True,
            }
        }

    def action_relocate_boxes(self):
        """Relocate boxes from this location"""
        self.ensure_one()
        return {
            'name': _('Relocate Boxes'),
            'type': 'ir.actions.act_window',
            'res_model': 'box.relocation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_source_location_id': self.id},
        }

    def action_check_capacity(self):
        """Check location capacity"""
        self.ensure_one()
        self._compute_current_utilization()
        return True

    def action_view_child_locations(self):
        """View child locations"""
        self.ensure_one()
        return {
            'name': _('Child Locations'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.location',
            'view_mode': 'tree,form',
            'domain': [('parent_id', '=', self.id)],
            'context': {'default_parent_id': self.id},
        }

    def action_archive_location(self):
        """Archive this location"""
        self.ensure_one()
        if self.box_count > 0:
            raise ValidationError(_("Cannot archive location with boxes. Please relocate boxes first."))
        self.active = False
        return True

    def action_print_location_label(self):
        """Print location label"""
        self.ensure_one()
        return {
            'name': _('Print Location Label'),
            'type': 'ir.actions.report',
            'report_name': 'records_management.location_label_report',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.location_label_report',
            'context': {'active_ids': [self.id]},
        }

    def action_view_boxes(self):
        """View boxes in this location"""
        self.ensure_one()
        return {
            'name': _('Boxes in %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.box',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id},
        }

    def action_location_report(self):
        """Generate location report"""
        self.ensure_one()
        return {
            'name': _('Location Report: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'location.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_location_id': self.id},
        }
