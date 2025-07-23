# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class RecordsTag(models.Model, mail.thread):
    """Minimal tag model for initial deployment - will be enhanced later."""
    _name = 'records.tag'
    _description = 'Records Management Tag'
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
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    category = fields.Selection([('general', 'General'), ('legal', 'Legal'), ('financial', 'Financial'), ('hr', 'HR')], string='Category')
    priority = fields.Selection([('low', 'Low'), ('normal', 'Normal'), ('high', 'High')], string='Priority', default='normal')
    
    # TODO: Enhanced fields will be added in next deployment phase:
    # - active field
    # - description field  
    # - category selection
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
