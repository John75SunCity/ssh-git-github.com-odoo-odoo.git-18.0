# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class RecordsDocumentType(models.Model):
    """Model for document types in records management."""
    _name = 'records.document.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Record Document Type'
    _order = 'name'

    name = fields.Char(string='Type Name', required=True, translate=True)
    description = fields.Text(string='Description', translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        readonly=True
    )

    # Phase 2: Audit & Compliance Fields (10 fields) 
    audit_required = fields.Boolean(
        string='Audit Required',
        default=False
    )
    compliance_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review')
    ], string='Compliance Status', default='pending')
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Risk Level', default='low')
    regulatory_requirement = fields.Text(string='Regulatory Requirement')
    approval_required = fields.Boolean(
        string='Approval Required',
        default=False
    )
    approved_by = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Datetime(string='Approval Date')
    security_classification = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret')
    ], string='Security Classification', default='internal')
    retention_compliance = fields.Boolean(
        string='Retention Compliance',
        default=True
    )
    compliance_notes = fields.Text(string='Compliance Notes')

    # Enhanced tracking and technical fields for records management
    activity_ids = fields.One2many('mail.activity', compute='_compute_activity_ids', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', compute='_compute_message_followers', string='Followers')
    message_ids = fields.One2many('mail.message', compute='_compute_message_ids', string='Messages')
    
    # Technical view fields
    arch = fields.Text(string='View Architecture')
    model = fields.Char(string='Model Name', default='records.document.type')
    res_model = fields.Char(string='Resource Model', default='records.document.type')
    help = fields.Text(string='Help Text')
    view_mode = fields.Char(string='View Mode', default='tree,form')

    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count',
        store=False
    )
    
    # Phase 3: Advanced Document Type Analytics
    
    # Usage Analytics
    document_type_utilization = fields.Float(
        string='Type Utilization %',
        compute='_compute_usage_analytics',
        store=True,
        help='Utilization rate of this document type'
    )
    
    growth_trend_indicator = fields.Selection([
        ('declining', 'Declining'),
        ('stable', 'Stable'),
        ('growing', 'Growing'),
        ('rapid_growth', 'Rapid Growth')
    ], string='Growth Trend',
       compute='_compute_usage_analytics',
       store=True,
       help='Growth trend for documents of this type')
    
    seasonal_pattern_score = fields.Float(
        string='Seasonal Pattern Score',
        compute='_compute_usage_analytics',
        store=True,
        help='Score indicating seasonal usage patterns'
    )
    
    # Classification Analytics
    classification_accuracy_score = fields.Float(
        string='Classification Accuracy Score',
        compute='_compute_classification_analytics',
        store=True,
        help='Accuracy of document classification for this type'
    )
    
    auto_classification_potential = fields.Float(
        string='Auto-Classification Potential %',
        compute='_compute_classification_analytics',
        store=True,
        help='Potential for automated classification'
    )
    
    type_complexity_rating = fields.Selection([
        ('simple', 'Simple'),
        ('moderate', 'Moderate'),
        ('complex', 'Complex'),
        ('highly_complex', 'Highly Complex')
    ], string='Type Complexity',
       compute='_compute_classification_analytics',
       store=True,
       help='Complexity rating for this document type')
    
    # Compliance Analytics
    regulatory_compliance_score = fields.Float(
        string='Regulatory Compliance Score',
        compute='_compute_compliance_analytics',
        store=True,
        help='Overall regulatory compliance assessment'
    )
    
    audit_readiness_level = fields.Selection([
        ('poor', 'Poor'),
        ('fair', 'Fair'),
        ('good', 'Good'),
        ('excellent', 'Excellent')
    ], string='Audit Readiness Level',
       compute='_compute_compliance_analytics',
       store=True,
       help='Assessment of audit readiness')
    
    compliance_risk_assessment = fields.Float(
        string='Compliance Risk Assessment',
        compute='_compute_compliance_analytics',
        store=True,
        help='Risk assessment score for compliance issues'
    )
    
    @api.depends('name')
    def _compute_document_count(self) -> None:
        for record in self:
            count = self.env['records.document'].search_count([
                ('document_type_id', '=', record.id)
            ])
            record.document_count = count
    
    @api.depends('document_count', 'active')
    def _compute_usage_analytics(self):
        """Compute document type usage analytics"""
        for record in self:
            if not record.active:
                record.document_type_utilization = 0
                record.growth_trend_indicator = 'declining'
                record.seasonal_pattern_score = 0
                continue
            
            # Total documents across all types for comparison
            total_documents = self.env['records.document'].search_count([])
            
            if total_documents > 0:
                utilization = (record.document_count / total_documents) * 100
                record.document_type_utilization = round(utilization, 2)
            else:
                record.document_type_utilization = 0
            
            # Growth trend analysis (last 90 days vs previous 90 days)
            current_date = fields.Date.today()
            last_90_days = current_date - timedelta(days=90)
            previous_90_days = current_date - timedelta(days=180)
            
            recent_docs = self.env['records.document'].search_count([
                ('document_type_id', '=', record.id),
                ('create_date', '>=', last_90_days)
            ])
            
            previous_docs = self.env['records.document'].search_count([
                ('document_type_id', '=', record.id),
                ('create_date', '>=', previous_90_days),
                ('create_date', '<', last_90_days)
            ])
            
            if previous_docs > 0:
                growth_rate = ((recent_docs - previous_docs) / previous_docs) * 100
            else:
                growth_rate = 100 if recent_docs > 0 else 0
            
            if growth_rate > 50:
                record.growth_trend_indicator = 'rapid_growth'
            elif growth_rate > 10:
                record.growth_trend_indicator = 'growing'
            elif growth_rate > -10:
                record.growth_trend_indicator = 'stable'
            else:
                record.growth_trend_indicator = 'declining'
            
            # Seasonal pattern analysis
            monthly_counts = []
            for month in range(12):
                month_start = current_date.replace(day=1) - timedelta(days=30*month)
                month_end = month_start + timedelta(days=30)
                
                count = self.env['records.document'].search_count([
                    ('document_type_id', '=', record.id),
                    ('create_date', '>=', month_start),
                    ('create_date', '<', month_end)
                ])
                monthly_counts.append(count)
            
            if monthly_counts and max(monthly_counts) > 0:
                # Calculate coefficient of variation as seasonality indicator
                avg_count = sum(monthly_counts) / len(monthly_counts)
                variance = sum((x - avg_count) ** 2 for x in monthly_counts) / len(monthly_counts)
                cv = (variance ** 0.5) / avg_count if avg_count > 0 else 0
                
                # Convert to 0-100 scale where higher = more seasonal
                seasonal_score = min(cv * 100, 100)
                record.seasonal_pattern_score = round(seasonal_score, 2)
            else:
                record.seasonal_pattern_score = 0
    
    @api.depends('security_classification', 'risk_level', 'name')
    def _compute_classification_analytics(self):
        """Compute document classification analytics"""
        for record in self:
            # Classification accuracy based on security classification and risk level alignment
            base_accuracy = 75  # Base accuracy score
            
            # Security classification consistency
            security_scores = {
                'public': 90,       # Easy to classify
                'internal': 85,     # Moderate complexity
                'confidential': 70, # More complex
                'secret': 60        # Most complex
            }
            
            security_score = security_scores.get(record.security_classification, 75)
            
            # Risk level classification difficulty
            risk_scores = {
                'low': 90,      # Easy to assess
                'medium': 80,   # Moderate difficulty
                'high': 70,     # More difficult
                'critical': 60  # Most difficult
            }
            
            risk_score = risk_scores.get(record.risk_level, 75)
            
            # Average of security and risk classification scores
            classification_accuracy = (security_score + risk_score) / 2
            
            # Adjust for document volume (more documents = better training data = higher accuracy)
            if record.document_count > 100:
                classification_accuracy += 10
            elif record.document_count > 50:
                classification_accuracy += 5
            elif record.document_count < 10:
                classification_accuracy -= 10
            
            record.classification_accuracy_score = min(max(classification_accuracy, 0), 100)
            
            # Auto-classification potential
            auto_potential = 40  # Base potential
            
            # Standard types have higher auto-classification potential
            standard_types = ['invoice', 'contract', 'report', 'memo', 'email', 'form']
            if any(keyword in record.name.lower() for keyword in standard_types):
                auto_potential += 30
            
            # Security classification affects automation potential
            auto_factors = {
                'public': 25,       # High automation potential
                'internal': 20,     # Good automation potential
                'confidential': 10, # Lower automation potential
                'secret': 5         # Minimal automation potential
            }
            auto_potential += auto_factors.get(record.security_classification, 15)
            
            # Document volume helps with automation
            if record.document_count > 50:
                auto_potential += 15
            elif record.document_count > 20:
                auto_potential += 10
            
            record.auto_classification_potential = min(max(auto_potential, 0), 100)
            
            # Type complexity rating
            complexity_score = 30  # Base complexity
            
            # Security classification adds complexity
            complexity_factors = {
                'public': 0,
                'internal': 10,
                'confidential': 25,
                'secret': 40
            }
            complexity_score += complexity_factors.get(record.security_classification, 10)
            
            # Risk level adds complexity
            risk_complexity = {
                'low': 0,
                'medium': 15,
                'high': 30,
                'critical': 45
            }
            complexity_score += risk_complexity.get(record.risk_level, 15)
            
            # Regulatory requirements add complexity
            if record.regulatory_requirement and len(record.regulatory_requirement.strip()) > 50:
                complexity_score += 20
            
            # Approval requirements add complexity
            if record.approval_required:
                complexity_score += 15
            
            if complexity_score <= 40:
                record.type_complexity_rating = 'simple'
            elif complexity_score <= 60:
                record.type_complexity_rating = 'moderate'
            elif complexity_score <= 80:
                record.type_complexity_rating = 'complex'
            else:
                record.type_complexity_rating = 'highly_complex'
    
    @api.depends('compliance_status', 'audit_required', 'approval_required', 'retention_compliance')
    def _compute_compliance_analytics(self):
        """Compute compliance-related analytics"""
        for record in self:
            # Base compliance score
            base_score = 60
            
            # Compliance status factor
            status_scores = {
                'approved': 25,
                'under_review': 10,
                'pending': 0,
                'rejected': -30
            }
            base_score += status_scores.get(record.compliance_status, 0)
            
            # Retention compliance
            if record.retention_compliance:
                base_score += 15
            else:
                base_score -= 20
            
            # Approval process completeness
            if record.approval_required:
                if record.approved_by and record.approval_date:
                    base_score += 10
                else:
                    base_score -= 15
            
            # Regulatory requirements documentation
            if record.regulatory_requirement and len(record.regulatory_requirement.strip()) > 20:
                base_score += 10
            
            # Compliance notes quality
            if record.compliance_notes and len(record.compliance_notes.strip()) > 30:
                base_score += 5
            
            record.regulatory_compliance_score = min(max(base_score, 0), 100)
            
            # Audit readiness assessment
            audit_score = record.regulatory_compliance_score
            
            # Audit requirement readiness
            if record.audit_required:
                # Required audits should have proper documentation
                if record.compliance_notes and record.regulatory_requirement:
                    audit_score += 10
                else:
                    audit_score -= 15
            
            # Document volume for audit sampling
            if record.document_count > 25:
                audit_score += 5  # Good sample size
            elif record.document_count < 5:
                audit_score -= 10  # Poor sample size
            
            if audit_score >= 90:
                record.audit_readiness_level = 'excellent'
            elif audit_score >= 75:
                record.audit_readiness_level = 'good'
            elif audit_score >= 60:
                record.audit_readiness_level = 'fair'
            else:
                record.audit_readiness_level = 'poor'
            
            # Compliance risk assessment (inverted compliance score)
            risk_score = 100 - record.regulatory_compliance_score
            
            # Risk level amplifies compliance risk
            risk_multipliers = {
                'low': 0.8,
                'medium': 1.0,
                'high': 1.3,
                'critical': 1.6
            }
            
            multiplier = risk_multipliers.get(record.risk_level, 1.0)
            risk_score *= multiplier
            
            # Security classification affects risk
            security_risk_factors = {
                'public': 0.7,
                'internal': 1.0,
                'confidential': 1.4,
                'secret': 1.8
            }
            
            security_factor = security_risk_factors.get(record.security_classification, 1.0)
            risk_score *= security_factor
            
            record.compliance_risk_assessment = min(max(risk_score, 0), 100)

    def action_view_type_documents(self) -> dict:
        """View all documents of this type"""
        self.ensure_one()
        return {
            'name': _('Documents of Type: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('document_type_id', '=', self.id)],
            'context': {'default_document_type_id': self.id},
        }

    @api.depends()
    def _compute_activity_ids(self):
        """Compute activities related to this document type"""
        for record in self:
            activities = self.env['mail.activity'].search([
                ('res_model', '=', record._name),
                ('res_id', '=', record.id)
            ])
            record.activity_ids = activities

    @api.depends()
    def _compute_message_followers(self):
        """Compute followers of this document type"""
        for record in self:
            followers = self.env['mail.followers'].search([
                ('res_model', '=', record._name),
                ('res_id', '=', record.id)
            ])
            record.message_follower_ids = followers

    @api.depends()
    def _compute_message_ids(self):
        """Compute messages related to this document type"""
        for record in self:
            messages = self.env['mail.message'].search([
                ('model', '=', record._name),
                ('res_id', '=', record.id)
            ])
            record.message_ids = messages
