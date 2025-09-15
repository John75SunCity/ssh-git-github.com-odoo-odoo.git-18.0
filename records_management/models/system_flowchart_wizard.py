# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import json
import logging

_logger = logging.getLogger(__name__)


class SystemFlowchartWizard(models.TransientModel):
    """
    System Flowchart Wizard - Generates dynamic flowcharts showing the flow of records,
    containers, and processes through the Records Management system. Integrates with
    actual data to provide real-time visualization of system operations.
    """
    _name = 'system.flowchart.wizard'
    _description = 'System Flowchart Wizard'

    # Basic Information
    name = fields.Char(
        string='Flowchart Generation',
        default='System Flowchart Generator',
        readonly=True
    )

    # Flowchart Configuration
    flowchart_type = fields.Selection([
        ('document_lifecycle', 'Document Lifecycle'),
        ('container_flow', 'Container Flow'),
        ('billing_process', 'Billing Process'),
        ('retrieval_workflow', 'Retrieval Workflow'),
        ('shredding_process', 'Shredding Process'),
        ('audit_trail', 'Audit Trail'),
        ('customer_journey', 'Customer Journey'),
        ('work_order_flow', 'Work Order Flow'),
        ('system_overview', 'System Overview')
    ], string='Flowchart Type', required=True, default='system_overview')

    # Data Filters
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain=[('is_company', '=', True)],
        help='Filter data for specific customer'
    )

    department_id = fields.Many2one(
        'records.department',
        string='Department',
        help='Filter data for specific department'
    )

    location_id = fields.Many2one(
        'records.location',
        string='Location',
        help='Filter data for specific location'
    )

    date_from = fields.Date(
        string='From Date',
        default=lambda self: fields.Date.today().replace(day=1),
        help='Start date for data analysis'
    )

    date_to = fields.Date(
        string='To Date',
        default=fields.Date.today,
        help='End date for data analysis'
    )

    # Display Options
    include_statistics = fields.Boolean(
        string='Include Statistics',
        default=True,
        help='Include statistical data in flowchart nodes'
    )

    show_bottlenecks = fields.Boolean(
        string='Highlight Bottlenecks',
        default=True,
        help='Highlight process bottlenecks in red'
    )

    include_timing = fields.Boolean(
        string='Include Timing Data',
        default=True,
        help='Show average processing times'
    )

    detail_level = fields.Selection([
        ('high', 'High Detail'),
        ('medium', 'Medium Detail'),
        ('low', 'Low Detail')
    ], string='Detail Level', default='medium')

    # Real-time Data Analysis
    total_documents = fields.Integer(
        string='Total Documents',
        compute='_compute_data_statistics',
        help='Total documents in selected scope'
    )

    total_containers = fields.Integer(
        string='Total Containers',
        compute='_compute_data_statistics',
        help='Total containers in selected scope'
    )

    active_work_orders = fields.Integer(
        string='Active Work Orders',
        compute='_compute_data_statistics',
        help='Currently active work orders'
    )

    pending_retrievals = fields.Integer(
        string='Pending Retrievals',
        compute='_compute_data_statistics',
        help='Retrieval requests awaiting processing'
    )

    # Process Metrics
    avg_document_processing_time = fields.Float(
        string='Avg Document Processing (Days)',
        compute='_compute_process_metrics',
        help='Average time to process documents'
    )

    avg_retrieval_time = fields.Float(
        string='Avg Retrieval Time (Hours)',
        compute='_compute_process_metrics',
        help='Average time to complete retrievals'
    )

    container_utilization = fields.Float(
        string='Container Utilization (%)',
        compute='_compute_process_metrics',
        help='Average container capacity utilization'
    )

    # Bottleneck Analysis
    identified_bottlenecks = fields.Text(
        string='Identified Bottlenecks',
        compute='_compute_bottleneck_analysis',
        help='System bottlenecks identified from data'
    )

    efficiency_score = fields.Float(
        string='System Efficiency Score',
        compute='_compute_bottleneck_analysis',
        help='Overall system efficiency (0-100)'
    )

    # Generated Output
    flowchart_data = fields.Text(
        string='Flowchart Data',
        readonly=True,
        help='Generated flowchart data in JSON format'
    )

    flowchart_url = fields.Char(
        string='Flowchart URL',
        readonly=True,
        help='URL to view the generated flowchart'
    )

    @api.depends('customer_id', 'department_id', 'location_id', 'date_from', 'date_to')
    def _compute_data_statistics(self):
        """Compute real-time data statistics based on filters"""
        for wizard in self:
            # Build domain for filtering
            document_domain = wizard._build_data_domain('records.document')
            container_domain = wizard._build_data_domain('records.container')
            work_order_domain = wizard._build_data_domain('project.task')
            retrieval_domain = wizard._build_data_domain('container.retrieval')

            # Count documents
            wizard.total_documents = self.env['records.document'].search_count(document_domain)

            # Count containers
            wizard.total_containers = self.env['records.container'].search_count(container_domain)

            # Count active work orders
            work_order_domain.append(('stage_id.is_closed', '=', False))
            wizard.active_work_orders = self.env['project.task'].search_count(work_order_domain)

            # Count pending retrievals
            retrieval_domain.append(('state', 'in', ['requested', 'in_progress']))
            wizard.pending_retrievals = self.env['container.retrieval'].search_count(retrieval_domain)

    @api.depends('customer_id', 'department_id', 'date_from', 'date_to')
    def _compute_process_metrics(self):
        """Compute process performance metrics"""
        for wizard in self:
            # Calculate average document processing time
            document_domain = wizard._build_data_domain('records.document')
            documents = self.env['records.document'].search(document_domain)
            
            if documents:
                processing_times = []
                for doc in documents:
                    if doc.create_date and doc.storage_date:
                        delta = doc.storage_date.date() - doc.create_date.date()
                        processing_times.append(delta.days)
                
                wizard.avg_document_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            else:
                wizard.avg_document_processing_time = 0

            # Calculate average retrieval time
            retrieval_domain = wizard._build_data_domain('container.retrieval')
            retrieval_domain.append(('state', '=', 'completed'))
            retrievals = self.env['container.retrieval'].search(retrieval_domain)
            
            if retrievals:
                retrieval_times = []
                for retrieval in retrievals:
                    if retrieval.request_date and retrieval.completion_date:
                        delta = retrieval.completion_date - retrieval.request_date
                        retrieval_times.append(delta.total_seconds() / 3600)  # Convert to hours
                
                wizard.avg_retrieval_time = sum(retrieval_times) / len(retrieval_times) if retrieval_times else 0
            else:
                wizard.avg_retrieval_time = 0

            # Calculate container utilization
            container_domain = wizard._build_data_domain('records.container')
            containers = self.env['records.container'].search(container_domain)
            
            if containers:
                utilizations = []
                for container in containers:
                    if hasattr(container, 'fill_percentage') and container.capacity > 0:
                        utilizations.append(container.fill_percentage)
                
                wizard.container_utilization = sum(utilizations) / len(utilizations) if utilizations else 0
            else:
                wizard.container_utilization = 0

    @api.depends('avg_document_processing_time', 'avg_retrieval_time', 'container_utilization', 
                 'active_work_orders', 'pending_retrievals')
    def _compute_bottleneck_analysis(self):
        """Analyze system bottlenecks and efficiency"""
        for wizard in self:
            bottlenecks = []
            efficiency_factors = []

            # Document processing bottleneck
            if wizard.avg_document_processing_time > 5:  # More than 5 days
                bottlenecks.append(f"Document Processing: {wizard.avg_document_processing_time:.1f} days (target: <3 days)")
                efficiency_factors.append(max(0, 100 - (wizard.avg_document_processing_time - 3) * 10))
            else:
                efficiency_factors.append(100)

            # Retrieval time bottleneck
            if wizard.avg_retrieval_time > 24:  # More than 24 hours
                bottlenecks.append(f"Retrieval Processing: {wizard.avg_retrieval_time:.1f} hours (target: <12 hours)")
                efficiency_factors.append(max(0, 100 - (wizard.avg_retrieval_time - 12) * 2))
            else:
                efficiency_factors.append(100)

            # Container utilization
            if wizard.container_utilization < 70:  # Less than 70% utilization
                bottlenecks.append(f"Container Utilization: {wizard.container_utilization:.1f}% (target: >80%)")
                efficiency_factors.append(wizard.container_utilization)
            else:
                efficiency_factors.append(100)

            # Work order backlog
            if wizard.active_work_orders > 50:
                bottlenecks.append(f"Work Order Backlog: {wizard.active_work_orders} active orders")
                efficiency_factors.append(max(0, 100 - (wizard.active_work_orders - 20) * 2))
            else:
                efficiency_factors.append(100)

            # Pending retrievals
            if wizard.pending_retrievals > 20:
                bottlenecks.append(f"Retrieval Backlog: {wizard.pending_retrievals} pending requests")
                efficiency_factors.append(max(0, 100 - (wizard.pending_retrievals - 10) * 3))
            else:
                efficiency_factors.append(100)

            wizard.identified_bottlenecks = '\n'.join(f"• {bottleneck}" for bottleneck in bottlenecks) or "No significant bottlenecks identified"
            wizard.efficiency_score = sum(efficiency_factors) / len(efficiency_factors) if efficiency_factors else 0

    def _build_data_domain(self, model_name):
        """Build domain for data filtering"""
        domain = []

        # Customer filter
        if self.customer_id:
            if model_name in ['records.document', 'records.container']:
                domain.append(('partner_id', '=', self.customer_id.id))
            elif model_name == 'project.task':
                domain.append(('partner_id', '=', self.customer_id.id))

        # Department filter
        if self.department_id:
            if model_name in ['records.document', 'records.container']:
                domain.append(('department_id', '=', self.department_id.id))

        # Location filter
        if self.location_id:
            if model_name in ['records.container']:
                domain.append(('location_id', '=', self.location_id.id))

        # Date filters
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))

        return domain

    def action_generate_flowchart(self):
        """Generate the system flowchart"""
        self.ensure_one()

        if self.flowchart_type == 'document_lifecycle':
            flowchart_data = self._generate_document_lifecycle_flowchart()
        elif self.flowchart_type == 'container_flow':
            flowchart_data = self._generate_container_flow_flowchart()
        elif self.flowchart_type == 'billing_process':
            flowchart_data = self._generate_billing_process_flowchart()
        elif self.flowchart_type == 'retrieval_workflow':
            flowchart_data = self._generate_retrieval_workflow_flowchart()
        elif self.flowchart_type == 'shredding_process':
            flowchart_data = self._generate_shredding_process_flowchart()
        elif self.flowchart_type == 'audit_trail':
            flowchart_data = self._generate_audit_trail_flowchart()
        elif self.flowchart_type == 'customer_journey':
            flowchart_data = self._generate_customer_journey_flowchart()
        elif self.flowchart_type == 'work_order_flow':
            flowchart_data = self._generate_work_order_flow_flowchart()
        else:  # system_overview
            flowchart_data = self._generate_system_overview_flowchart()

        self.flowchart_data = json.dumps(flowchart_data, indent=2)
        self.flowchart_url = f"/records_management/flowchart/{self.id}"

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Flowchart Generated'),
                'message': _('System flowchart has been generated successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _generate_system_overview_flowchart(self):
        """Generate system overview flowchart with real data"""
        nodes = []
        edges = []

        # Customer node
        customer_stats = f"{self.total_documents} docs" if self.include_statistics else ""
        nodes.append({
            'id': 'customer',
            'label': f'Customer\n{customer_stats}',
            'type': 'start',
            'color': '#4CAF50'
        })

        # Document intake
        intake_stats = f"Avg: {self.avg_document_processing_time:.1f} days" if self.include_timing else ""
        nodes.append({
            'id': 'intake',
            'label': f'Document Intake\n{intake_stats}',
            'type': 'process',
            'color': '#2196F3'
        })

        # Storage
        storage_stats = f"{self.total_containers} containers" if self.include_statistics else ""
        nodes.append({
            'id': 'storage',
            'label': f'Storage\n{storage_stats}',
            'type': 'process',
            'color': '#FF9800'
        })

        # Retrieval
        retrieval_stats = f"{self.pending_retrievals} pending" if self.include_statistics else ""
        retrieval_color = '#F44336' if self.show_bottlenecks and self.pending_retrievals > 20 else '#9C27B0'
        nodes.append({
            'id': 'retrieval',
            'label': f'Retrieval\n{retrieval_stats}',
            'type': 'process',
            'color': retrieval_color
        })

        # Shredding
        nodes.append({
            'id': 'shredding',
            'label': 'Secure Shredding',
            'type': 'end',
            'color': '#607D8B'
        })

        # Billing
        nodes.append({
            'id': 'billing',
            'label': 'Billing',
            'type': 'process',
            'color': '#795548'
        })

        # Define edges
        edges = [
            {'from': 'customer', 'to': 'intake'},
            {'from': 'intake', 'to': 'storage'},
            {'from': 'storage', 'to': 'retrieval'},
            {'from': 'retrieval', 'to': 'customer'},
            {'from': 'storage', 'to': 'shredding'},
            {'from': 'intake', 'to': 'billing'},
            {'from': 'retrieval', 'to': 'billing'},
            {'from': 'shredding', 'to': 'billing'}
        ]

        return {
            'type': self.flowchart_type,
            'title': f'System Overview - Efficiency: {self.efficiency_score:.1f}%',
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'generated_date': fields.Datetime.now().isoformat(),
                'filters': {
                    'customer': self.customer_id.name if self.customer_id else 'All',
                    'department': self.department_id.name if self.department_id else 'All',
                    'date_range': f"{self.date_from} to {self.date_to}"
                },
                'statistics': {
                    'total_documents': self.total_documents,
                    'total_containers': self.total_containers,
                    'active_work_orders': self.active_work_orders,
                    'efficiency_score': self.efficiency_score
                }
            }
        }

    def _generate_document_lifecycle_flowchart(self):
        """Generate document lifecycle flowchart"""
        # Implementation would create detailed document lifecycle flow
        return self._generate_system_overview_flowchart()

    def _generate_container_flow_flowchart(self):
        """Generate container flow flowchart"""
        # Implementation would create container-specific flow
        return self._generate_system_overview_flowchart()

    def _generate_billing_process_flowchart(self):
        """Generate billing process flowchart"""
        # Implementation would create billing-specific flow
        return self._generate_system_overview_flowchart()

    def _generate_retrieval_workflow_flowchart(self):
        """Generate retrieval workflow flowchart"""
        # Implementation would create retrieval-specific flow
        return self._generate_system_overview_flowchart()

    def _generate_shredding_process_flowchart(self):
        """Generate shredding process flowchart"""
        # Implementation would create shredding-specific flow
        return self._generate_system_overview_flowchart()

    def _generate_audit_trail_flowchart(self):
        """Generate audit trail flowchart"""
        # Implementation would create audit trail flow
        return self._generate_system_overview_flowchart()

    def _generate_customer_journey_flowchart(self):
        """Generate customer journey flowchart"""
        # Implementation would create customer journey flow
        return self._generate_system_overview_flowchart()

    def _generate_work_order_flow_flowchart(self):
        """Generate work order flow flowchart"""
        # Implementation would create work order flow
        return self._generate_system_overview_flowchart()

    def action_view_flowchart(self):
        """Open flowchart in new window"""
        if not self.flowchart_data:
            raise ValidationError(_("Please generate the flowchart first"))

        return {
            'type': 'ir.actions.act_url',
            'url': self.flowchart_url,
            'target': 'new'
        }

    def action_export_flowchart(self):
        """Export flowchart data"""
        if not self.flowchart_data:
            raise ValidationError(_("Please generate the flowchart first"))

        # This would create a downloadable file
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Export Ready'),
                'message': _('Flowchart data ready for export'),
                'type': 'info',
                'sticky': False,
            }
        }
