# -*- coding: utf-8 -*-
"""
Enhanced Field Service Integration Manager

This model provides enhanced field service management integration for the Records Management module.
It works with or without the industry_fsm module and provides comprehensive FSM functionality.
"""

from datetime import datetime
from odoo import api, fields, models, _


class EnhancedFsmIntegration(models.Model):
    """
    Enhanced FSM Integration

    Model for managing enhanced field service integration with comprehensive
    functionality that works with or without the industry_fsm module.
    """

    _name = 'enhanced.fsm.integration'
    _description = 'Enhanced FSM Integration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Integration Name', required=True, tracking=True)
    description = fields.Text(string='Description', help='Description of this FSM integration')
    active = fields.Boolean(default=True, tracking=True)

    # Integration settings
    integration_type = fields.Selection([
        ('pickup_delivery', 'Pickup & Delivery'),
        ('maintenance_repair', 'Maintenance & Repair'),
        ('installation_setup', 'Installation & Setup'),
        ('audit_inspection', 'Audit & Inspection'),
        ('emergency_response', 'Emergency Response'),
    ], string='Integration Type', required=True, default='pickup_delivery')

    # Target models for integration
    target_pickup_requests = fields.Boolean(
        string='Pickup Requests',
        default=True,
        help='Integrate with pickup request workflows'
    )

    target_maintenance = fields.Boolean(
        string='Maintenance',
        default=True,
        help='Integrate with maintenance workflows'
    )

    target_containers = fields.Boolean(
        string='Containers',
        default=True,
        help='Integrate with container management'
    )

    # FSM Task management (works with or without industry_fsm)
    auto_create_tasks = fields.Boolean(
        string='Auto Create Tasks',
        default=True,
        help='Automatically create FSM tasks for work orders'
    )

    task_priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string='Default Task Priority', default='1')

    # Mobile integration
    enable_mobile_checkin = fields.Boolean(
        string='Mobile Check-in',
        default=True,
        help='Enable mobile check-in functionality'
    )

    enable_gps_tracking = fields.Boolean(
        string='GPS Tracking',
        default=False,
        help='Enable GPS tracking for field technicians'
    )

    # Mobile update interval (used in views)
    location_update_interval = fields.Integer(
        string='Location Update Interval (sec)',
        default=60,
        help='Time interval in seconds between technician GPS location updates'
    )

    # Notification settings
    enable_sms_notifications = fields.Boolean(
        string='SMS Notifications',
        default=True,
        help='Send SMS notifications for task updates'
    )

    enable_email_notifications = fields.Boolean(
        string='Email Notifications',
        default=True,
        help='Send email notifications for task updates'
    )

    # Company and settings
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.model
    def create_fsm_task_for_pickup(self, pickup_request):
        """
        Create an FSM task for a pickup request.
        Works with or without industry_fsm module.
        """
        try:
            return self._create_pickup_task(pickup_request)
        except Exception as e:
            self.env['ir.logging'].create({
                'name': 'FSM Task Creation Error',
                'type': 'server',
                'level': 'ERROR',
                'message': _("Error creating FSM task for pickup: %s") % str(e),
                'path': 'enhanced.fsm.integration',
                'func': 'create_fsm_task_for_pickup',
            })
            raise

    def _create_pickup_task(self, pickup_request):
        """Internal method to create pickup task"""
        # Check if industry_fsm is available
        fsm_available = self._check_fsm_availability()

        if fsm_available:
            # Use industry_fsm module
            return self._create_industry_fsm_task(pickup_request)
        else:
            # Use alternative implementation
            return self._create_alternative_fsm_task(pickup_request)

    def _check_fsm_availability(self):
        """Check if industry_fsm module is available"""
        try:
            self.env['fsm.task']
            return True
        except Exception:
            return False

    def _create_industry_fsm_task(self, pickup_request):
        """Create task using industry_fsm module"""
        task_data = {
            'name': _("Pickup Request: %s") % pickup_request.name,
            'description': _("Pickup request for customer: %s") % (pickup_request.partner_id.name or ''),
            'partner_id': pickup_request.partner_id.id,
            'scheduled_date_start': pickup_request.requested_date,
            'priority': self.task_priority,
            'user_id': pickup_request.assigned_user_id.id if pickup_request.assigned_user_id else False,
        }

        task = self.env['fsm.task'].create(task_data)

        # Log task creation
        self.env['ir.logging'].create({
            'name': 'FSM Task Created',
            'type': 'server',
            'level': 'INFO',
            'message': _("Created FSM task %s for pickup request %s") % (task.name, pickup_request.name),
            'path': 'enhanced.fsm.integration',
            'func': '_create_industry_fsm_task',
        })

        return task

    def _create_alternative_fsm_task(self, pickup_request):
        """Create alternative task implementation"""
        work_order_data = {
            'name': _("Pickup Task: %s") % pickup_request.name,
            'description': _("Pickup request for customer: %s") % (pickup_request.partner_id.name or ''),
            'partner_id': pickup_request.partner_id.id,
            'scheduled_date': pickup_request.requested_date,
            'priority': self.task_priority,
            'assigned_user_id': pickup_request.assigned_user_id.id if pickup_request.assigned_user_id else False,
            'work_order_type': 'pickup',
        }

        work_order = self.env['work.order.coordinator'].create(work_order_data)

        # Log alternative task creation
        self.env['ir.logging'].create({
            'name': 'Alternative FSM Task Created',
            'type': 'server',
            'level': 'INFO',
            'message': _("Created alternative work order %s for pickup request %s") % (work_order.name, pickup_request.name),
            'path': 'enhanced.fsm.integration',
            'func': '_create_alternative_fsm_task',
        })

        return work_order

    def create_default_integrations(self):
        """UI button: create a set of default FSM integrations.

        Returns an action to show the created integrations, or a notification if none were created.
        """
        self.ensure_one()
        created = self._create_default_integrations()
        created_ids = [rec.id for rec in created if rec]
        if created_ids:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Enhanced FSM Integrations'),
                'res_model': 'enhanced.fsm.integration',
                'view_mode': 'list,form',
                'domain': [('id', 'in', created_ids)],
                'target': 'current',
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('No New Integrations'),
                'message': _('Default integrations already exist or could not be created.'),
                'sticky': False,
                'type': 'warning',
            }
        }

    @api.model
    def get_mobile_dashboard_data(self, user_id=None):
        """
        Get dashboard data for mobile FSM interface.
        """
        if not user_id:
            user_id = self.env.user.id

        # Select user field depending on availability
        is_fsm = self._check_fsm_availability()
        user_field = 'user_id' if is_fsm else 'assigned_user_id'
        domain = [(user_field, '=', user_id)]

        if is_fsm:
            tasks = self.env['fsm.task'].search(domain + [('stage_id.fold', '=', False)])
        else:
            tasks = self.env['work.order.coordinator'].search(domain + [('state', 'not in', ['completed', 'cancelled'])])

        dashboard_data = {
            'user_id': user_id,
            'total_tasks': len(tasks),
            'pending_tasks': len(tasks.filtered(
                lambda t: (hasattr(t, 'stage_id') and t.stage_id and not getattr(t.stage_id, 'fold', True))
                or (hasattr(t, 'state') and t.state in ['draft', 'confirmed'])
            )),
            'completed_today': len(tasks.filtered(
                lambda t: (
                    (getattr(t, 'date_end', None) or getattr(t, 'date_done', None)) and
                    (getattr(t, 'date_end', None) or getattr(t, 'date_done', None)).date() == datetime.now().date()
                )
            )),
            'tasks': [],
        }

        for task in tasks[:10]:
            task_data = {
                'id': task.id,
                'name': task.name,
                'partner_name': task.partner_id.name if getattr(task, 'partner_id', False) else '',
                'scheduled_date': getattr(task, 'scheduled_date_start', getattr(task, 'scheduled_date', None)),
                'priority': getattr(task, 'priority', '1'),
                'state': (getattr(task, 'stage_id', False) and getattr(task.stage_id, 'name', '')) or getattr(task, 'state', ''),
            }
            dashboard_data['tasks'].append(task_data)

        return dashboard_data

    @api.model
    def update_task_location(self, task_id, latitude, longitude, user_id=None):
        """
        Update task location for GPS tracking.

        Security intent:
        - Persist logs only in technical logs (ir.logging), which are invisible to regular users.
        - Regular users cannot see or edit location logs.
        - Admins (base.group_system) can see full coordinates and details in responses and logs.
        """
        if not user_id:
            user_id = self.env.user.id

        # Prepare immutable log payload
        timestamp = datetime.now()
        is_admin = self.env.user.has_group('base.group_system')

        # Always log full coordinates in technical logs; only admins can browse them by default
        self.env['ir.logging'].sudo().create({
            'name': 'GPS Location Update',
            'type': 'server',
            'level': 'INFO',
            'message': _("GPS location updated for task %s: %s, %s") % (task_id, latitude, longitude),
            'path': 'enhanced.fsm.integration',
            'func': 'update_task_location',
        })

        # Do NOT create any user-visible business records for location logs
        # This ensures users cannot view or edit location history
        # Return minimal info to users; full details only to admins
        base_message = _("Location updated successfully")
        if is_admin:
            return {
                'status': 'success',
                'message': base_message,
                'data': {
                    'task_id': task_id,
                    'user_id': user_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    'timestamp': timestamp,
                },
            }
        return {'status': 'success', 'message': base_message}

    @api.model
    def _create_default_integrations(self):
        """
        Create default FSM integrations for common workflows.
        """
        default_integrations = [
            {
                'name': 'Pickup & Delivery Integration',
                'description': 'Automated FSM integration for pickup and delivery workflows',
                'integration_type': 'pickup_delivery',
                'target_pickup_requests': True,
                'target_containers': True,
                'auto_create_tasks': True,
                'enable_mobile_checkin': True,
                'enable_sms_notifications': True,
            },
            {
                'name': 'Maintenance Integration',
                'description': 'FSM integration for maintenance and repair workflows',
                'integration_type': 'maintenance_repair',
                'target_maintenance': True,
                'auto_create_tasks': True,
                'enable_mobile_checkin': True,
                'enable_gps_tracking': True,
            },
        ]

        created_integrations = []
        for integration_data in default_integrations:
            try:
                integration = self.create(integration_data)
                created_integrations.append(integration)
            except Exception as e:
                self.env['ir.logging'].create({
                    'name': 'Default Integration Creation Error',
                    'type': 'server',
                    'level': 'ERROR',
                    'message': _("Error creating default integration %s: %s") % (integration_data['name'], str(e)),
                    'path': 'enhanced.fsm.integration',
                    'func': '_create_default_integrations',
                })

        return created_integrations
