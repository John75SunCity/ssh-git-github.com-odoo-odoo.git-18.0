# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MobileDashboardWidget(models.Model):
    """Mobile Dashboard Widget Model for FSM Integration

    This model defines individual dashboard widgets that can be displayed
    on mobile devices for field service management. Widgets provide
    real-time data visualization and quick access to key information.
    """
    _name = 'mobile.dashboard.widget'
    _description = 'Mobile Dashboard Widget'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # Basic Information
    name = fields.Char(
        string='Widget Name',
        required=True,
        tracking=True,
        help='Display name for the dashboard widget'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order in which widgets appear on the dashboard'
    )

    # Widget Configuration
    widget_type = fields.Selection([
        ('kpi', 'KPI Card'),
        ('chart', 'Chart'),
        ('map', 'Map View'),
        ('calendar', 'Calendar'),
        ('list', 'List View'),
        ('gauge', 'Gauge'),
        ('progress', 'Progress Bar'),
        ('counter', 'Counter'),
        ('status', 'Status Indicator'),
        ('notification', 'Notification Center'),
        ('weather', 'Weather Info'),
        ('location', 'Location Tracker'),
        ('timer', 'Timer/Countdown'),
        ('badge', 'Badge/Label'),
        ('button', 'Action Button'),
        ('form', 'Quick Form')
    ], string='Widget Type', required=True, default='kpi',
       help='Type of widget to display on the dashboard')

    category_id = fields.Many2one(
        comodel_name='mobile.dashboard.widget.category',
        string='Category',
        required=True,
        ondelete='cascade',
        help='Category this widget belongs to'
    )

    # Display Settings
    icon = fields.Char(
        string='Icon',
        help='FontAwesome icon class (e.g., fa-tachometer-alt)'
    )

    color = fields.Char(
        string='Color',
        default='#007bff',
        help='Hex color code for the widget'
    )

    size = fields.Selection([
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('xlarge', 'Extra Large')
    ], string='Size', default='medium',
       help='Size of the widget on the dashboard')

    # Data Source Configuration
    data_source = fields.Selection([
        ('model', 'Odoo Model'),
        ('query', 'Custom Query'),
        ('api', 'External API'),
        ('computed', 'Computed Field'),
        ('static', 'Static Value')
    ], string='Data Source', default='model',
       help='Source of data for this widget')

    model_name = fields.Char(
        string='Model Name',
        help='Odoo model to query for data (e.g., project.task)'
    )

    domain = fields.Char(
        string='Domain Filter',
        help='Domain expression to filter records (JSON format)'
    )

    field_name = fields.Char(
        string='Field Name',
        help='Field to display or aggregate'
    )

    aggregation = fields.Selection([
        ('count', 'Count'),
        ('sum', 'Sum'),
        ('avg', 'Average'),
        ('min', 'Minimum'),
        ('max', 'Maximum')
    ], string='Aggregation',
       help='How to aggregate the field values')

    # Widget Content
    title = fields.Char(
        string='Widget Title',
        help='Title displayed on the widget'
    )

    subtitle = fields.Char(
        string='Subtitle',
        help='Subtitle or description for the widget'
    )

    content = fields.Text(
        string='Content',
        help='Static content or template for dynamic content'
    )

    # Behavior Settings
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this widget is active and visible'
    )

    auto_refresh = fields.Boolean(
        string='Auto Refresh',
        default=False,
        help='Whether to automatically refresh widget data'
    )

    refresh_interval = fields.Integer(
        string='Refresh Interval (seconds)',
        default=300,
        help='How often to refresh data (in seconds)'
    )

    clickable = fields.Boolean(
        string='Clickable',
        default=True,
        help='Whether the widget can be clicked to perform actions'
    )

    action_type = fields.Selection([
        ('url', 'Open URL'),
        ('model', 'Open Model View'),
        ('wizard', 'Open Wizard'),
        ('report', 'Generate Report'),
        ('javascript', 'Run JavaScript')
    ], string='Action Type',
       help='Type of action to perform when widget is clicked')

    action_value = fields.Char(
        string='Action Value',
        help='Value for the action (URL, model name, etc.)'
    )

    # Permissions and Access
    user_groups = fields.Many2many(
        comodel_name='res.groups',
        relation='mobile_dashboard_widget_group_rel',
        column1='widget_id',
        column2='group_id',
        string='Allowed Groups',
        help='User groups that can see this widget'
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        help='Company this widget belongs to'
    )

    # Technical Fields
    technical_name = fields.Char(
        string='Technical Name',
        help='Unique technical identifier for the widget'
    )

    config_params = fields.Json(
        string='Configuration Parameters',
        help='Additional configuration parameters as JSON'
    )

    # Computed Fields
    @api.depends('name', 'category_id.name')
    def _compute_display_name(self):
        """Compute display name with category"""
        for record in self:
            if record.category_id:
                record.display_name = f"{record.category_id.name}: {record.name}"
            else:
                record.display_name = record.name

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    # Constraints
    @api.constrains('technical_name')
    def _check_technical_name_unique(self):
        """Ensure technical name is unique"""
        for record in self:
            if record.technical_name:
                existing = self.search([
                    ('technical_name', '=', record.technical_name),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        _("Technical name must be unique. '%s' already exists.") %
                        record.technical_name
                    )

    @api.constrains('model_name', 'field_name')
    def _check_model_field_exists(self):
        """Validate that model and field exist"""
        for record in self:
            if record.model_name and record.field_name:
                try:
                    model = self.env[record.model_name]
                    if record.field_name not in model._fields:
                        raise ValidationError(
                            _("Field '%s' does not exist in model '%s'.") %
                            (record.field_name, record.model_name)
                        )
                except KeyError:
                    raise ValidationError(
                        _("Model '%s' does not exist.") % record.model_name
                    )

    # Methods
    @api.model
    def get_widget_data(self, widget_id):
        """Get data for a specific widget with dynamic content"""
        widget = self.browse(widget_id)
        if not widget:
            return {}

        try:
            data = {
                'id': widget.id,
                'name': widget.name,
                'type': widget.widget_type,
                'title': widget.title or widget.name,
                'subtitle': widget.subtitle,
                'icon': widget.icon,
                'color': widget.color,
                'size': widget.size,
                'data': {},
                'last_updated': fields.Datetime.now(),
            }

            # Fetch dynamic data based on widget configuration
            if widget.data_source == 'model' and widget.model_name:
                data['data'] = self._get_model_data(widget)
            elif widget.data_source == 'static':
                data['data'] = {'value': widget.content or 'No data'}
            elif widget.data_source == 'computed':
                data['data'] = self._get_computed_data(widget)

            return data

        except Exception as e:
            return {
                'id': widget.id,
                'name': widget.name,
                'type': widget.widget_type,
                'title': widget.title or widget.name,
                'error': str(e),
                'data': {'value': 'Error loading data'}
            }

    def _get_model_data(self, widget):
        """Get data from Odoo model"""
        try:
            if not widget.model_name:
                return {'value': 'No model specified'}

            # Build domain
            domain = []
            if widget.domain:
                try:
                    # Parse domain string to list
                    import ast
                    domain = ast.literal_eval(widget.domain)
                except (ValueError, SyntaxError):
                    # If domain parsing fails, use empty domain
                    domain = []

            # Get records
            model = self.env[widget.model_name]
            records = model.search(domain)

            # Apply aggregation if specified
            if widget.aggregation and widget.field_name:
                if widget.aggregation == 'count':
                    value = len(records)
                elif widget.aggregation == 'sum':
                    values = [getattr(rec, widget.field_name, 0) for rec in records if hasattr(rec, widget.field_name)]
                    value = sum(values)
                elif widget.aggregation == 'avg':
                    values = [getattr(rec, widget.field_name, 0) for rec in records if hasattr(rec, widget.field_name)]
                    value = sum(values) / len(values) if values else 0
                elif widget.aggregation == 'min':
                    values = [getattr(rec, widget.field_name, 0) for rec in records if hasattr(rec, widget.field_name)]
                    value = min(values) if values else 0
                elif widget.aggregation == 'max':
                    values = [getattr(rec, widget.field_name, 0) for rec in records if hasattr(rec, widget.field_name)]
                    value = max(values) if values else 0
                else:
                    value = len(records)
            else:
                value = len(records)

            return {
                'value': value,
                'count': len(records),
                'model': widget.model_name,
                'field': widget.field_name,
                'aggregation': widget.aggregation
            }

        except Exception as e:
            return {'value': f'Error: {str(e)}', 'error': True}

    def _get_computed_data(self, widget):
        """Get computed data based on widget configuration"""
        try:
            # This is a placeholder for custom computed data
            # In a real implementation, you would add specific logic here
            return {
                'value': 'Computed data not implemented',
                'type': 'computed'
            }
        except Exception as e:
            return {'value': f'Error: {str(e)}', 'error': True}

    def get_available_widgets(self):
        """Get all available widgets for current user"""
        user = self.env.user
        domain = [('is_active', '=', True)]

        # Filter by user groups if specified
        if self.env.user.id != 1:  # Not superuser
            domain.append('|')
            domain.append(('user_groups', '=', False))  # No group restriction
            domain.append(('user_groups', 'in', user.groups_id.ids))

        return self.search(domain)

    @api.model
    def _ensure_default_category(self):
        """Ensure the default operations category exists"""
        category_model = self.env['mobile.dashboard.widget.category']

        # Check if default category exists
        default_category = category_model.search([
            ('technical_name', '=', 'operations')
        ], limit=1)

        if not default_category:
            # Create default category
            default_category = category_model.create({
                'name': 'Operations',
                'technical_name': 'operations',
                'description': 'Default category for operational dashboard widgets',
                'icon': 'fa-cogs',
                'is_active': True,
                'sort_order': 10
            })

        # Set the XML ID reference for the default widgets
        if not self.env.ref('records_management.mobile_dashboard_widget_category_operations', raise_if_not_found=False):
            # Create XML ID reference
            self.env['ir.model.data'].create({
                'name': 'mobile_dashboard_widget_category_operations',
                'model': 'mobile.dashboard.widget.category',
                'module': 'records_management',
                'res_id': default_category.id,
                'noupdate': True
            })

        return default_category

    @api.model
    def create_default_widgets(self):
        """Create default dashboard widgets using available models"""
        # Ensure default category exists
        default_category = self._ensure_default_category()

        default_widgets = [
            {
                'name': 'Active Records',
                'widget_type': 'kpi',
                'category_id': default_category.id,
                'icon': 'fa-file-text',
                'color': '#28a745',
                'model_name': 'records.document',
                'domain': "[('active', '=', True)]",
                'aggregation': 'count',
                'title': 'Active Records',
                'action_type': 'model',
                'action_value': 'records.document',
                'technical_name': 'active_records'
            },
            {
                'name': 'Pending Requests',
                'widget_type': 'counter',
                'category_id': default_category.id,
                'icon': 'fa-clock',
                'color': '#ffc107',
                'model_name': 'records.request',
                'domain': "[('state', 'in', ['draft', 'submitted'])]",
                'aggregation': 'count',
                'title': 'Pending Requests',
                'action_type': 'model',
                'action_value': 'records.request',
                'technical_name': 'pending_requests'
            },
            {
                'name': 'Containers Today',
                'widget_type': 'kpi',
                'category_id': default_category.id,
                'icon': 'fa-box',
                'color': '#007bff',
                'model_name': 'records.container',
                'domain': "[('create_date', '>=', (context_today()).strftime('%Y-%m-%d'))]",
                'aggregation': 'count',
                'title': 'Containers Today',
                'action_type': 'model',
                'action_value': 'records.container',
                'technical_name': 'containers_today'
            },
            {
                'name': 'Storage Locations',
                'widget_type': 'status',
                'category_id': default_category.id,
                'icon': 'fa-map-marker',
                'color': '#dc3545',
                'model_name': 'records.location',
                'domain': "[('active', '=', True)]",
                'aggregation': 'count',
                'title': 'Storage Locations',
                'action_type': 'model',
                'action_value': 'records.location',
                'technical_name': 'storage_locations'
            },
            {
                'name': 'Quick Actions',
                'widget_type': 'button',
                'category_id': default_category.id,
                'icon': 'fa-plus',
                'color': '#ffc107',
                'title': 'Quick Actions',
                'technical_name': 'quick_actions'
            },
            {
                'name': 'System Alerts',
                'widget_type': 'notification',
                'category_id': default_category.id,
                'icon': 'fa-bell',
                'color': '#6c757d',
                'title': 'System Alerts',
                'auto_refresh': True,
                'refresh_interval': 60,
                'technical_name': 'system_alerts'
            },
            {
                'name': 'Time Tracker',
                'widget_type': 'timer',
                'category_id': default_category.id,
                'icon': 'fa-clock',
                'color': '#fd7e14',
                'title': 'Time Tracker',
                'technical_name': 'time_tracker'
            },
            {
                'name': 'Completed Tasks',
                'widget_type': 'counter',
                'category_id': default_category.id,
                'icon': 'fa-check-circle',
                'color': '#20c997',
                'model_name': 'records.request',
                'domain': "[('state', '=', 'done')]",
                'aggregation': 'count',
                'title': 'Completed Tasks',
                'technical_name': 'completed_tasks'
            },
            {
                'name': 'Overdue Items',
                'widget_type': 'kpi',
                'category_id': default_category.id,
                'icon': 'fa-exclamation-triangle',
                'color': '#dc3545',
                'model_name': 'records.request',
                'domain': "[('date_deadline', '<', (context_today()).strftime('%Y-%m-%d')), ('state', '!=', 'done')]",
                'aggregation': 'count',
                'title': 'Overdue Items',
                'action_type': 'model',
                'action_value': 'records.request',
                'technical_name': 'overdue_items'
            },
            {
                'name': 'Progress Status',
                'widget_type': 'progress',
                'category_id': default_category.id,
                'icon': 'fa-chart-line',
                'color': '#6f42c1',
                'title': 'Task Progress',
                'technical_name': 'progress_status'
            },
            {
                'name': 'Department Stats',
                'widget_type': 'chart',
                'category_id': default_category.id,
                'icon': 'fa-building',
                'color': '#17a2b8',
                'model_name': 'records.department',
                'domain': "[('active', '=', True)]",
                'aggregation': 'count',
                'title': 'Departments',
                'action_type': 'model',
                'action_value': 'records.department',
                'technical_name': 'department_stats'
            },
            {
                'name': 'Location Tracker',
                'widget_type': 'location',
                'category_id': default_category.id,
                'icon': 'fa-crosshairs',
                'color': '#007bff',
                'title': 'GPS Location',
                'technical_name': 'location_tracker'
            },
            {
                'name': 'Document Types',
                'widget_type': 'list',
                'category_id': default_category.id,
                'icon': 'fa-list',
                'color': '#28a745',
                'model_name': 'records.document.type',
                'domain': "[('active', '=', True)]",
                'aggregation': 'count',
                'title': 'Document Types',
                'action_type': 'model',
                'action_value': 'records.document.type',
                'technical_name': 'document_types'
            },
            {
                'name': 'System Maintenance',
                'widget_type': 'badge',
                'category_id': default_category.id,
                'icon': 'fa-tools',
                'color': '#ffc107',
                'title': 'System Maintenance',
                'technical_name': 'system_maintenance'
            },
            {
                'name': 'Weather Info',
                'widget_type': 'weather',
                'category_id': default_category.id,
                'icon': 'fa-cloud-sun',
                'color': '#17a2b8',
                'title': 'Weather',
                'technical_name': 'weather_info'
            },
            {
                'name': 'Quick Report',
                'widget_type': 'form',
                'category_id': default_category.id,
                'icon': 'fa-clipboard',
                'color': '#6c757d',
                'title': 'Quick Report',
                'technical_name': 'quick_report'
            }
        ]

        for widget_data in default_widgets:
            # Check if widget already exists
            existing = self.search([('technical_name', '=', widget_data['technical_name'])])
            if not existing:
                try:
                    self.create(widget_data)
                except Exception as e:
                    # Log error but continue with other widgets
                    _logger.warning("Failed to create widget %s: %s" % (widget_data['name'], str(e)))
                    continue

        return True

    # Override create to set technical name if not provided
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('technical_name') and vals.get('name'):
                vals['technical_name'] = vals['name'].lower().replace(' ', '_').replace("'", '')
        return super().create(vals_list)
