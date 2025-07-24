from odoo import models, fields, api
from datetime import datetime, timedelta

class RecordsChainOfCustody(models.Model):
    _name = 'records.chain.of.custody'
    _description = 'Document Chain of Custody'
    _order = 'event_date desc'

    document_id = fields.Many2one('records.document', string='Document', required=True, ondelete='cascade')
    service_id = fields.Many2one('shredding.service', string='Shredding Service', ondelete='cascade')
    event_date = fields.Datetime('Event Date', required=True, default=fields.Datetime.now)
    event_type = fields.Selection([
        ('creation', 'Document Creation'),
        ('receipt', 'Receipt'),
        ('storage', 'Storage'),
        ('access', 'Access/Retrieval'),
        ('transfer', 'Transfer'),
        ('scan', 'Scanning/Digitization'),
        ('destruction', 'Destruction')
    ], string='Event Type', required=True)
    
    responsible_person = fields.Char('Responsible Person', required=True)
    location = fields.Char('Location', required=True)
    signature_verified = fields.Boolean('Signature Verified', default=False)
    notes = fields.Text('Notes')
    
    # Audit fields
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    created_on = fields.Datetime('Created On', default=fields.Datetime.now, readonly=True)
    
    # Phase 3: Advanced Analytics & Computed Fields
    
    # Custody Analytics
    custody_duration = fields.Float(
        string='Custody Duration (hours)',
        compute='_compute_custody_analytics',
        store=True,
        help='Duration this custody event lasted'
    )
    
    custody_efficiency_score = fields.Float(
        string='Custody Efficiency Score',
        compute='_compute_custody_analytics',
        store=True,
        help='Efficiency score based on processing time and compliance'
    )
    
    event_criticality_level = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    ], string='Event Criticality',
       compute='_compute_custody_analytics',
       store=True,
       help='Risk level assessment for this custody event')
    
    # Compliance Analytics
    compliance_score = fields.Float(
        string='Compliance Score',
        compute='_compute_compliance_analytics',
        store=True,
        help='Automated compliance assessment score (0-100)'
    )
    
    regulatory_flags = fields.Integer(
        string='Regulatory Flags',
        compute='_compute_compliance_analytics',
        store=True,
        help='Number of potential regulatory compliance issues'
    )
    
    audit_readiness_score = fields.Float(
        string='Audit Readiness Score',
        compute='_compute_compliance_analytics',
        store=True,
        help='Assessment of audit trail completeness'
    )
    
    # Process Analytics
    event_sequence_accuracy = fields.Float(
        string='Sequence Accuracy %',
        compute='_compute_process_analytics',
        store=True,
        help='Accuracy of event sequencing in custody chain'
    )
    
    process_automation_potential = fields.Float(
        string='Automation Potential %',
        compute='_compute_process_analytics',
        store=True,
        help='Potential for process automation based on patterns'
    )
    
    chain_completeness_score = fields.Float(
        string='Chain Completeness Score',
        compute='_compute_process_analytics',
        store=True,
        help='Completeness of custody chain documentation'
    )
    
    @api.depends('event_date', 'event_type', 'signature_verified', 'document_id')
    def _compute_custody_analytics(self):
        """Compute custody-related analytics"""
        for record in self:
            # Calculate custody duration
            if record.document_id:
                next_event = self.search([
                    ('document_id', '=', record.document_id.id),
                    ('event_date', '>', record.event_date)
                ], limit=1, order='event_date asc')
                
                if next_event:
                    duration = (next_event.event_date - record.event_date).total_seconds() / 3600
                    record.custody_duration = round(duration, 2)
                else:
                    # If no next event, calculate from current time
                    current_time = fields.Datetime.now()
                    duration = (current_time - record.event_date).total_seconds() / 3600
                    record.custody_duration = round(min(duration, 8760), 2)  # Cap at 1 year
            else:
                record.custody_duration = 0
            
            # Calculate efficiency score
            base_score = 70
            
            # Signature verification bonus
            if record.signature_verified:
                base_score += 15
            
            # Event type risk factor
            risk_factors = {
                'creation': 0,
                'receipt': 5,
                'storage': 0,
                'access': 10,
                'transfer': 15,
                'scan': 5,
                'destruction': 20
            }
            base_score += risk_factors.get(record.event_type, 0)
            
            # Duration factor (shorter custody periods often indicate efficiency)
            if record.custody_duration > 0:
                if record.custody_duration < 24:  # Less than 1 day
                    base_score += 10
                elif record.custody_duration > 168:  # More than 1 week
                    base_score -= 10
            
            record.custody_efficiency_score = min(max(base_score, 0), 100)
            
            # Determine criticality level
            if record.event_type in ['destruction', 'transfer'] or not record.signature_verified:
                if record.custody_efficiency_score < 60:
                    record.event_criticality_level = 'critical'
                elif record.custody_efficiency_score < 75:
                    record.event_criticality_level = 'high'
                else:
                    record.event_criticality_level = 'medium'
            else:
                record.event_criticality_level = 'low' if record.custody_efficiency_score > 80 else 'medium'
    
    @api.depends('signature_verified', 'notes', 'responsible_person', 'document_id')
    def _compute_compliance_analytics(self):
        """Compute compliance-related analytics"""
        for record in self:
            base_score = 50
            flags = 0
            
            # Signature verification
            if record.signature_verified:
                base_score += 25
            else:
                flags += 1
            
            # Required information completeness
            if record.responsible_person and len(record.responsible_person.strip()) > 0:
                base_score += 10
            else:
                flags += 1
            
            if record.location and len(record.location.strip()) > 0:
                base_score += 10
            else:
                flags += 1
            
            if record.notes and len(record.notes.strip()) > 10:
                base_score += 5
            
            record.compliance_score = min(base_score, 100)
            record.regulatory_flags = flags
            
            # Audit readiness based on documentation quality
            audit_score = record.compliance_score
            if record.document_id:
                # Check if part of complete chain
                chain_count = self.search_count([('document_id', '=', record.document_id.id)])
                if chain_count >= 3:  # Minimum viable audit trail
                    audit_score += 10
                
                # Recent activity bonus
                recent_events = self.search_count([
                    ('document_id', '=', record.document_id.id),
                    ('event_date', '>=', fields.Datetime.now() - timedelta(days=30))
                ])
                if recent_events > 0:
                    audit_score += 5
            
            record.audit_readiness_score = min(audit_score, 100)
    
    @api.depends('event_date', 'event_type', 'document_id')
    def _compute_process_analytics(self):
        """Compute process optimization analytics"""
        for record in self:
            if not record.document_id:
                record.event_sequence_accuracy = 0
                record.process_automation_potential = 0
                record.chain_completeness_score = 0
                continue
            
            # Get all events for this document
            all_events = self.search([
                ('document_id', '=', record.document_id.id)
            ], order='event_date asc')
            
            # Calculate sequence accuracy
            expected_sequence = ['creation', 'receipt', 'storage', 'access', 'scan', 'destruction']
            actual_sequence = [event.event_type for event in all_events]
            
            if len(actual_sequence) > 1:
                sequence_matches = sum(1 for i, event_type in enumerate(actual_sequence) 
                                     if i < len(expected_sequence) and event_type == expected_sequence[i])
                record.event_sequence_accuracy = (sequence_matches / len(actual_sequence)) * 100
            else:
                record.event_sequence_accuracy = 100 if actual_sequence and actual_sequence[0] == 'creation' else 50
            
            # Automation potential based on pattern regularity
            automation_score = 30  # Base automation potential
            
            # Regular intervals suggest automation potential
            if len(all_events) >= 3:
                intervals = []
                for i in range(1, len(all_events)):
                    interval = (all_events[i].event_date - all_events[i-1].event_date).total_seconds() / 3600
                    intervals.append(interval)
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
                    
                    # Low variance suggests regular patterns (higher automation potential)
                    if variance < avg_interval * 0.1:  # Very regular
                        automation_score += 40
                    elif variance < avg_interval * 0.3:  # Somewhat regular
                        automation_score += 20
            
            # Standard event types suggest automation potential
            standard_events = ['creation', 'receipt', 'storage', 'scan']
            if all(event.event_type in standard_events for event in all_events):
                automation_score += 15
            
            record.process_automation_potential = min(automation_score, 100)
            
            # Chain completeness
            essential_events = ['creation', 'storage']
            has_essential = all(event_type in actual_sequence for event_type in essential_events)
            
            completeness_score = 40 if has_essential else 20
            completeness_score += min(len(actual_sequence) * 10, 50)  # More events = more complete
            
            # Verification completeness
            verified_events = sum(1 for event in all_events if event.signature_verified)
            if len(all_events) > 0:
                verification_rate = verified_events / len(all_events)
                completeness_score += verification_rate * 10
            
            record.chain_completeness_score = min(completeness_score, 100)

