# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import Dict
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RecordsManagementInstaller(models.TransientModel):
    """Transient model for records management installation helper."""
    _name = 'records.management.installer'
    _description = 'Records Management Installation Helper'
    _rec_name = 'name'

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Installation Name', default='Records Management Setup', required=True)
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Installing User',
                             default=lambda self: self.env.user, required=True)
    
    # ==========================================
    # INSTALLATION OPTIONS
    # ==========================================
    install_demo_data = fields.Boolean(string='Install Demo Data', default=False,
                                      help='Install sample data for testing purposes')
    configure_sequences = fields.Boolean(string='Configure Sequences', default=True,
                                        help='Automatically configure number sequences')
    setup_default_locations = fields.Boolean(string='Setup Default Locations', default=True,
                                            help='Create default storage locations')
    install_barcode_scanner = fields.Boolean(string='Enable Barcode Scanning', default=True,
                                            help='Configure barcode scanning capabilities')
    
    # ==========================================
    # MODULE DEPENDENCIES
    # ==========================================
    stock_installed = fields.Boolean(string='Stock Module', compute='_compute_module_status', store=True)
    account_installed = fields.Boolean(string='Accounting Module', compute='_compute_module_status', store=True)
    sale_installed = fields.Boolean(string='Sales Module', compute='_compute_module_status', store=True)
    pos_installed = fields.Boolean(string='Point of Sale Module', compute='_compute_module_status', store=True)
    
    # ==========================================
    # STATUS FIELDS
    # ==========================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('checking', 'Checking Dependencies'),
        ('installing', 'Installing'),
        ('configuring', 'Configuring'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], string='Installation Status', default='draft', required=True)
    
    installation_date = fields.Datetime(string='Installation Date', default=fields.Datetime.now)
    completion_date = fields.Datetime(string='Completion Date')
    
    # ==========================================
    # PROGRESS TRACKING
    # ==========================================
    progress_percentage = fields.Float(string='Progress %', default=0.0)
    current_step = fields.Char(string='Current Step', default='Ready to start')
    error_message = fields.Text(string='Error Message')
    
    # ==========================================
    # CONFIGURATION OPTIONS
    # ==========================================
    default_retention_days = fields.Integer(string='Default Retention (Days)', default=2555,  # ~7 years
                                           help='Default document retention period in days')
    enable_naid_compliance = fields.Boolean(string='Enable NAID Compliance', default=True,
                                           help='Enable NAID AAA compliance features')
    setup_portal_access = fields.Boolean(string='Setup Customer Portal', default=True,
                                        help='Configure customer portal access')

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends()
    def _compute_module_status(self):
        """Check status of required modules"""
        for record in self:
            modules = ['stock', 'account', 'sale', 'point_of_sale']
            for module_name in modules:
                module = self.env['ir.module.module'].search([
                    ('name', '=', module_name),
                    ('state', '=', 'installed')
                ], limit=1)
                setattr(record, f'{module_name}_installed', bool(module))

    @api.model
    def check_dependencies(self) -> bool:
        """
        Check if required modules are installed before installing
        records_management.
        """
        required_modules = ['stock', 'account', 'sale', 'point_of_sale']
        for module_name in required_modules:
            module = self.env['ir.module.module'].search([
                ('name', '=', module_name),
                ('state', '=', 'installed')
            ])
            if not module:
                raise UserError(_(
                    f'The {module_name.capitalize()} module must be '
                    'installed before installing Records Management.'
                ))
        return True

    def install_required_modules(self) -> Dict:
        """Install required modules automatically."""
        self.write({'state': 'installing', 'current_step': 'Installing dependencies'})
        
        required_modules = ['stock', 'account', 'sale', 'point_of_sale']
        for module_name in required_modules:
            module = self.env['ir.module.module'].search([
                ('name', '=', module_name),
                ('state', 'in', ['uninstalled', 'to install'])
            ])
            if module:
                module.button_immediate_install()
                
        self.write({'progress_percentage': 25.0, 'current_step': 'Dependencies installed'})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    # ==========================================
    # INSTALLATION WORKFLOW
    # ==========================================
    def action_start_installation(self):
        """Start the installation process"""
        self.ensure_one()
        try:
            self.write({'state': 'checking', 'current_step': 'Checking dependencies'})
            
            # Check dependencies
            self.check_dependencies()
            self.write({'progress_percentage': 10.0})
            
            # Configure sequences if requested
            if self.configure_sequences:
                self._setup_sequences()
                self.write({'progress_percentage': 40.0, 'current_step': 'Sequences configured'})
            
            # Setup default locations if requested
            if self.setup_default_locations:
                self._setup_default_locations()
                self.write({'progress_percentage': 60.0, 'current_step': 'Default locations created'})
            
            # Install demo data if requested
            if self.install_demo_data:
                self._install_demo_data()
                self.write({'progress_percentage': 80.0, 'current_step': 'Demo data installed'})
            
            # Final configuration
            self._final_configuration()
            self.write({
                'state': 'completed',
                'progress_percentage': 100.0,
                'current_step': 'Installation completed',
                'completion_date': fields.Datetime.now()
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Installation Complete'),
                    'message': _('Records Management has been successfully installed and configured.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            self.write({
                'state': 'failed',
                'error_message': str(e),
                'current_step': 'Installation failed'
            })
            raise UserError(_('Installation failed: %s') % str(e))

    def _setup_sequences(self):
        """Setup number sequences for various records"""
        sequences = [
            ('records.container', 'Container Number', 'CONT'),
            ('records.billing', 'Billing Reference', 'BILL'),
            ('pickup.request', 'Pickup Request', 'PICK'),
            ('shredding.service', 'Shredding Service', 'SHRED'),
        ]
        
        for model, name, prefix in sequences:
            existing = self.env['ir.sequence'].search([('code', '=', model)], limit=1)
            if not existing:
                self.env['ir.sequence'].create({
                    'name': name,
                    'code': model,
                    'prefix': f'{prefix}%(y)s%(month)02d',
                    'padding': 4,
                    'number_increment': 1,
                    'number_next': 1,
                })

    def _setup_default_locations(self):
        """Create default storage locations"""
        default_locations = [
            ('Main Warehouse', 'warehouse'),
            ('Storage Room A', 'room'),
            ('Storage Room B', 'room'),
            ('Archive Section', 'aisle'),
        ]
        
        for name, location_type in default_locations:
            existing = self.env['records.location'].search([('name', '=', name)], limit=1)
            if not existing:
                self.env['records.location'].create({
                    'name': name,
                    'location_type': location_type,
                    'max_capacity': 1000 if location_type == 'warehouse' else 500,
                    'access_level': 'restricted',
                    'company_id': self.company_id.id,
                })

    def _install_demo_data(self):
        """Install demo data for testing"""
        # Create sample customer
        customer = self.env['res.partner'].create({
            'name': 'Demo Records Customer',
            'is_company': True,
            'email': 'demo@example.com',
        })
        
        # Create sample department
        self.env['records.department'].create({
            'name': 'Demo Department',
            'customer_id': customer.id,
            'description': 'Sample department for testing',
        })

    def _final_configuration(self):
        """Perform final configuration steps"""
        # Set up default retention policy if requested
        if self.default_retention_days:
            existing_policy = self.env['records.retention.policy'].search([
                ('name', '=', 'Default Retention Policy')
            ], limit=1)
            if not existing_policy:
                self.env['records.retention.policy'].create({
                    'name': 'Default Retention Policy',
                    'retention_period_days': self.default_retention_days,
                    'description': 'Default document retention policy',
                })

    # ==========================================
    # UTILITY ACTIONS
    # ==========================================
    def action_reset_installation(self):
        """Reset installation to start over"""
        self.write({
            'state': 'draft',
            'progress_percentage': 0.0,
            'current_step': 'Ready to start',
            'error_message': False,
            'completion_date': False,
        })

    def action_view_logs(self):
        """View installation logs"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Installation Logs',
            'res_model': 'ir.logging',
            'view_mode': 'tree,form',
            'domain': [('name', 'like', 'records_management')],
        }
