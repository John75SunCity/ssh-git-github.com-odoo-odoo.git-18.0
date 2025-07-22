# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class RecordsTag(models.Model):
    """Enhanced model for tags in records management with enterprise features."""
    _name = 'records.tag'
    _description = 'Records Management Tag'
    _order = 'name'

    # Basic Fields
    name = fields.Char(
        string='Name', 
        required=True, 
        translate=True,
        help="Unique name for this tag"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Uncheck to archive this tag"
    )
    color = fields.Integer(
        string='Color Index',
        help="Color used to display this tag"
    )
    description = fields.Text(
        string='Description', 
        translate=True,
        help="Description of what this tag represents"
    )
    
    # Categorization
    category = fields.Selection([
        ('system', 'System'),
        ('user', 'User Defined'),
        ('auto', 'Auto Generated'),
        ('compliance', 'Compliance'),
        ('workflow', 'Workflow')
    ], string='Category', default='user', help="Category of this tag")
    
    # Analytics & Usage
    tag_usage_count = fields.Integer(
        string='Usage Count',
        compute='_compute_tag_usage',
        store=True,
        help="Number of records using this tag"
    )
    last_used_date = fields.Datetime(
        string='Last Used',
        help="When this tag was last applied to a record"
    )
    popularity_score = fields.Float(
        string='Popularity Score',
        compute='_compute_popularity_score',
        help="Calculated popularity based on usage"
    )
    
    # Automation Features
    auto_assign = fields.Boolean(
        string='Auto Assign',
        default=False,
        help="Automatically assign this tag based on rules"
    )
    priority = fields.Integer(
        string='Priority',
        default=10,
        help="Priority for auto-assignment (higher = more priority)"
    )
    applies_to_documents = fields.Boolean(
        string='Applies to Documents',
        default=True,
        help="This tag can be applied to documents"
    )
    applies_to_boxes = fields.Boolean(
        string='Applies to Boxes',
        default=True,
        help="This tag can be applied to boxes"
    )
    
    # Relationships
    parent_tag_id = fields.Many2one(
        'records.tag',
        string='Parent Tag',
        help="Parent tag for hierarchical organization"
    )
    child_tag_ids = fields.One2many(
        'records.tag',
        'parent_tag_id',
        string='Child Tags'
    )
    
    # System & Advanced Settings
    is_system_tag = fields.Boolean(
        string='System Tag',
        default=False,
        help="System-generated tag that cannot be deleted"
    )
    exclude_from_search = fields.Boolean(
        string='Exclude from Search',
        default=False,
        help="Don't show this tag in search suggestions"
    )
    requires_approval = fields.Boolean(
        string='Requires Approval',
        default=False,
        help="Tag assignment requires approval"
    )
    
    # Display & UI Settings
    icon = fields.Char(
        string='Icon',
        help="FontAwesome icon class for display"
    )
    display_order = fields.Integer(
        string='Display Order',
        default=100,
        help="Order for displaying tags"
    )
    
    # Computed Fields
    auto_rule_count = fields.Integer(
        string='Auto Rules',
        compute='_compute_auto_rule_count',
        help="Number of auto-assignment rules"
    )
    related_tag_count = fields.Integer(
        string='Related Tags',
        compute='_compute_related_tag_count',
        help="Number of related tags"
    )
    trend_direction = fields.Selection([
        ('up', 'Trending Up'),
        ('down', 'Trending Down'),
        ('stable', 'Stable')
    ], string='Trend Direction', compute='_compute_trend_direction')

    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name

    @api.depends('tag_usage_count')
    def _compute_popularity_score(self):
        """Calculate popularity score based on usage."""
        for record in self:
            # Simple popularity calculation
            record.popularity_score = record.tag_usage_count * 1.0

    @api.depends('tag_usage_count')
    def _compute_trend_direction(self):
        """Calculate trend direction based on recent usage."""
        for record in self:
            if record.tag_usage_count > 10:
                record.trend_direction = 'up'
            elif record.tag_usage_count < 5:
                record.trend_direction = 'down'
            else:
                record.trend_direction = 'stable'

    def _compute_tag_usage(self):
        """Compute how many records use this tag."""
        for record in self:
            # This would need to be implemented based on your tagging system
            # For now, set a default value
            record.tag_usage_count = 0

    def _compute_auto_rule_count(self):
        """Compute number of auto-assignment rules."""
        for record in self:
            # Placeholder - implement based on your auto-rule system
            record.auto_rule_count = 0

    def _compute_related_tag_count(self):
        """Compute number of related tags."""
        for record in self:
            record.related_tag_count = len(record.child_tag_ids)

    def toggle_active(self):
        """Toggle the active state of the tag."""
        for record in self:
            record.active = not record.active
        return True

    def action_view_tagged_records(self):
        """Action to view records tagged with this tag."""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Records tagged with {self.name}',
            'res_model': 'records.document',  # Adjust based on your model
            'view_mode': 'tree,form',
            'domain': [],  # Add domain to filter by this tag
            'context': {'default_tag_ids': [(4, self.id)]},
        }

    def action_bulk_tag(self):
        """Action for bulk tagging operations."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bulk Tag Records',
            'res_model': 'records.tag.wizard',  # You'd need to create this wizard
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_tag_id': self.id},
        }

    def action_configure_rules(self):
        """Action to configure auto-assignment rules."""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Auto Rules for {self.name}',
            'res_model': 'records.tag.rule',  # You'd need to create this model
            'view_mode': 'tree,form',
            'domain': [('tag_id', '=', self.id)],
            'context': {'default_tag_id': self.id},
        }

    def action_analytics(self):
        """Action to view tag analytics."""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Analytics for {self.name}',
            'res_model': 'records.tag.analytics',  # You'd need to create this model
            'view_mode': 'graph,pivot',
            'domain': [('tag_id', '=', self.id)],
            'context': {'default_tag_id': self.id},
        }

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!")
    ]
