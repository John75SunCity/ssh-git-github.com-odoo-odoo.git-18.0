# -*- coding: utf-8 -*-
"""
Workflow Visualization Manager

This model manages workflow visualizations, process diagrams, and workflow analytics
for the Records Management module. It                       'target_model_id': self.env.ref('records_management.model_pickup_request').id,         'target_model_id': self.env.ref('records_management.model_records_document').id,rovides tools for visualizing business processes,
workflow states, and system interactions.
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class WorkflowVisualizationManager(models.Model):
    """
    Workflow Visualization Manager

    Central model for managing workflow visualizations and process diagrams
    in the Records Management module.
    """

    _name = 'workflow.visualization.manager'
    _description = 'Workflow Visualization Manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Visualization Name', required=True, tracking=True)
    description = fields.Text(string='Description', help='Description of this workflow visualization')
    active = fields.Boolean(default=True)

    # Visualization settings
    visualization_type = fields.Selection([
        ('process_flow', 'Process Flow Diagram'),
        ('state_machine', 'State Machine'),
        ('data_flow', 'Data Flow Diagram'),
        ('user_journey', 'User Journey Map'),
        ('system_architecture', 'System Architecture'),
    ], string='Visualization Type', required=True, default='process_flow')

    target_model_id = fields.Many2one("ir.model", string="Target Model", help="Model to visualize workflow for")

    include_states = fields.Boolean(
        string='Include States',
        default=True,
        help='Include workflow states in visualization'
    )

    include_transitions = fields.Boolean(
        string='Include Transitions',
        default=True,
        help='Include state transitions in visualization'
    )

    include_users = fields.Boolean(
        string='Include Users',
        default=False,
        help='Include user roles in visualization'
    )

    # Generated visualization data
    diagram_data = fields.Text(
        string='Diagram Data',
        help='JSON data for diagram visualization'
    )

    last_generated = fields.Datetime(
        string='Last Generated',
        readonly=True
    )

    # Company and settings
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.model
    def generate_process_flow_diagram(self, model_name):
        """
        Generate a process flow diagram for the specified model.
        """
        try:
            return self._generate_process_flow(model_name)
        except Exception as e:
            self.env["ir.logging"].create(
                {
                    "name": "Process Flow Generation Error",
                    "type": "server",
                    "level": "ERROR",
                    "message": _("Error generating process flow diagram: %s", str(e)),
                    "path": "workflow.visualization.manager",
                    "func": "generate_process_flow_diagram",
                }
            )
            raise

    def _generate_process_flow(self, model_name):
        """Internal method to generate process flow diagram"""
        model = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
        if not model:
            raise UserError(_("Model %s not found", model_name))

        # Get workflow states and transitions
        states = []
        transitions = []

        # For records.container model, define specific workflow
        if model_name == 'records.container':
            states = [
                {'id': 'draft', 'name': 'Draft', 'color': '#ffcccc'},
                {'id': 'confirmed', 'name': 'Confirmed', 'color': '#cce5ff'},
                {'id': 'in_transit', 'name': 'In Transit', 'color': '#ffffcc'},
                {'id': 'received', 'name': 'Received', 'color': '#ccffcc'},
                {'id': 'stored', 'name': 'Stored', 'color': '#e6ccff'},
                {'id': 'retrieved', 'name': 'Retrieved', 'color': '#ffcc99'},
                {'id': 'destroyed', 'name': 'Destroyed', 'color': '#ff9999'},
            ]
            transitions = [
                {'from': 'draft', 'to': 'confirmed', 'label': 'Confirm'},
                {'from': 'confirmed', 'to': 'in_transit', 'label': 'Pickup'},
                {'from': 'in_transit', 'to': 'received', 'label': 'Receive'},
                {'from': 'received', 'to': 'stored', 'label': 'Store'},
                {'from': 'stored', 'to': 'retrieved', 'label': 'Retrieve'},
                {'from': 'retrieved', 'to': 'destroyed', 'label': 'Destroy'},
            ]

        diagram_data = {
            'model': model_name,
            'model_display_name': model.name,
            'states': states,
            'transitions': transitions,
            'generated_at': datetime.now().isoformat(),
        }

        return diagram_data

    @api.model
    def get_workflow_analytics(self, model_name, date_from=None, date_to=None):
        """
        Get workflow analytics for the specified model and date range.
        """
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()

        # Get workflow state changes
        analytics = {
            'model': model_name,
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'state_changes': [],
            'average_time_in_states': {},
            'bottlenecks': [],
        }

        # Log analytics generation
        self.env["ir.logging"].create(
            {
                "name": "Workflow Analytics",
                "type": "server",
                "level": "INFO",
                "message": _("Generated workflow analytics for model %s", model_name),
                "path": "workflow.visualization.manager",
                "func": "get_workflow_analytics",
            }
        )

        return analytics

    @api.model
    def create_default_visualizations(self):
        """
        Create default workflow visualizations for common models.
        """
        default_visualizations = [
            {
                "name": "Container Lifecycle Process",
                "description": "Complete lifecycle process for records containers",
                "visualization_type": "process_flow",
                "target_model_id": self.env.ref("records_management.model_records_container").id,
            },
            {
                "name": "Document Management Workflow",
                "description": "Document processing and management workflow",
                "visualization_type": "process_flow",
                "target_model": self.env.ref("records_management.model_records_document").id,
            },
            {
                "name": "Pickup Request Process",
                "description": "Customer pickup request processing workflow",
                "visualization_type": "user_journey",
                "target_model": self.env.ref("records_management.model_pickup_request").id,
            },
        ]

        created_visualizations = []
        for viz_data in default_visualizations:
            try:
                visualization = self.create(viz_data)
                created_visualizations.append(visualization)
            except Exception as e:
                self.env['ir.logging'].create({
                    'name': 'Default Visualization Creation Error',
                    'type': 'server',
                    'level': 'ERROR',
                    'message': _('Error creating default visualization %s: %s', viz_data['name'], str(e)),
                    'path': 'workflow.visualization.manager',
                    'func': 'create_default_visualizations',
                })

        return created_visualizations
