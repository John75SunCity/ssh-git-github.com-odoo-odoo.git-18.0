from odoo import models, fields, api
from datetime import datetime, timedelta

class RecordsBoxMovement(models.Model):
    _name = 'records.box.movement'
    _description = 'Box Movement History'
    _order = 'movement_date desc'

    box_id = fields.Many2one('records.box', string='Box', required=True, ondelete='cascade')
    movement_date = fields.Datetime('Movement Date', required=True, default=fields.Datetime.now)
    from_location_id = fields.Many2one('records.location', string='From Location')
    to_location_id = fields.Many2one('records.location', string='To Location', required=True)
    movement_type = fields.Selection([
        ('storage', 'Initial Storage'),
        ('transfer', 'Transfer'),
        ('retrieval', 'Retrieval'),
        ('return', 'Return'),
        ('relocation', 'Relocation'),
        ('destruction', 'To Destruction')
), string="Selection Field")
    responsible_user_id = fields.Many2one('res.users', string='Responsible User', 
                                        default=lambda self: self.env.user, required=True
    notes = fields.Text('Notes')
    reference = fields.Char('Reference Number')
    
    # Tracking fields
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    
    # Phase 3: Advanced Movement Analytics
    
    # Logistics Analytics
    movement_efficiency_score = fields.Float(
        string='Movement Efficiency Score',
        compute='_compute_logistics_analytics',
        store=True,
        help='Efficiency score for this movement (0-100',
    distance_optimization_rating = fields.Float(
        string='Distance Optimization Rating',
        compute='_compute_logistics_analytics',
        store=True,
        help='Rating of route optimization for this movement',
    handling_complexity_score = fields.Float(
        string='Handling Complexity Score',
        compute='_compute_logistics_analytics',
        store=True,
        help='Complexity assessment of the movement operation'
    
    # Pattern Analytics
    movement_pattern_score = fields.Float(
        string='Movement Pattern Score',
        compute='_compute_pattern_analytics',
        store=True,
        help='Score based on movement patterns and predictability',
    seasonal_trend_indicator = fields.Selection([
        ('low_season', 'Low Season',
        ('normal', 'Normal Period'),
        ('peak_season', 'Peak Season'),
        ('irregular', 'Irregular Pattern')
       compute='_compute_pattern_analytics',
       store=True,
       help='Seasonal movement trend indicator'
), string="Selection Field"
    frequency_anomaly_flag = fields.Boolean(
        string='Frequency Anomaly Detected',
        compute='_compute_pattern_analytics',
        store=True,
        help='Indicates unusual movement frequency'
    
    # Cost Analytics
    estimated_movement_cost = fields.Float(
        string='Estimated Movement Cost',
        compute='_compute_cost_analytics',
        store=True,
        help='Estimated cost of this movement operation',
    labor_efficiency_rating = fields.Float(
        string='Labor Efficiency Rating',
        compute='_compute_cost_analytics',
        store=True,
        help='Efficiency rating of labor utilization',
    resource_utilization_score = fields.Float(
        string='Resource Utilization Score',
        compute='_compute_cost_analytics',
        store=True,
        help='Score for resource utilization optimization'

    @api.depends('movement_type', 'from_location_id', 'to_location_id', 'movement_date'
    def _compute_logistics_analytics(self):
        """Compute logistics efficiency analytics"""
        for record in self:
            # Base efficiency assessment
            efficiency_scores = {
                'storage': 85,      # Simple operation
                'transfer': 70,     # Moderate complexity
                'retrieval': 75,    # Standard operation
                'return': 80,       # Return to known location
                'relocation': 65,   # More complex
                'destruction': 90   # Final destination, high efficiency
            }
            
            base_efficiency = efficiency_scores.get(record.movement_type, 70
            
            # Location distance factor (simplified - would integrate with actual distance calculation
            distance_rating = 80  # Default rating
            
            if record.from_location_id and record.to_location_id:
                # Simulate distance calculation based on location hierarchy
                from_path = record.from_location_id.complete_name or ''
                to_path = record.to_location_id.complete_name or ''
                
                # Same building/area = high efficiency
                if from_path.split('/'[0] == to_path.split('/'[0]:
                    distance_rating = 95
                # Different areas = moderate efficiency
                elif len(from_path.split('/' > 1 and len(to_path.split('/')) > 1:
                    distance_rating = 75
                # Complex routing = lower efficiency
                else:
                    distance_rating = 60
            
            record.distance_optimization_rating = distance_rating
            
            # Handling complexity assessment
            complexity_factors = {
                'storage': 30,      # Low complexity
                'transfer': 50,     # Medium complexity
                'retrieval': 40,    # Medium-low complexity
                'return': 35,       # Low-medium complexity
                'relocation': 70,   # High complexity
                'destruction': 60   # Medium-high complexity
            }
            
            complexity_score = complexity_factors.get(record.movement_type, 50
            
            # Time-based complexity (movements outside business hours are more complex
            if record.movement_date:
                hour = record.movement_date.hour
                if hour < 7 or hour > 18:
                    complexity_score += 15
                
                # Weekend movements are more complex
                if record.movement_date.weekday( >= 5:
                    complexity_score += 10
            
            record.handling_complexity_score = min(complexity_score, 100
            
            # Overall efficiency (considering distance and complexity
            adjusted_efficiency = base_efficiency
            adjusted_efficiency += (distance_rating - 80 * 0.3  # Distance factor
            adjusted_efficiency -= (complexity_score - 50 * 0.2  # Complexity penalty
            
            record.movement_efficiency_score = min(max(adjusted_efficiency, 0, 100
    
    @api.depends('box_id', 'movement_date', 'movement_type')
    def _compute_pattern_analytics(self):
        """Compute movement pattern analytics"""
        for record in self:
            if not record.box_id:
                record.movement_pattern_score = 0
                record.seasonal_trend_indicator = 'irregular'
                record.frequency_anomaly_flag = False
                continue
            
            # Analyze movement patterns for this box
            box_movements = self.search\([
                ('box_id', '=', record.box_id.id,
                ('movement_date', '<=', record.movement_date])
            ], order='movement_date asc'
            
            pattern_score = 50  # Base score
            
            if len(box_movements >= 3:
                # Calculate movement intervals
                intervals = []
                for i in range(1, len(box_movements:
                    interval_days = (box_movements[i].movement_date - box_movements[i-1].movement_date).days
                    intervals.append(interval_days)
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
                    
                    # Regular patterns get higher scores
                    if variance < avg_interval * 0.2:  # Very regular
                        pattern_score += 30
                    elif variance < avg_interval * 0.5:  # Somewhat regular
                        pattern_score += 15
                    
                    # Seasonal trend analysis
                    if record.movement_date:
                        month = record.movement_date.month
                        
                        # Peak seasons (end of quarters, year-end
                        if month in [3, 6, 9, 12]:
                            record.seasonal_trend_indicator = 'peak_season'
                            pattern_score += 10
                        # Low season (typically summer months
                        elif month in [7, 8]:
                            record.seasonal_trend_indicator = 'low_season'
                        else:
                            record.seasonal_trend_indicator = 'normal'
                    else:
                        record.seasonal_trend_indicator = 'irregular'
                    
                    # Frequency anomaly detection
                    recent_movements = len([m for m in box_movements 
                                          if (record.movement_date - m.movement_date.days <= 7]
                    
                    if recent_movements > 3:  # More than 3 movements in a week
                        record.frequency_anomaly_flag = True
                        pattern_score -= 20
                    else:
                        record.frequency_anomaly_flag = False
            else:
                record.seasonal_trend_indicator = 'irregular'
                record.frequency_anomaly_flag = False
            
            record.movement_pattern_score = min(max(pattern_score, 0, 100
    
    @api.depends('movement_type', 'responsible_user_id', 'movement_date')
    def _compute_cost_analytics(self):
        """Compute cost and resource analytics"""
        for record in self:
            # Base cost estimation (in currency units
            base_costs = {
                'storage': 15,      # Low cost
                'transfer': 35,     # Medium cost
                'retrieval': 25,    # Medium-low cost
                'return': 20,       # Low-medium cost
                'relocation': 45,   # High cost
                'destruction': 30   # Medium cost
            }
            
            base_cost = base_costs.get(record.movement_type, 30
            
            # Time-based cost adjustments
            if record.movement_date:
                hour = record.movement_date.hour
                
                # Overtime costs
                if hour < 7 or hour > 18:
                    base_cost *= 1.5
                
                # Weekend premium
                if record.movement_date.weekday( >= 5:
                    base_cost *= 1.3
            
            record.estimated_movement_cost = base_cost
            
            # Labor efficiency assessment
            labor_efficiency = 75  # Base efficiency
            
            if record.responsible_user_id:
                # Analyze user's movement history
                user_movements = self.search\([
                    ('responsible_user_id', '=', record.responsible_user_id.id,
                    ('movement_date', '>=', fields.Datetime.now( - timedelta(days=30))])
                ]
                
                # Experience factor
                if len(user_movements > 20:  # Experienced user
                    labor_efficiency += 15
                elif len(user_movements > 10:  # Moderate experience
                    labor_efficiency += 8
                elif len(user_movements < 3:  # New user
                    labor_efficiency -= 10
                
                # Consistency factor (same user handling similar movements
                similar_movements = user_movements.filtered(
                    lambda m: m.movement_type == record.movement_type
                if len(similar_movements >= 5:
                    labor_efficiency += 10
            
            record.labor_efficiency_rating = min(max(labor_efficiency, 0), 100)
            
            # Resource utilization score
            resource_score = 60  # Base score
            
            # Movement type efficiency
            efficient_types = ['storage', 'return', 'destruction']
            if record.movement_type in efficient_types:
                resource_score += 20
            
            # Time optimization
            if record.movement_date:
                hour = record.movement_date.hour
                # Optimal working hours
                if 8 <= hour <= 16:
                    resource_score += 15
            
            # Pattern efficiency (regular movements are more resource-efficient
            if record.movement_pattern_score > 70:
                resource_score += 10
            
            record.resource_utilization_score = min(max(resource_score, 0, 100)

class RecordsServiceRequest(models.Model):
    _name = 'records.service.request'
    _description = 'Records Service Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'requested_date desc'

    name = fields.Char('Request Reference', required=True, default='New')
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                domain="[('is_company', '=', True]", required=True)
    
    service_type = fields.Selection([
        ('retrieval', 'Document Retrieval'),
        ('delivery', 'Document Delivery'),
        ('scanning', 'Document Scanning'),
        ('destruction', 'Document Destruction'),
        ('relocation', 'Box Relocation'),
        ('inventory', 'Inventory Check'),
        ('other', 'Other Service')
), string="Selection Field")
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
), string="Selection Field")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
), string="Selection Field")
    required_date = fields.Date('Required Date')
    completed_date = fields.Datetime('Completed Date')
    
    description = fields.Text('Description')
    
    # Assignment
    assigned_to = fields.Many2one('res.users', string='Assigned To')
    
    # Tracking
    requestor_id = fields.Many2one('res.users', string='Requestor', 
                                 default=lambda self: self.env.user, required=True
    
    # Phase 3: Advanced Service Request Analytics
    
    # Performance Analytics
    service_efficiency_score = fields.Float(
        string='Service Efficiency Score',
        compute='_compute_performance_analytics',
        store=True,
        help='Overall efficiency score for this service request',
    response_time_score = fields.Float(
        string='Response Time Score',
        compute='_compute_performance_analytics',
        store=True,
        help='Score based on response time to customer request',
    completion_quality_rating = fields.Float(
        string='Completion Quality Rating',
        compute='_compute_performance_analytics',
        store=True,
        help='Quality assessment of service completion'
    
    # Customer Analytics
    customer_satisfaction_prediction = fields.Float(
        string='Customer Satisfaction Prediction',
        compute='_compute_customer_analytics',
        store=True,
        help='Predicted customer satisfaction score',
    repeat_service_likelihood = fields.Float(
        string='Repeat Service Likelihood %',
        compute='_compute_customer_analytics',
        store=True,
        help='Likelihood of repeat service requests',
    service_complexity_assessment = fields.Selection([
        ('simple', 'Simple',
        ('moderate', 'Moderate'),
        ('complex', 'Complex'),
        ('very_complex', 'Very Complex')
       compute='_compute_customer_analytics',
       store=True,
       help='Complexity assessment of the service'
    
    # Resource Analytics), string="Selection Field"
    resource_allocation_score = fields.Float(
        string='Resource Allocation Score',
        compute='_compute_resource_analytics',
        store=True,
        help='Efficiency of resource allocation for this request',
    workload_balance_indicator = fields.Selection([
        ('underutilized', 'Underutilized',
        ('optimal', 'Optimal'),
        ('overloaded', 'Overloaded'),
        ('critical', 'Critical')
       compute='_compute_resource_analytics',
       store=True,
       help='Workload balance indicator'
), string="Selection Field"
    cost_efficiency_rating = fields.Float(
        string='Cost Efficiency Rating',
        compute='_compute_resource_analytics',
        store=True,
        help='Cost efficiency assessment'

    @api.depends('state', 'requested_date', 'completed_date', 'required_date', 'priority')
    def _compute_performance_analytics(self):
        """Compute service performance analytics"""
        for record in self:
            # Service efficiency based on completion status and timing
            base_efficiency = 50
            
            if record.state == 'completed':
                base_efficiency += 30
                
                # Timing efficiency
                if record.completed_date and record.requested_date:
                    completion_hours = (record.completed_date - record.requested_date.total_seconds( / 3600
                    
                    # Expected completion times by service type
                    expected_hours = {
                        'retrieval': 4,
                        'delivery': 8,
                        'scanning': 24,
                        'destruction': 48,
                        'relocation': 12,
                        'inventory': 6,
                        'other': 12
                    }
                    
                    expected = expected_hours.get(record.service_type, 12
                    
                    if completion_hours <= expected:
                        base_efficiency += 20
                    elif completion_hours <= expected * 1.5:
                        base_efficiency += 10
                    elif completion_hours > expected * 2:
                        base_efficiency -= 15
            elif record.state == 'cancelled':
                base_efficiency -= 30
            elif record.state in ['in_progress', 'confirmed']:
                base_efficiency += 10
            
            # Priority handling efficiency
            priority_bonuses = {
                'urgent': 15,
                'high': 10,
                'normal': 5,
                'low': 0
            }
            base_efficiency += priority_bonuses.get(record.priority, 0
            
            record.service_efficiency_score = min(max(base_efficiency, 0, 100)
            
            # Response time score
            response_score = 80  # Base score
            
            if record.state not in ['draft'] and record.requested_date:
                # Time from request to first action (submitted/confirmed
                if record.state in ['submitted', 'confirmed', 'in_progress', 'completed']:
                    # Simulate response time (would track actual state change timestamps
                    current_time = fields.Datetime.now(
                    if record.completed_date and record.state == 'completed':
                        current_time = record.completed_date
                    
                    response_hours = (current_time - record.requested_date).total_seconds() / 3600
                    
                    # Priority-based expected response times
                    expected_response = {
                        'urgent': 1,    # 1 hour
                        'high': 4,      # 4 hours
                        'normal': 24,   # 1 day
                        'low': 48       # 2 days
                    }
                    
                    expected = expected_response.get(record.priority, 24
                    
                    if response_hours <= expected * 0.5:
                        response_score = 100
                    elif response_hours <= expected:
                        response_score = 90
                    elif response_hours <= expected * 2:
                        response_score = 70
                    else:
                        response_score = max(50 - (response_hours - expected * 2 * 2, 0)
            
            record.response_time_score = response_score
            
            # Completion quality rating
            quality_rating = 70  # Base quality
            
            if record.state == 'completed':
                quality_rating += 20
                
                # On-time completion bonus
                if record.required_date and record.completed_date:
                    if record.completed_date.date( <= record.required_date:
                        quality_rating += 10
                    elif (record.completed_date.date( - record.required_date).days <= 1:
                        quality_rating += 5
                
                # Notes quality (indicates thoroughness
                if record.notes and len(record.notes.strip() > 50:
                    quality_rating += 5
            
            record.completion_quality_rating = min(max(quality_rating, 0), 100)
    
    @api.depends('customer_id', 'service_type', 'priority', 'state')
    def _compute_customer_analytics(self):
        """Compute customer-related analytics"""
        for record in self:
            # Customer satisfaction prediction
            satisfaction_score = 75  # Base satisfaction
            
            # Service type satisfaction factors
            satisfaction_factors = {
                'retrieval': 80,    # Generally high satisfaction
                'delivery': 85,     # High satisfaction
                'scanning': 75,     # Moderate satisfaction
                'destruction': 70,  # Lower satisfaction (necessary but not preferred
                'relocation': 65,   # Moderate satisfaction
                'inventory': 90,    # High satisfaction (proactive
                'other': 70         # Variable satisfaction
            }
            
            base_satisfaction = satisfaction_factors.get(record.service_type, 75
            
            # Priority handling affects satisfaction
            if record.priority == 'urgent' and record.state in ['confirmed', 'in_progress', 'completed']:
                base_satisfaction += 10
            elif record.priority == 'urgent' and record.state in ['draft', 'submitted']:
                base_satisfaction -= 20
            
            # State-based satisfaction
            if record.state == 'completed':
                base_satisfaction += 15
            elif record.state == 'cancelled':
                base_satisfaction -= 30
            elif record.state == 'in_progress':
                base_satisfaction += 5
            
            record.customer_satisfaction_prediction = min(max(base_satisfaction, 0, 100
            
            # Repeat service likelihood
            repeat_likelihood = 60  # Base likelihood
            
            if record.customer_id:
                # Customer history analysis
                customer_requests = self.search_count([
                    ('customer_id', '=', record.customer_id.id
                ]
                
                if customer_requests > 5:  # Frequent customer
                    repeat_likelihood += 20
                elif customer_requests > 2:  # Regular customer
                    repeat_likelihood += 10
                
                # Recent request frequency
                recent_requests = self.search_count([
                    ('customer_id', '=', record.customer_id.id,
                    ('requested_date', '>=', fields.Datetime.now( - timedelta(days=90))
                ]
                
                if recent_requests > 3:
                    repeat_likelihood += 15
            
            # Service type repeat factors
            repeat_factors = {
                'inventory': 30,    # Regular service
                'retrieval': 25,    # Frequent need
                'delivery': 20,     # Regular need
                'scanning': 15,     # Occasional need
                'relocation': 10,   # Infrequent need
                'destruction': 5,   # Rare repeat
                'other': 15         # Variable
            }
            
            repeat_likelihood += repeat_factors.get(record.service_type, 15
            
            record.repeat_service_likelihood = min(max(repeat_likelihood, 0, 100)
            
            # Service complexity assessment
            complexity_scores = {
                'inventory': 20,
                'retrieval': 30,
                'delivery': 35,
                'scanning': 50,
                'relocation': 60,
                'destruction': 70,
                'other': 40
            }
            
            complexity = complexity_scores.get(record.service_type, 40
            
            # Priority adds complexity
            priority_complexity = {
                'urgent': 20,
                'high': 10,
                'normal': 0,
                'low': -5
            }
            
            complexity += priority_complexity.get(record.priority, 0
            
            if complexity <= 30:
                record.service_complexity_assessment = 'simple'
            elif complexity <= 50:
                record.service_complexity_assessment = 'moderate'
            elif complexity <= 70:
                record.service_complexity_assessment = 'complex'
            else:
                record.service_complexity_assessment = 'very_complex'
    
    @api.depends('assigned_to', 'service_type', 'priority', 'state'
    def _compute_resource_analytics(self):
        """Compute resource allocation analytics"""
        for record in self:
            # Resource allocation efficiency
            allocation_score = 70  # Base score
            
            if record.assigned_to:
                allocation_score += 15  # Assigned requests are better managed
                
                # Assignee workload analysis
                assignee_requests = self.search_count([
                    ('assigned_to', '=', record.assigned_to.id,
                    ('state', 'in', ['confirmed', 'in_progress'],
                    ('requested_date', '>=', fields.Datetime.now() - timedelta(days=7))
                ]
                
                # Workload balance assessment
                if assignee_requests <= 3:
                    record.workload_balance_indicator = 'underutilized'
                    allocation_score += 10
                elif assignee_requests <= 8:
                    record.workload_balance_indicator = 'optimal'
                    allocation_score += 15
                elif assignee_requests <= 15:
                    record.workload_balance_indicator = 'overloaded'
                    allocation_score -= 10
                else:
                    record.workload_balance_indicator = 'critical'
                    allocation_score -= 25
            else:
                record.workload_balance_indicator = 'underutilized'
                allocation_score -= 20  # Unassigned requests are inefficient
            
            # Service type resource requirements
            resource_requirements = {
                'retrieval': 60,    # Moderate resources
                'delivery': 70,     # Higher resources
                'scanning': 80,     # High resources
                'destruction': 50,  # Lower resources
                'relocation': 75,   # High resources
                'inventory': 40,    # Low resources
                'other': 60         # Moderate resources
            }
            
            requirement = resource_requirements.get(record.service_type, 60
            
            # Adjust score based on resource intensity
            if requirement <= 50:
                allocation_score += 10  # Low resource needs are easier to allocate
            elif requirement >= 80:
                allocation_score -= 5   # High resource needs are harder to allocate
            
            record.resource_allocation_score = min(max(allocation_score, 0, 100
            
            # Cost efficiency rating
            cost_efficiency = 65  # Base efficiency
            
            # Service type cost factors
            cost_factors = {
                'inventory': 85,    # High efficiency
                'retrieval': 75,    # Good efficiency
                'delivery': 70,     # Moderate efficiency
                'scanning': 60,     # Lower efficiency (equipment intensive
                'relocation': 55,   # Lower efficiency (labor intensive
                'destruction': 80,  # Good efficiency (specialized but efficient
                'other': 65         # Average efficiency
            }
            
            cost_efficiency = cost_factors.get(record.service_type, 65
            
            # Priority impact on cost efficiency
            if record.priority == 'urgent':
                cost_efficiency -= 15  # Rush jobs are less cost efficient
            elif record.priority == 'low':
                cost_efficiency += 10  # Low priority allows for optimization
            
            # State impact
            if record.state == 'completed':
                cost_efficiency += 10
            elif record.state == 'cancelled':
                cost_efficiency -= 20
            
            record.cost_efficiency_rating = min(max(cost_efficiency, 0, 100
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('records.service.request') or 'New'
        return super().create(vals_list)
    
    def action_submit(self):
        self.state = 'submitted'
    
    def action_confirm(self):
        self.state = 'confirmed'
    
    def action_start(self):
        self.state = 'in_progress'
    
    def action_complete(self):
        self.state = 'completed'
    
    def action_cancel(self):
        self.state = 'cancelled'
