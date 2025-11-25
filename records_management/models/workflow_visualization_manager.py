# -*- coding: utf-8 -*-
"""
Workflow Visualization Manager

This model manages workflow visualizations, process diagrams, and workflow analytics
for the Records Management module. It provides tools for visualizing business processes,
workflow states, and system interactions.
"""

from datetime import datetime, timedelta
import json
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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

    def action_generate_process_flow_diagram(self):
        """Generate and store a process flow diagram for the current record.

        Must be parameterless to be callable from a form button.
        """
        self.ensure_one()
        try:
            model_name = self.target_model_id.model if self.target_model_id else None
            if not model_name:
                raise UserError(_("Please select a Target Model before generating the diagram."))
            data = self._generate_process_flow(model_name)
            # store JSON text into diagram_data and update timestamp
            self.write({
                'diagram_data': json.dumps(data),
                'last_generated': fields.Datetime.now(),
            })
            return True
        except Exception as e:
            _logger.error("Error generating process flow diagram: %s", str(e), exc_info=True)
            raise

    def _generate_process_flow(self, model_name):
        """Internal method to generate process flow"""
        self.ensure_one()
        model = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
        if not model:
            raise UserError(_("Model %s not found") % model_name)

        # Get workflow states and transitions
        states = []
        transitions = []

        # For records.container model, define specific workflow
        if model_name == 'records.container':
            states = [
                {'id': 'draft', 'name': 'Draft', 'color': '#ffcccc'},
                {'id': 'active', 'name': 'Active/Indexed', 'color': '#cce5ff'},
                {'id': 'pending_pickup', 'name': 'Pending Pickup', 'color': '#fff3cd'},
                {'id': 'in_storage', 'name': 'In Storage', 'color': '#ccffcc'},
                {'id': 'in_transit', 'name': 'In Transit', 'color': '#ffffcc'},
                {'id': 'retrieved', 'name': 'Retrieved', 'color': '#ffcc99'},
                {'id': 'pending_destruction', 'name': 'Pending Destruction', 'color': '#f8d7da'},
                {'id': 'destroyed', 'name': 'Destroyed', 'color': '#ff9999'},
            ]
            transitions = [
                {'from': 'draft', 'to': 'active', 'label': 'Activate/Index'},
                {'from': 'active', 'to': 'pending_pickup', 'label': 'Request Pickup'},
                {'from': 'pending_pickup', 'to': 'in_storage', 'label': 'Complete Pickup'},
                {'from': 'in_storage', 'to': 'in_transit', 'label': 'Retrieve'},
                {'from': 'in_transit', 'to': 'retrieved', 'label': 'Deliver'},
                {'from': 'retrieved', 'to': 'pending_destruction', 'label': 'Schedule Destruction'},
                {'from': 'pending_destruction', 'to': 'destroyed', 'label': 'Destroy'},
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
        _logger.info("Generated workflow analytics for model %s", model_name)

        return analytics

    @api.model
    def action_create_default_visualizations(self):
        """
        Create default workflow visualizations for common models.
        """
        self.ensure_one()
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
                "target_model_id": self.env.ref("records_management.model_records_document").id,
            },
            {
                "name": "Pickup Request Process",
                "description": "Customer pickup request processing workflow",
                "visualization_type": "user_journey",
                "target_model_id": self.env.ref("records_management.model_pickup_request").id,
            },
        ]

        created_visualizations = []
        for viz_data in default_visualizations:
            try:
                visualization = self.create(viz_data)
                created_visualizations.append(visualization)
            except Exception as e:
                _logger.error(
                    "Error creating default visualization %s: %s",
                    viz_data['name'],
                    str(e),
                    exc_info=True
                )

        return created_visualizations
