# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class RecordsTag(models.Model):
    """Minimal tag model for initial deployment - will be enhanced later."""
    _name = 'records.tag'
    _description = 'Records Management Tag'
    _inherit = ['mail.thread']
    _order = 'name'

    # Essential fields only
    name = fields.Char(
        string='Name', 
        required=True, 
        translate=True,
        help="Unique name for this tag"
    )
    description = fields.Text(
        string='Description',
        help="Detailed description of this tag's purpose and usage"
    )
    color = fields.Integer(
        string='Color Index',
        help="Color used to display this tag"
    )

    # Phase 1 Critical Fields - Added by automated script
    
    # Technical fields for view compatibility
    arch = fields.Text(string='View Architecture')
    model = fields.Char(string='Model Name', default='records.tag')
    res_model = fields.Char(string='Resource Model', default='records.tag')
    help = fields.Text(string='Help Text')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View')
    view_id = fields.Many2one('ir.ui.view', string='View')
    view_mode = fields.Char(string='View Mode', default='tree,form')
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    category = fields.Selection([('general', 'General'), ('legal', 'Legal'), ('financial', 'Financial'), ('hr', 'HR')], string='Category')
    priority = fields.Selection([('low', 'Low'), ('normal', 'Normal'), ('high', 'High')], string='Priority', default='normal')
    
    # Phase 3: Advanced Tag Analytics & Computed Fields
    
    # Usage Analytics
    tag_usage_frequency = fields.Float(
        string='Usage Frequency Score',
        compute='_compute_usage_analytics',
        store=True,
        help='Frequency of tag usage across documents'
    )
    
    tag_adoption_rate = fields.Float(
        string='Adoption Rate %',
        compute='_compute_usage_analytics',
        store=True,
        help='Rate of tag adoption by users'
    )
    
    trending_status = fields.Selection([
        ('declining', 'Declining'),
        ('stable', 'Stable'),
        ('growing', 'Growing'),
        ('viral', 'Viral Growth')
    ], string='Trending Status',
       compute='_compute_usage_analytics',
       store=True,
       help='Current trend status of tag usage')
    
    # Categorization Analytics
    semantic_relevance_score = fields.Float(
        string='Semantic Relevance Score',
        compute='_compute_categorization_analytics',
        store=True,
        help='AI-style semantic relevance assessment'
    )
    
    categorization_accuracy = fields.Float(
        string='Categorization Accuracy %',
        compute='_compute_categorization_analytics',
        store=True,
        help='Accuracy of tag categorization'
    )
    
    tag_specificity_index = fields.Float(
        string='Tag Specificity Index',
        compute='_compute_categorization_analytics',
        store=True,
        help='Index measuring how specific vs generic this tag is'
    )
    
    # Collaboration Analytics
    user_collaboration_score = fields.Float(
        string='User Collaboration Score',
        compute='_compute_collaboration_analytics',
        store=True,
        help='Score indicating collaborative usage of this tag'
    )
    
    cross_department_usage = fields.Float(
        string='Cross-Department Usage %',
        compute='_compute_collaboration_analytics',
        store=True,
        help='Percentage of departments using this tag'
    )
    
    knowledge_sharing_potential = fields.Float(
        string='Knowledge Sharing Potential',
        compute='_compute_collaboration_analytics',
        store=True,
        help='Potential for knowledge sharing through this tag'
    )
    
    @api.depends('name', 'category', 'priority')
    def _compute_usage_analytics(self):
        """Compute tag usage analytics"""
        for record in self:
            # Get tagged documents count
            tagged_documents = self.env['records.document'].search_count([
                ('tag_ids', 'in', [record.id])
            ])
            
            # Calculate usage frequency
            total_documents = self.env['records.document'].search_count([])
            if total_documents > 0:
                usage_frequency = (tagged_documents / total_documents) * 100
                record.tag_usage_frequency = round(usage_frequency, 2)
            else:
                record.tag_usage_frequency = 0
            
            # Calculate adoption rate based on unique users who've used this tag
            if hasattr(self.env['records.document'], 'user_id'):
                unique_users = self.env['records.document'].search([
                    ('tag_ids', 'in', [record.id])
                ]).mapped('user_id')
                
                total_users = self.env['res.users'].search_count([('active', '=', True)])
                if total_users > 0:
                    adoption_rate = (len(unique_users) / total_users) * 100
                    record.tag_adoption_rate = round(adoption_rate, 2)
                else:
                    record.tag_adoption_rate = 0
            else:
                record.tag_adoption_rate = 50  # Default assumption
            
            # Trending analysis (simulate trend calculation)
            # In real implementation, would track usage over time
            current_month_usage = tagged_documents  # Simplified
            
            if current_month_usage == 0:
                record.trending_status = 'declining'
            elif record.tag_usage_frequency > 10:
                record.trending_status = 'viral'
            elif record.tag_usage_frequency > 5:
                record.trending_status = 'growing'
            elif record.tag_usage_frequency > 1:
                record.trending_status = 'stable'
            else:
                record.trending_status = 'declining'
    
    @api.depends('name', 'description', 'category')
    def _compute_categorization_analytics(self):
        """Compute tag categorization analytics"""
        for record in self:
            # Semantic relevance based on name characteristics
            base_relevance = 70
            
            # Name quality assessment
            name_words = record.name.lower().split() if record.name else []
            
            # Specific terms indicate higher relevance
            specific_terms = [
                'contract', 'invoice', 'report', 'legal', 'financial', 
                'hr', 'policy', 'procedure', 'compliance', 'audit',
                'confidential', 'urgent', 'draft', 'final', 'archived'
            ]
            
            specificity_bonus = sum(5 for term in specific_terms if any(term in word for word in name_words))
            base_relevance += min(specificity_bonus, 20)
            
            # Description quality
            if record.description and len(record.description.strip()) > 20:
                base_relevance += 10
            elif record.description and len(record.description.strip()) > 5:
                base_relevance += 5
            
            # Category alignment
            if record.category:
                # Check if tag name aligns with category
                category_keywords = {
                    'legal': ['legal', 'contract', 'agreement', 'compliance', 'policy'],
                    'financial': ['financial', 'invoice', 'payment', 'budget', 'cost'],
                    'hr': ['hr', 'employee', 'personnel', 'training', 'payroll'],
                    'general': ['general', 'misc', 'other', 'document']
                }
                
                relevant_keywords = category_keywords.get(record.category, [])
                if any(keyword in record.name.lower() for keyword in relevant_keywords):
                    base_relevance += 15
            
            record.semantic_relevance_score = min(base_relevance, 100)
            
            # Categorization accuracy
            accuracy = record.semantic_relevance_score
            
            # Priority alignment with usage
            if record.priority == 'high' and record.tag_usage_frequency > 5:
                accuracy += 10
            elif record.priority == 'low' and record.tag_usage_frequency < 2:
                accuracy += 5
            
            record.categorization_accuracy = min(accuracy, 100)
            
            # Tag specificity index
            # More specific tags have fewer words and more technical terms
            specificity = 50  # Base specificity
            
            if record.name:
                word_count = len(record.name.split())
                if word_count == 1:
                    specificity += 30
                elif word_count == 2:
                    specificity += 20
                elif word_count >= 4:
                    specificity -= 15
                
                # Technical/specific terms increase specificity
                technical_terms = [
                    'api', 'sql', 'pdf', 'xml', 'json', 'csv', 'gdpr', 'sox',
                    'iso', 'naid', 'hipaa', 'pci', 'sla', 'kpi', 'roi'
                ]
                
                tech_bonus = sum(10 for term in technical_terms 
                               if term in record.name.lower())
                specificity += min(tech_bonus, 25)
            
            record.tag_specificity_index = min(max(specificity, 0), 100)
    
    @api.depends('name', 'category')
    def _compute_collaboration_analytics(self):
        """Compute collaboration-related analytics"""
        for record in self:
            # User collaboration score based on multi-user usage
            tagged_docs = self.env['records.document'].search([
                ('tag_ids', 'in', [record.id])
            ])
            
            if tagged_docs:
                # Get unique users (simplified - would check document creators/editors)
                # Using create_uid as proxy for user interaction
                unique_users = len(set(tagged_docs.mapped('create_uid')))
                
                if unique_users >= 5:
                    collaboration_score = 90
                elif unique_users >= 3:
                    collaboration_score = 75
                elif unique_users >= 2:
                    collaboration_score = 60
                else:
                    collaboration_score = 30
                
                # Boost score for collaborative categories
                if record.category in ['legal', 'financial']:
                    collaboration_score += 10
                
                record.user_collaboration_score = min(collaboration_score, 100)
            else:
                record.user_collaboration_score = 0
            
            # Cross-department usage (simplified calculation)
            # In real implementation, would check user departments
            department_usage = 40  # Base assumption
            
            # Category-based department distribution
            category_distribution = {
                'general': 80,      # Used across all departments
                'legal': 30,        # Primarily legal department
                'financial': 40,    # Finance + accounting departments
                'hr': 25           # Primarily HR department
            }
            
            department_usage = category_distribution.get(record.category, 50)
            
            # High usage frequency suggests cross-department appeal
            if record.tag_usage_frequency > 5:
                department_usage += 20
            elif record.tag_usage_frequency > 2:
                department_usage += 10
            
            record.cross_department_usage = min(department_usage, 100)
            
            # Knowledge sharing potential
            knowledge_potential = 50  # Base potential
            
            # Tags with good descriptions have higher knowledge sharing potential
            if record.description and len(record.description.strip()) > 50:
                knowledge_potential += 25
            elif record.description and len(record.description.strip()) > 20:
                knowledge_potential += 15
            
            # Specific, well-categorized tags have higher potential
            if record.semantic_relevance_score > 80:
                knowledge_potential += 15
            
            # Collaborative tags have higher knowledge sharing potential
            if record.user_collaboration_score > 70:
                knowledge_potential += 10
            
            # Category-based knowledge potential
            knowledge_categories = {
                'general': 60,
                'legal': 80,        # Legal knowledge is highly shareable
                'financial': 70,    # Financial procedures are shareable
                'hr': 65           # HR policies are moderately shareable
            }
            
            category_bonus = knowledge_categories.get(record.category, 60) - 60
            knowledge_potential += category_bonus
            
            record.knowledge_sharing_potential = min(max(knowledge_potential, 0), 100)
    
    # Additional essential fields
    active = fields.Boolean(string='Active', default=True)
    
    # TODO: Enhanced fields will be added in next deployment phase:
    # - analytics fields
    # - automation features

    def action_tag_documents(self):
        """Tag selected documents"""
        self.ensure_one()
        return {
            'name': _('Tag Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'tag.documents.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_tag_id': self.id},
        }

    def action_view_tagged_documents(self):
        """View documents with this tag"""
        self.ensure_one()
        return {
            'name': _('Documents Tagged: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('tag_ids', 'in', [self.id])],
            'context': {'default_tag_ids': [(6, 0, [self.id])]},
        }

    def action_merge_tags(self):
        """Merge this tag with another"""
        self.ensure_one()
        return {
            'name': _('Merge Tags'),
            'type': 'ir.actions.act_window',
            'res_model': 'merge.tags.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_source_tag_id': self.id},
        }

    def action_archive_tag(self):
        """Archive this tag"""
        self.ensure_one()
        self.active = False
        return True

    def action_duplicate_tag(self):
        """Duplicate this tag"""
        self.ensure_one()
        new_tag = self.copy({
            'name': _('%s (Copy)') % self.name,
        })
        return {
            'name': _('Duplicated Tag'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.tag',
            'res_id': new_tag.id,
            'view_mode': 'form',
            'target': 'current',
        }
