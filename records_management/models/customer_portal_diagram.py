# -*- coding: utf-8 -*-
"""
Customer Portal Diagram Module

This model generates data for an interactive organizational diagram,
visualizing the relationships between companies, departments, and users
for customer portal users.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CustomerPortalDiagram(models.Model):
    _name = 'customer.portal.diagram'
    _description = 'Interactive Customer Portal Organization Diagram'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # CORE & CONFIGURATION
    # ============================================================================
    name = fields.Char(string="Diagram Name", required=True, default="Customer Organization Diagram")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)

    # ============================================================================
    # DIAGRAM DATA (Computed)
    # ============================================================================
    diagram_data = fields.Text(string="Diagram JSON Data", compute='_compute_diagram_data', help="JSON data for the diagram visualization.")
    diagram_stats = fields.Text(string="Diagram Statistics", compute='_compute_diagram_stats', help="Summary statistics of the diagram.")

    # ============================================================================
    # FILTER & DISPLAY OPTIONS
    # ============================================================================
    search_partner_id = fields.Many2one('res.partner', string="Filter by Customer")
    search_department_id = fields.Many2one('records.department', string="Filter by Department", domain="[('partner_id', '=', search_partner_id)]")
    search_query = fields.Char(string="Search Query")
    show_access_rights = fields.Boolean(string="Show Access Rights", default=False)
    layout_type = fields.Selection([
        ('hierarchical', 'Hierarchical'),
        ('force_directed', 'Force Directed')
    ], string="Layout Type", default='hierarchical', required=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('search_partner_id', 'search_department_id', 'search_query', 'show_access_rights', 'layout_type')
    def _compute_diagram_data(self):
        """
        Compute the diagram nodes and edges data for the interactive visualization.
        This method orchestrates the generation of the entire diagram structure.
        """
        for record in self:
            nodes = []
            edges = []

            # Determine the scope based on the user type (portal vs. internal)
            partner_scope = self._get_portal_user_scope()
            if record.search_partner_id:
                partner_scope = record.search_partner_id

            if not partner_scope:
                record.diagram_data = json.dumps({'nodes': [], 'edges': []})
                continue

            # Generate nodes and edges for different elements
            nodes, edges = self._generate_partner_nodes(nodes, edges, partner_scope)
            nodes, edges = self._generate_department_nodes(nodes, edges, partner_scope)
            nodes, edges = self._generate_user_nodes(nodes, edges, partner_scope)

            # Apply filtering if any search criteria is provided
            # Note: A full implementation would filter nodes/edges here based on search_query

            record.diagram_data = json.dumps({'nodes': nodes, 'edges': edges})

    @api.depends('diagram_data')
    def _compute_diagram_stats(self):
        """Compute diagram statistics for display."""
        for record in self:
            try:
                data = json.loads(record.diagram_data or '{}')
                nodes = data.get('nodes', [])
                stats = {
                    'partners': len([n for n in nodes if n.get('group') == 'partner']),
                    'departments': len([n for n in nodes if n.get('group') == 'department']),
                    'users': len([n for n in nodes if n.get('group') == 'user']),
                }
                record.diagram_stats = json.dumps(stats, indent=2)
            except (json.JSONDecodeError, TypeError):
                record.diagram_stats = "Invalid data format."

    # ============================================================================
    # HELPER METHODS (Node & Edge Generation)
    # ============================================================================
    def _get_portal_user_scope(self):
        """Get the recordset of partners a portal user is allowed to see."""
        if self.env.user.has_group('base.group_portal'):
            return self.env.user.partner_id
        # Internal users can see all customers by default, can be filtered later
        return self.env['res.partner'].search([('is_company', '=', True)])

    def _generate_partner_nodes(self, nodes, edges, partners):
        """Generate partner (customer) nodes for the diagram."""
        for partner in partners:
            nodes.append({
                'id': f'partner_{partner.id}',
                'label': partner.name,
                'title': _("Customer: %s") % partner.name,
                'group': 'partner',
                'level': 0,
                'shape': 'box',
            })
        return nodes, edges

    def _generate_department_nodes(self, nodes, edges, partners):
        """Generate department nodes for the diagram."""
        domain = [('partner_id', 'in', partners.ids)]
        if self.search_department_id:
            domain.append(('id', '=', self.search_department_id.id))

        departments = self.env['records.department'].search(domain)
        for dept in departments:
            nodes.append({
                'id': f'dept_{dept.id}',
                'label': dept.name,
                'title': _("Department: %s\nCustomer: %s") % (dept.name, dept.partner_id.name),
                'group': 'department',
                'level': 1,
                'shape': 'ellipse',
            })
            edges.append({
                'from': f'partner_{dept.partner_id.id}',
                'to': f'dept_{dept.id}',
            })
        return nodes, edges

    def _generate_user_nodes(self, nodes, edges, partners):
        """Generate user nodes for the diagram."""
        users = self.env['res.users'].search([('partner_id', 'in', partners.ids)])
        for user in users:
            # Find which department the user belongs to, if any
            department = self.env['records.department'].search([
                ('partner_id', '=', user.partner_id.id),
                # A more specific link might be needed here depending on your model structure
            ], limit=1)

            nodes.append({
                'id': f'user_{user.id}',
                'label': user.name,
                'title': _("User: %s") % user.name,
                'group': 'user',
                'level': 2,
                'shape': 'circle',
            })

            # Link user to a department or directly to the partner
            if department:
                edges.append({'from': f'dept_{department.id}', 'to': f'user_{user.id}'})
            else:
                edges.append({'from': f'partner_{user.partner_id.id}', 'to': f'user_{user.id}'})
        return nodes, edges

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_refresh_diagram(self):
        """Refresh the diagram data by re-running the compute methods."""
        self.ensure_one()
        self.invalidate_recordset(['diagram_data', 'diagram_stats'])
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_export_diagram_data(self):
        """Export diagram data as a JSON file for external use."""
        self.ensure_one()
        if not self.diagram_data:
            raise UserError(_("No diagram data to export."))

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/customer.portal.diagram/{self.id}/diagram_data?download=true',
            'target': 'self',
        }
