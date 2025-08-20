from odoo import models, fields, _
from odoo.exceptions import UserError

class FileRetrievalItem(models.Model):
    _name = 'file.retrieval.item'
    _description = 'File Retrieval Item'
    _inherit = ['retrieval.item.base']  # Now inherits from the new base model
    _rec_name = 'display_name'

    # File-specific fields
    requested_file_name = fields.Char(string='Requested File Name', required=True, tracking=True)
    container_id = fields.Many2one('records.container', string='Target Container', tracking=True)
    searched_container_ids = fields.Many2many(
        'records.container',
        'file_retrieval_item_searched_container_rel',
        'item_id', 'container_id',
        string='Searched Containers'
    )
    discovery_container_id = fields.Many2one('records.container', string='Discovery Container', tracking=True)
    search_attempt_ids = fields.One2many('document.search.attempt', 'retrieval_item_id', string="Search Attempts")

    status = fields.Selection([
        ('pending', 'Pending'),
        ('searching', 'Searching'),
        ('located', 'Located'),
        ('retrieved', 'Retrieved'),
        ('packaged', 'Packaged'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('not_found', 'Not Found')
    ], string='Status', default='pending', tracking=True)

    # File search methods
    def action_start_file_search(self):
        self.ensure_one()
        if self.status != 'pending':
            raise UserError(_("You can only begin a search for items in the 'Pending' state."))
        self.write({'status': 'searching'})
        self.message_post(body=_("File search has been initiated."))

    def action_log_container_search(self, container, found=False, notes=""):
        """
        Records an attempt to search a specific container for the file.
        This method is intended to be called by other processes or wizards.
        """
        self.ensure_one()
        if self.status != 'searching':
            raise UserError(_("You can only record search attempts for items in the 'Searching' state."))

        # Create a search attempt log for audit purposes
        self.env['document.search.attempt'].create({
            'retrieval_item_id': self.id,
            'container_id': container.id,
            'found': found,
            'search_notes': notes,
            'requested_file_name': self.requested_file_name,
        })

        # Add the container to the list of those already searched
        self.write({'searched_container_ids': [(4, container.id)]})

        if found:
            self.write({
                'status': 'located',
                'discovery_container_id': container.id,
            })
            self.message_post(body=_("File located in container %s", container.name))
        else:
            self.message_post(body=_("Container %s searched. File not found", container.name))
