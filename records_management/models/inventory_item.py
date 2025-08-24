"""
Inventory Item Model

This model manages inventory items within the Records Management system.
It tracks product details, serial numbers, locations, status, acquisition dates,
and company association. Integrated with Odoo's mail and activity mixins for
chatter and activity tracking.
"""

from odoo import models, fields, api, _

class InventoryItem(models.Model):
    """
    Represents an inventory item in the Records Management system.

    Fields:
        name (Char): Unique item reference, auto-generated.
        product_id (Many2one): Linked product.
        serial_number (Char): Serial number of the item.
        location_id (Many2one): Storage location.
        status (Selection): Current status of the item.
        acquisition_date (Date): Date of acquisition.
        notes (Text): Additional notes.
        active (Boolean): Active flag.
        company_id (Many2one): Associated company.

    Methods:
        create(vals_list): Overrides create to auto-generate item reference.
            This method is decorated with @api.model_create_multi and expects a list of value dicts (vals_list).
    """

    _name = 'inventory.item'
    _description = 'Inventory Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Item Reference', required=True, copy=False, readonly=True, default=_('New'))
    product_id = fields.Many2one('product.product', string='Product', required=True)
    serial_number = fields.Char(string='Serial Number')
    location_id = fields.Many2one('records.location', string='Location')
    status = fields.Selection([
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Maintenance'),
        ('retired', 'Retired'),
        ('lost', 'Lost')
    ], string='Status', default='available', tracking=True)
    acquisition_date = fields.Date(string='Acquisition Date')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    # Use a lambda for the default to ensure the current environment's company is set at record creation time.
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.model_create_multi
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('inventory.item') or _('New')
        return super().create(vals_list)
        return super().create(vals_list)