class RecordsAuditTrail(models.Model):
    _name = 'records.audit.trail'
    _description = 'Document Audit Trail'
    _order = 'timestamp desc'

    document_id = fields.Many2one('records.document', string='Document', required=True, ondelete='cascade')
    timestamp = fields.Datetime('Timestamp', required=True, default=fields.Datetime.now)
    action_type = fields.Selection([
        ('create', 'Created'),
        ('read', 'Accessed'),
        ('update', 'Modified'),
        ('delete', 'Deleted'),
        ('move', 'Moved'),
        ('scan', 'Scanned'),
        ('export', 'Exported'),
        ('print', 'Printed'),
        ('email', 'Emailed'),
        ('archive', 'Archived'),
        ('destroy', 'Destroyed')
    ], string='Action Type', required=True)
    
    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user)
    description = fields.Text('Description', required=True)
    compliance_verified = fields.Boolean('Compliance Verified', default=False)
    
    # Additional audit fields
    ip_address = fields.Char('IP Address')
    browser_info = fields.Char('Browser Info')
    
    # Phase 3: Advanced Audit Analytics
    
    # Security Analytics
    security_risk_level = fields.Selection([
        ('minimal', 'Minimal Risk'),
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    ], string='Security Risk Level',
       compute='_compute_security_analytics',
       store=True,
       help='Automated security risk assessment')
    
    access_pattern_score = fields.Float(
        string='Access Pattern Score',
        compute='_compute_security_analytics',
        store=True,
        help='Score based on access patterns and anomalies'
    )
    
    behavioral_anomaly_flag = fields.Boolean(
        string='Behavioral Anomaly Detected',
        compute='_compute_security_analytics',
        store=True,
        help='Indicates unusual access patterns'
    )
    
    # Compliance Analytics
    regulatory_compliance_score = fields.Float(
        string='Regulatory Compliance Score',
        compute='_compute_compliance_analytics',
        store=True,
        help='Compliance assessment score (0-100)'
    )
    
    audit_trail_completeness = fields.Float(
        string='Trail Completeness %',
        compute='_compute_compliance_analytics',
        store=True,
        help='Completeness of audit trail documentation'
    )
    
    retention_compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('warning', 'Warning'),
        ('violation', 'Violation')
    ], string='Retention Compliance',
       compute='_compute_compliance_analytics',
       store=True)
    
    # Performance Analytics
    action_frequency_score = fields.Float(
        string='Action Frequency Score',
        compute='_compute_performance_analytics',
        store=True,
        help='Score based on action frequency patterns'
    )
    
    user_efficiency_rating = fields.Float(
        string='User Efficiency Rating',
        compute='_compute_performance_analytics',
        store=True,
        help='Efficiency rating for the user performing this action'
    )
    
    system_performance_impact = fields.Float(
        string='System Performance Impact',
        compute='_compute_performance_analytics',
        store=True,
        help='Estimated impact on system performance (0-100)'
    )
    
    @api.depends('action_type', 'user_id', 'timestamp', 'ip_address')
    def _compute_security_analytics(self):
        """Compute security-related analytics"""
        for record in self:
            # Base security assessment
            risk_scores = {
                'create': 20,
                'read': 10,
                'update': 40,
                'delete': 80,
                'move': 50,
                'scan': 15,
                'export': 60,
                'print': 30,
                'email': 70,
                'archive': 25,
                'destroy': 90
            }
            
            base_risk = risk_scores.get(record.action_type, 30)
            
            # Time-based risk factors
            if record.timestamp:
                hour = record.timestamp.hour
                # Higher risk for actions outside business hours
                if hour < 7 or hour > 18:
                    base_risk += 15
                
                # Weekend actions are higher risk
                weekday = record.timestamp.weekday()
                if weekday >= 5:  # Saturday or Sunday
                    base_risk += 10
            
            # IP address consistency check
            if record.user_id and record.ip_address:
                user_recent_ips = self.search([
                    ('user_id', '=', record.user_id.id),
                    ('timestamp', '>=', fields.Datetime.now() - timedelta(days=7)),
                    ('ip_address', '!=', False)
                ]).mapped('ip_address')
                
                if len(set(user_recent_ips)) > 3:  # Multiple IPs suggest higher risk
                    base_risk += 20
            
            # Access pattern analysis
            if record.user_id and record.document_id:
                recent_actions = self.search_count([
                    ('user_id', '=', record.user_id.id),
                    ('document_id', '=', record.document_id.id),
                    ('timestamp', '>=', fields.Datetime.now() - timedelta(hours=1))
                ])
                
                if recent_actions > 5:  # Unusual frequency
                    base_risk += 25
                    record.behavioral_anomaly_flag = True
                else:
                    record.behavioral_anomaly_flag = False
            else:
                record.behavioral_anomaly_flag = False
            
            # Set risk level
            if base_risk >= 80:
                record.security_risk_level = 'critical'
            elif base_risk >= 60:
                record.security_risk_level = 'high'
            elif base_risk >= 40:
                record.security_risk_level = 'medium'
            elif base_risk >= 20:
                record.security_risk_level = 'low'
            else:
                record.security_risk_level = 'minimal'
            
            record.access_pattern_score = min(100 - base_risk, 100)
    
    @api.depends('compliance_verified', 'description', 'document_id', 'timestamp')
    def _compute_compliance_analytics(self):
        """Compute compliance-related analytics"""
        for record in self:
            base_score = 60
            
            # Compliance verification
            if record.compliance_verified:
                base_score += 20
            
            # Description quality
            if record.description and len(record.description.strip()) > 20:
                base_score += 10
            elif record.description and len(record.description.strip()) > 5:
                base_score += 5
            
            # Trail completeness assessment
            if record.document_id:
                total_actions = self.search_count([('document_id', '=', record.document_id.id)])
                verified_actions = self.search_count([
                    ('document_id', '=', record.document_id.id),
                    ('compliance_verified', '=', True)
                ])
                
                if total_actions > 0:
                    verification_rate = (verified_actions / total_actions) * 100
                    record.audit_trail_completeness = verification_rate
                    
                    if verification_rate >= 90:
                        base_score += 10
                    elif verification_rate >= 70:
                        base_score += 5
                else:
                    record.audit_trail_completeness = 0
            else:
                record.audit_trail_completeness = 0
            
            record.regulatory_compliance_score = min(base_score, 100)
            
            # Retention compliance
            if record.document_id and hasattr(record.document_id, 'retention_policy_id'):
                if record.regulatory_compliance_score >= 80:
                    record.retention_compliance_status = 'compliant'
                elif record.regulatory_compliance_score >= 60:
                    record.retention_compliance_status = 'warning'
                else:
                    record.retention_compliance_status = 'violation'
            else:
                record.retention_compliance_status = 'warning'
    
    @api.depends('action_type', 'user_id', 'timestamp')
    def _compute_performance_analytics(self):
        """Compute performance-related analytics"""
        for record in self:
            # Action frequency analysis
            if record.user_id:
                # Count user actions in last hour
                recent_actions = self.search_count([
                    ('user_id', '=', record.user_id.id),
                    ('timestamp', '>=', fields.Datetime.now() - timedelta(hours=1))
                ])
                
                # Score based on frequency (optimal range is 5-15 actions per hour)
                if 5 <= recent_actions <= 15:
                    frequency_score = 100
                elif recent_actions < 5:
                    frequency_score = recent_actions * 20  # Scale up low activity
                else:
                    frequency_score = max(100 - (recent_actions - 15) * 5, 0)  # Penalize excessive activity
                
                record.action_frequency_score = frequency_score
                
                # User efficiency rating
                user_actions_today = self.search_count([
                    ('user_id', '=', record.user_id.id),
                    ('timestamp', '>=', fields.Date.today())
                ])
                
                user_errors_today = self.search_count([
                    ('user_id', '=', record.user_id.id),
                    ('timestamp', '>=', fields.Date.today()),
                    ('action_type', 'in', ['delete', 'update']),  # Potential error indicators
                    ('compliance_verified', '=', False)
                ])
                
                if user_actions_today > 0:
                    error_rate = user_errors_today / user_actions_today
                    efficiency_rating = max(100 - (error_rate * 100), 0)
                else:
                    efficiency_rating = 80  # Neutral rating for new users
                
                record.user_efficiency_rating = efficiency_rating
            else:
                record.action_frequency_score = 0
                record.user_efficiency_rating = 0
            
            # System performance impact estimation
            impact_weights = {
                'create': 30,
                'read': 5,
                'update': 25,
                'delete': 35,
                'move': 40,
                'scan': 50,
                'export': 45,
                'print': 20,
                'email': 30,
                'archive': 35,
                'destroy': 20
            }
            
            base_impact = impact_weights.get(record.action_type, 25)
            
            # Time-based impact (higher impact during business hours)
            if record.timestamp:
                hour = record.timestamp.hour
                if 9 <= hour <= 17:
                    base_impact += 10
            
            record.system_performance_impact = min(base_impact, 100)

