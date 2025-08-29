# -*- coding: utf-8 -*-
"""
Mobile FSM Integration Manager

This model provides mobile-optimized field service management integration for the Records Management module.
It includes mobile-specific features, offline capabilities, and enhanced mobile user experience.
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class MobileFsmIntegration(models.Model):
    """
    Mobile FSM Integration

    Model for managing mobile-optimized field service integration with
    offline capabilities and mobile-specific user experience enhancements.
    """

    _name = 'mobile.fsm.integration'
    _description = 'Mobile FSM Integration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Mobile Integration Name', required=True, tracking=True)
    description = fields.Text(string='Description', help='Description of this mobile integration')
    active = fields.Boolean(default=True, tracking=True)

    # Mobile settings
    enable_offline_mode = fields.Boolean(
        string='Offline Mode',
        default=True,
        help='Enable offline data synchronization'
    )

    enable_push_notifications = fields.Boolean(
        string='Push Notifications',
        default=True,
        help='Enable push notifications for mobile devices'
    )

    enable_biometric_auth = fields.Boolean(
        string='Biometric Authentication',
        default=False,
        help='Enable biometric authentication for mobile login'
    )

    # Mobile UI settings
    mobile_theme = fields.Selection([
        ('light', 'Light Theme'),
        ('dark', 'Dark Theme'),
        ('auto', 'Auto (System)'),
    ], string='Mobile Theme', default='auto')

    enable_voice_commands = fields.Boolean(
        string='Voice Commands',
        default=False,
        help='Enable voice command functionality'
    )

    # Data synchronization
    sync_interval = fields.Integer(
        string='Sync Interval (minutes)',
        default=15,
        help='Data synchronization interval in minutes'
    )

    max_offline_days = fields.Integer(
        string='Max Offline Days',
        default=7,
        help='Maximum days data can be stored offline'
    )

    # Mobile-specific features
    enable_qr_scanning = fields.Boolean(
        string='QR Code Scanning',
        default=True,
        help='Enable QR code scanning for containers and documents'
    )

    enable_barcode_scanning = fields.Boolean(
        string='Barcode Scanning',
        default=True,
        help='Enable barcode scanning functionality'
    )

    enable_photo_capture = fields.Boolean(
        string='Photo Capture',
        default=True,
        help='Enable photo capture for documentation'
    )

    # GPS and location
    enable_location_tracking = fields.Boolean(
        string='Location Tracking',
        default=True,
        help='Enable GPS location tracking'
    )

    location_update_interval = fields.Integer(
        string='Location Update Interval (minutes)',
        default=5,
        help='Location update interval in minutes'
    )

    # Mobile dashboard
    dashboard_widgets = fields.Many2many(
        'mobile.dashboard.widget',
        string='Dashboard Widgets',
        help='Widgets to display on mobile dashboard'
    )

    # Company and settings
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.model
    def get_mobile_dashboard_config(self, user_id=None):
        """
        Get mobile dashboard configuration for the specified user.
        """
        if not user_id:
            user_id = self.env.user.id

        config = self.search([('active', '=', True)], limit=1)
        if not config:
            config = self._create_default_config()

        dashboard_config = {
            'user_id': user_id,
            'theme': config.mobile_theme,
            'sync_interval': config.sync_interval,
            'enable_offline': config.enable_offline_mode,
            'enable_push': config.enable_push_notifications,
            'enable_voice': config.enable_voice_commands,
            'enable_qr': config.enable_qr_scanning,
            'enable_barcode': config.enable_barcode_scanning,
            'enable_photo': config.enable_photo_capture,
            'enable_gps': config.enable_location_tracking,
            'gps_interval': config.location_update_interval,
            'widgets': [w.name for w in config.dashboard_widgets],
        }

        return dashboard_config

    def _create_default_config(self):
        """Create default mobile configuration"""
        return self.create({
            'name': 'Default Mobile Configuration',
            'description': 'Default mobile FSM integration configuration',
            'enable_offline_mode': True,
            'enable_push_notifications': True,
            'mobile_theme': 'auto',
            'sync_interval': 15,
            'max_offline_days': 7,
            'enable_qr_scanning': True,
            'enable_barcode_scanning': True,
            'enable_photo_capture': True,
            'enable_location_tracking': True,
            'location_update_interval': 5,
        })

    @api.model
    def sync_mobile_data(self, user_id, device_id, data_payload):
        """
        Synchronize data from mobile device.
        """
        try:
            return self._process_mobile_sync(user_id, device_id, data_payload)
        except Exception as e:
            self.env['ir.logging'].create({
                'name': 'Mobile Sync Error',
                'type': 'server',
                'level': 'ERROR',
                'message': _('Error syncing mobile data: %s') % str(e),
                'path': 'mobile.fsm.integration',
                'func': 'sync_mobile_data',
            })
            raise

    def _process_mobile_sync(self, user_id, device_id, data_payload):
        """Process mobile data synchronization"""
        sync_results = {
            'device_id': device_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'processed_records': 0,
            'errors': [],
            'warnings': [],
        }

        # Process different types of data
        if 'tasks' in data_payload:
            task_results = self._sync_tasks(user_id, data_payload['tasks'])
            sync_results.update(task_results)

        if 'photos' in data_payload:
            photo_results = self._sync_photos(user_id, data_payload['photos'])
            sync_results['processed_records'] += photo_results.get('processed', 0)

        if 'locations' in data_payload:
            location_results = self._sync_locations(user_id, data_payload['locations'])
            sync_results['processed_records'] += location_results.get('processed', 0)

        # Log sync completion
        self.env['ir.logging'].create({
            'name': 'Mobile Data Sync',
            'type': 'server',
            'level': 'INFO',
            'message': _('Mobile data sync completed for user %s, device %s: %s records processed') % (
                user_id, device_id, sync_results['processed_records']),
            'path': 'mobile.fsm.integration',
            'func': '_process_mobile_sync',
        })

        return sync_results

    def _sync_tasks(self, user_id, tasks_data):
        """Sync task data from mobile device"""
        processed = 0
        errors = []

        for task_data in tasks_data:
            try:
                # Update task status or create new task
                if 'task_id' in task_data:
                    task = self.env['work.order.coordinator'].browse(task_data['task_id'])
                    if task.exists():
                        task.write({
                            'state': task_data.get('state', task.state),
                            'notes': task_data.get('notes', ''),
                        })
                        processed += 1
                else:
                    # Create new task
                    self.env['work.order.coordinator'].create({
                        'name': task_data.get('name', 'Mobile Task'),
                        'assigned_user_id': user_id,
                        'description': task_data.get('description', ''),
                        'scheduled_date': task_data.get('scheduled_date'),
                    })
                    processed += 1
            except Exception as e:
                errors.append(str(e))

        return {'processed': processed, 'errors': errors}

    def _sync_photos(self, user_id, photos_data):
        """Sync photo data from mobile device"""
        processed = 0

        for photo_data in photos_data:
            try:
                # Create photo record
                self.env['mobile.photo'].create({
                    'name': photo_data.get('name', 'Mobile Photo'),
                    'image': photo_data.get('image_data'),
                    'user_id': user_id,
                    'latitude': photo_data.get('latitude'),
                    'longitude': photo_data.get('longitude'),
                    'timestamp': photo_data.get('timestamp'),
                })
                processed += 1
            except Exception as e:
                # Log photo sync error
                self.env['ir.logging'].create({
                    'name': 'Photo Sync Error',
                    'type': 'server',
                    'level': 'ERROR',
                    'message': _('Error syncing photo: %s') % str(e),
                    'path': 'mobile.fsm.integration',
                    'func': '_sync_photos',
                })

        return {'processed': processed}

    def _sync_locations(self, user_id, locations_data):
        """Sync location data from mobile device"""
        processed = 0

        for location_data in locations_data:
            try:
                # Log location update (could create location tracking record)
                self.env['ir.logging'].create({
                    'name': 'Mobile Location Update',
                    'type': 'server',
                    'level': 'INFO',
                    'message': _('Location update from user %s: %s, %s') % (
                        user_id, location_data.get('latitude'), location_data.get('longitude')),
                    'path': 'mobile.fsm.integration',
                    'func': '_sync_locations',
                })
                processed += 1
            except Exception as e:
                # Log location sync error
                self.env['ir.logging'].create({
                    'name': 'Location Sync Error',
                    'type': 'server',
                    'level': 'ERROR',
                    'message': _('Error syncing location: %s') % str(e),
                    'path': 'mobile.fsm.integration',
                    'func': '_sync_locations',
                })

        return {'processed': processed}

    @api.model
    def get_mobile_quick_actions(self, user_id=None):
        """
        Get quick actions available for mobile interface.
        """
        if not user_id:
            user_id = self.env.user.id

        quick_actions = [
            {
                'id': 'scan_qr',
                'name': 'Scan QR Code',
                'icon': 'qr_code_scanner',
                'action': 'scan_qr',
                'enabled': True,
            },
            {
                'id': 'take_photo',
                'name': 'Take Photo',
                'icon': 'camera',
                'action': 'take_photo',
                'enabled': True,
            },
            {
                'id': 'check_in',
                'name': 'Check In',
                'icon': 'location_on',
                'action': 'check_in',
                'enabled': True,
            },
            {
                'id': 'emergency',
                'name': 'Emergency',
                'icon': 'warning',
                'action': 'emergency',
                'enabled': True,
            },
        ]

        return quick_actions

    @api.model
    def create_default_mobile_config(self):
        """
        Create default mobile configuration.
        """
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            config = self._create_default_config()

        # Log configuration creation
        self.env['ir.logging'].create({
            'name': 'Mobile Config Created',
            'type': 'server',
            'level': 'INFO',
            'message': _('Default mobile configuration created: %s') % config.name,
            'path': 'mobile.fsm.integration',
            'func': 'create_default_mobile_config',
        })

        return config
