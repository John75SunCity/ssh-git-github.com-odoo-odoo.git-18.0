# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class MobileBinKeyWizard(models.TransientModel):
    """Mobile-friendly wizard for technicians to manage bin keys in the field"""
    _name = 'mobile.bin.key.wizard'
    _description = 'Mobile Bin Key Management Wizard'
    
    # Wizard type
    action_type = fields.Selection([
        ('issue_new', 'Issue New Key'),
        ('update_existing', 'Update Existing Contact'),
        ('create_unlock_service', 'Create Unlock Service'),
        ('quick_lookup', 'Quick Key Lookup')
    ], string='Action', required=True, default='issue_new')
    
    # Customer/Contact Information
    customer_company_id = fields.Many2one(
        'res.partner',
        string='Customer Company',
        domain=[('is_company', '=', True)],
        help="Select the customer company"
    )
    
    contact_id = fields.Many2one(
        'res.partner',
        string='Existing Contact',
        domain="[('parent_id', '=', customer_company_id), ('is_company', '=', False)]",
        help="Select existing contact to update"
    )
    
    # New contact creation fields
    create_new_contact = fields.Boolean(
        string='Create New Contact',
        default=True,
        help="Create a new contact for key assignment"
    )
    
    contact_name = fields.Char(
        string='Contact Name',
        help="Name of the person receiving the key"
    )
    
    contact_email = fields.Char(
        string='Email',
        help="Contact email address"
    )
    
    contact_phone = fields.Char(
        string='Phone',
        help="Contact phone number"
    )
    
    contact_mobile = fields.Char(
        string='Mobile',
        help="Contact mobile number"
    )
    
    contact_title = fields.Char(
        string='Job Title',
        help="Contact's job title or position"
    )
    
    # Key assignment fields
    issue_location = fields.Char(
        string='Issue Location',
        help="Where the key is being issued (e.g., loading dock, main office)"
    )
    
    bin_locations = fields.Text(
        string='Bin Locations',
        help="List the specific locations of bins this key provides access to"
    )
    
    emergency_contact = fields.Boolean(
        string='Emergency Contact',
        default=False,
        help="This contact can be reached for emergency bin access"
    )
    
    key_notes = fields.Text(
        string='Key Notes',
        help="Additional notes about this key assignment"
    )
    
    # Unlock service fields (when action_type = 'create_unlock_service')
    unlock_reason = fields.Selection([
        ('wrong_item', 'Wrong Item Deposited'),
        ('retrieve_item', 'Need to Retrieve Item'),
        ('maintenance', 'Bin Maintenance'),
        ('emergency', 'Emergency Access'),
        ('other', 'Other')
    ], string='Unlock Reason')
    
    unlock_reason_description = fields.Text(
        string='Reason Description',
        help="Detailed description of why unlock was needed"
    )
    
    unlock_bin_location = fields.Char(
        string='Bin Location',
        help="Specific location of the bin that was unlocked"
    )
    
    items_retrieved = fields.Text(
        string='Items Retrieved',
        help="Description of items retrieved from the bin"
    )
    
    unlock_charge = fields.Float(
        string='Charge Amount',
        default=25.00,
        help="Amount to charge for the unlock service"
    )
    
    billable = fields.Boolean(
        string='Billable',
        default=True,
        help="Whether this service should be billed"
    )
    
    # Lookup results (when action_type = 'quick_lookup')
    key_lookup_results = fields.Html(
        string='Key Holders',
        readonly=True,
        help="Display of key holders for the selected company"
    )
    
    # Service photos
    photo_ids = fields.Many2many(
        'ir.attachment',
        string='Photos',
        help="Photos taken during the service"
    )
    
    service_notes = fields.Text(
        string='Service Notes',
        help="Additional notes about the service"
    )
    
    # Computed fields for dynamic UI
    show_contact_creation = fields.Boolean(
        compute='_compute_show_sections',
        help="Show contact creation fields"
    )
    
    show_key_assignment = fields.Boolean(
        compute='_compute_show_sections',
        help="Show key assignment fields"
    )
    
    show_unlock_service = fields.Boolean(
        compute='_compute_show_sections',
        help="Show unlock service fields"
    )
    
    show_lookup_results = fields.Boolean(
        compute='_compute_show_sections',
        help="Show lookup results"
    )
    
    @api.depends('action_type', 'create_new_contact')
    def _compute_show_sections(self):
        """Compute which sections to show based on action type"""
        for wizard in self:
            wizard.show_contact_creation = (
                wizard.action_type in ['issue_new', 'update_existing'] and 
                wizard.create_new_contact
            )
            wizard.show_key_assignment = wizard.action_type in ['issue_new', 'update_existing']
            wizard.show_unlock_service = wizard.action_type == 'create_unlock_service'
            wizard.show_lookup_results = wizard.action_type == 'quick_lookup'
    
    @api.onchange('customer_company_id', 'action_type')
    def _onchange_company_lookup(self):
        """Update lookup results when company changes"""
        if self.action_type == 'quick_lookup' and self.customer_company_id:
            self._update_lookup_results()
    
    def _update_lookup_results(self):
        """Update the key lookup results HTML"""
        if not self.customer_company_id:
            self.key_lookup_results = ""
            return
        
        # Find all contacts with keys in this company
        key_holders = self.env['res.partner'].search([
            ('parent_id', '=', self.customer_company_id.id),
            ('has_bin_key', '=', True)
        ])
        
        if not key_holders:
            self.key_lookup_results = "<p><strong>No key holders found for this company.</strong></p>"
            return
        
        # Build HTML table
        html = """
        <table class="table table-sm">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Title</th>
                    <th>Phone</th>
                    <th>Key Issue Date</th>
                    <th>Emergency Contact</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for holder in key_holders:
            emergency_icon = "🚨" if holder.is_emergency_key_contact else ""
            html += f"""
                <tr>
                    <td><strong>🔑 {holder.name or ''}</strong></td>
                    <td>{holder.function or ''}</td>
                    <td>{holder.phone or holder.mobile or ''}</td>
                    <td>{holder.key_issue_date or ''}</td>
                    <td>{emergency_icon}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        <p><small><strong>🔑</strong> = Has Key | <strong>🚨</strong> = Emergency Contact</small></p>
        """
        
        self.key_lookup_results = html
    
    def action_execute(self):
        """Execute the selected action"""
        self.ensure_one()
        
        if self.action_type == 'issue_new':
            return self._execute_issue_new_key()
        elif self.action_type == 'update_existing':
            return self._execute_update_existing()
        elif self.action_type == 'create_unlock_service':
            return self._execute_create_unlock_service()
        elif self.action_type == 'quick_lookup':
            self._update_lookup_results()
            return {'type': 'ir.actions.do_nothing'}
    
    def _execute_issue_new_key(self):
        """Issue a new key to a contact"""
        if not self.customer_company_id:
            raise UserError(_('Please select a customer company.'))
        
        # Create or get contact
        if self.create_new_contact:
            if not self.contact_name:
                raise UserError(_('Please enter the contact name.'))
            
            contact = self.env['res.partner'].create({
                'name': self.contact_name,
                'parent_id': self.customer_company_id.id,
                'email': self.contact_email,
                'phone': self.contact_phone,
                'mobile': self.contact_mobile,
                'function': self.contact_title,
                'is_company': False,
            })
        else:
            if not self.contact_id:
                raise UserError(_('Please select an existing contact.'))
            contact = self.contact_id
        
        # Check if contact already has a key
        if contact.has_bin_key:
            raise UserError(_('This contact already has an active bin key.'))
        
        # Create key management record
        key_record = self.env['bin.key.management'].create({
            'partner_id': contact.id,
            'issue_location': self.issue_location,
            'bin_locations': self.bin_locations,
            'emergency_contact': self.emergency_contact,
            'notes': self.key_notes,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Key Issued Successfully'),
                'message': _('Key %s issued to %s at %s') % (
                    key_record.key_number, 
                    contact.name, 
                    self.issue_location or 'Customer Site'
                ),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _execute_update_existing(self):
        """Update an existing contact with key assignment"""
        if not self.contact_id:
            raise UserError(_('Please select a contact to update.'))
        
        if self.contact_id.has_bin_key:
            raise UserError(_('This contact already has an active bin key.'))
        
        # Create key management record
        key_record = self.env['bin.key.management'].create({
            'partner_id': self.contact_id.id,
            'issue_location': self.issue_location,
            'bin_locations': self.bin_locations,
            'emergency_contact': self.emergency_contact,
            'notes': self.key_notes,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Key Issued Successfully'),
                'message': _('Key %s issued to %s') % (key_record.key_number, self.contact_id.name),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _execute_create_unlock_service(self):
        """Create an unlock service record"""
        if not self.contact_id:
            raise UserError(_('Please select a contact for the unlock service.'))
        
        if not self.unlock_reason:
            raise UserError(_('Please select an unlock reason.'))
        
        if not self.unlock_bin_location:
            raise UserError(_('Please specify the bin location.'))
        
        # Create unlock service record
        unlock_service = self.env['bin.unlock.service'].create({
            'partner_id': self.contact_id.id,
            'key_holder_id': self.contact_id.active_bin_key_id.id if self.contact_id.has_bin_key else False,
            'bin_location': self.unlock_bin_location,
            'unlock_reason': self.unlock_reason,
            'reason_description': self.unlock_reason_description,
            'items_retrieved': self.items_retrieved,
            'charge_amount': self.unlock_charge,
            'billable': self.billable,
            'photo_ids': [(6, 0, self.photo_ids.ids)],
            'notes': self.service_notes,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Unlock Service Created'),
                'message': _('Service %s created for %s at %s') % (
                    unlock_service.service_number,
                    self.contact_id.name,
                    self.unlock_bin_location
                ),
                'type': 'success',
                'sticky': False,
            }
        }