class RecordsDigitalCopy(models.Model):
    _name = 'records.digital.copy'
    _description = 'Document Digital Copy'
    _order = 'scan_date desc'

    document_id = fields.Many2one('records.document', string='Document', required=True, ondelete='cascade')
    scan_date = fields.Datetime('Scan Date', required=True, default=fields.Datetime.now)
    file_format = fields.Selection([
        ('pdf', 'PDF'),
        ('tiff', 'TIFF'),
        ('jpeg', 'JPEG'),
        ('png', 'PNG'),
        ('docx', 'DOCX'),
        ('txt', 'TXT')
    ], string='File Format', required=True)
    
    resolution = fields.Char('Resolution (DPI)')
    file_size = fields.Float('File Size (MB)')
    storage_location = fields.Char('Storage Location', required=True)
    checksum = fields.Char('File Checksum')
    
    # Scan metadata
    scanned_by = fields.Many2one('res.users', string='Scanned By', default=lambda self: self.env.user)
    scanner_device = fields.Char('Scanner Device')
    scan_quality = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('archive', 'Archive Quality')
    ], string='Scan Quality', default='medium')
    
    # File access
    file_attachment_id = fields.Many2one('ir.attachment', string='File Attachment')
    
    # Phase 3: Digital Transformation Analytics
    
    # Digitization Analytics
    digitization_quality_score = fields.Float(
        string='Digitization Quality Score',
        compute='_compute_digitization_analytics',
        store=True,
        help='Overall quality assessment of digital copy'
    )
    
    compression_efficiency = fields.Float(
        string='Compression Efficiency %',
        compute='_compute_digitization_analytics',
        store=True,
        help='File size optimization efficiency'
    )
    
    format_optimization_score = fields.Float(
        string='Format Optimization Score',
        compute='_compute_digitization_analytics',
        store=True,
        help='Score for format choice optimization'
    )
    
    # Storage Analytics
    storage_cost_estimate = fields.Float(
        string='Storage Cost Estimate',
        compute='_compute_storage_analytics',
        store=True,
        help='Estimated annual storage cost'
    )
    
    access_frequency_prediction = fields.Float(
        string='Access Frequency Prediction',
        compute='_compute_storage_analytics',
        store=True,
        help='Predicted access frequency per month'
    )
    
    migration_priority_score = fields.Float(
        string='Migration Priority Score',
        compute='_compute_storage_analytics',
        store=True,
        help='Priority score for format migration'
    )
    
    # Process Analytics
    scanning_efficiency_score = fields.Float(
        string='Scanning Efficiency Score',
        compute='_compute_process_analytics',
        store=True,
        help='Efficiency of the scanning process'
    )
    
    automation_readiness = fields.Float(
        string='Automation Readiness %',
        compute='_compute_process_analytics',
        store=True,
        help='Readiness for automated digitization'
    )
    
    workflow_optimization_potential = fields.Float(
        string='Workflow Optimization Potential',
        compute='_compute_process_analytics',
        store=True,
        help='Potential for workflow improvements'
    )
    
    @api.depends('file_format', 'scan_quality', 'resolution', 'file_size')
    def _compute_digitization_analytics(self):
        """Compute digitization quality analytics"""
        for record in self:
            base_score = 50
            
            # Quality assessment based on scan quality
            quality_scores = {
                'archive': 95,
                'high': 85,
                'medium': 70,
                'low': 40
            }
            base_score += quality_scores.get(record.scan_quality, 50) - 50
            
            # Resolution factor
            if record.resolution:
                try:
                    dpi = int(record.resolution.replace('DPI', '').replace('dpi', '').strip())
                    if dpi >= 600:
                        base_score += 20
                    elif dpi >= 300:
                        base_score += 10
                    elif dpi >= 150:
                        base_score += 5
                except (ValueError, AttributeError):
                    pass
            
            # Format appropriateness
            format_scores = {
                'pdf': 85,    # Excellent for documents
                'tiff': 90,   # Excellent for archival
                'png': 75,    # Good for images
                'jpeg': 60,   # Acceptable for photos
                'docx': 70,   # Good for editable docs
                'txt': 50     # Basic for text-only
            }
            format_score = format_scores.get(record.file_format, 50)
            
            record.digitization_quality_score = min((base_score + format_score) / 2, 100)
            record.format_optimization_score = format_score
            
            # Compression efficiency
            if record.file_size and record.file_size > 0:
                # Estimate based on typical file sizes for quality levels
                expected_sizes = {
                    'archive': 5.0,   # MB
                    'high': 2.0,
                    'medium': 1.0,
                    'low': 0.5
                }
                expected_size = expected_sizes.get(record.scan_quality, 1.0)
                
                if record.file_size <= expected_size * 1.2:  # Within 20% of expected
                    compression_eff = 100
                elif record.file_size <= expected_size * 2:  # Within 100% of expected
                    compression_eff = 80
                else:
                    compression_eff = max(50 - (record.file_size - expected_size * 2) * 10, 0)
                
                record.compression_efficiency = compression_eff
            else:
                record.compression_efficiency = 0
    
    @api.depends('file_size', 'file_format', 'scan_date')
    def _compute_storage_analytics(self):
        """Compute storage-related analytics"""
        for record in self:
            # Storage cost estimation (per MB per year)
            cost_per_mb_year = 0.10  # Base cost
            
            # Format-based cost multipliers
            format_multipliers = {
                'tiff': 1.5,   # Higher storage needs
                'pdf': 1.0,    # Standard
                'png': 1.2,    # Moderate
                'jpeg': 0.8,   # Compressed
                'docx': 1.1,   # Moderate
                'txt': 0.5     # Minimal
            }
            
            multiplier = format_multipliers.get(record.file_format, 1.0)
            
            if record.file_size:
                record.storage_cost_estimate = record.file_size * cost_per_mb_year * multiplier
            else:
                record.storage_cost_estimate = 0
            
            # Access frequency prediction based on document age and type
            if record.scan_date:
                days_old = (fields.Datetime.now() - record.scan_date).days
                
                # Newer documents accessed more frequently
                if days_old < 30:
                    base_frequency = 8.0
                elif days_old < 90:
                    base_frequency = 4.0
                elif days_old < 365:
                    base_frequency = 2.0
                else:
                    base_frequency = 0.5
                
                # Format influence on access
                format_access_factors = {
                    'pdf': 1.2,    # More accessible
                    'docx': 1.1,   # Editable, more useful
                    'tiff': 0.8,   # Less accessible
                    'jpeg': 0.9,   # Moderate
                    'png': 0.9,    # Moderate
                    'txt': 1.0     # Standard
                }
                
                access_factor = format_access_factors.get(record.file_format, 1.0)
                record.access_frequency_prediction = base_frequency * access_factor
            else:
                record.access_frequency_prediction = 1.0
            
            # Migration priority (older formats and larger files need migration)
            migration_score = 30  # Base score
            
            # Format age factor
            format_ages = {
                'txt': 0,      # Timeless
                'pdf': 5,      # Modern standard
                'png': 10,     # Moderately old
                'jpeg': 15,    # Older
                'docx': 5,     # Modern
                'tiff': 25     # Older format
            }
            migration_score += format_ages.get(record.file_format, 15)
            
            # Size factor (larger files benefit more from migration)
            if record.file_size and record.file_size > 2.0:
                migration_score += min(record.file_size * 5, 30)
            
            # Age factor
            if record.scan_date:
                years_old = (fields.Datetime.now() - record.scan_date).days / 365
                migration_score += min(years_old * 10, 25)
            
            record.migration_priority_score = min(migration_score, 100)
    
    @api.depends('scan_date', 'scanned_by', 'scanner_device')
    def _compute_process_analytics(self):
        """Compute process optimization analytics"""
        for record in self:
            # Scanning efficiency based on file characteristics and timing
            efficiency_score = 70  # Base efficiency
            
            # File size vs quality efficiency
            if record.file_size and record.scan_quality:
                quality_weights = {'low': 0.5, 'medium': 1.0, 'high': 1.5, 'archive': 2.0}
                weight = quality_weights.get(record.scan_quality, 1.0)
                
                # Efficient if file size is proportional to quality
                expected_size = weight * 1.5  # MB
                if record.file_size <= expected_size * 1.3:
                    efficiency_score += 15
                elif record.file_size > expected_size * 2:
                    efficiency_score -= 10
            
            # Scanner consistency (same device/person indicates process optimization)
            if record.scanned_by:
                recent_scans = self.search([
                    ('scanned_by', '=', record.scanned_by.id),
                    ('scan_date', '>=', fields.Datetime.now() - timedelta(days=30))
                ])
                
                if len(recent_scans) >= 5:  # Regular scanning activity
                    efficiency_score += 10
                    
                    # Device consistency
                    devices = recent_scans.mapped('scanner_device')
                    if len(set(devices)) <= 2:  # Using 1-2 devices consistently
                        efficiency_score += 5
            
            record.scanning_efficiency_score = min(efficiency_score, 100)
            
            # Automation readiness assessment
            automation_score = 40  # Base automation potential
            
            # Standard format suggests automation readiness
            if record.file_format in ['pdf', 'tiff']:
                automation_score += 20
            
            # Consistent quality settings
            if record.scan_quality in ['medium', 'high']:
                automation_score += 15
            
            # Device standardization
            if record.scanner_device:
                device_scans = self.search_count([
                    ('scanner_device', '=', record.scanner_device),
                    ('scan_date', '>=', fields.Datetime.now() - timedelta(days=60))
                ])
                
                if device_scans >= 10:  # Regular use suggests standardization
                    automation_score += 20
            
            record.automation_readiness = min(automation_score, 100)
            
            # Workflow optimization potential
            optimization_score = 50
            
            # Time-based analysis
            if record.scan_date:
                hour = record.scan_date.hour
                # Optimal scanning hours (avoiding peak times)
                if 8 <= hour <= 10 or 14 <= hour <= 16:
                    optimization_score += 15
                elif hour < 7 or hour > 19:
                    optimization_score -= 10
            
            # Quality-size optimization
            if record.digitization_quality_score > 80 and record.compression_efficiency > 70:
                optimization_score += 20
            
            record.workflow_optimization_potential = min(optimization_score, 100)
    
    def action_download(self):
        """Download the digital copy file"""
        if self.file_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self.file_attachment_id.id}?download=true',
                'target': 'self',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No File Available',
                    'message': 'No digital file is attached to this record.',
                    'type': 'warning',
                }
            }
