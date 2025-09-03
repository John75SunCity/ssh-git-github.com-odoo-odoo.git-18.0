from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FileRetrieval(models.Model):
    _name = 'file.retrieval'
    _description = 'File Retrieval Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'
    _rec_name = 'display_name'

    # Core identification
    name = fields.Char(string='File Reference', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Assigned User', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)

    # File-specific fields
    document_id = fields.Many2one('records.document', string='Document')
    requested_file_name = fields.Char(string='Requested File Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    container_id = fields.Many2one('records.container', string='Container')
    barcode = fields.Char(string='Barcode/ID')

    # Search and discovery
    searched_container_ids = fields.Many2many(
        'records.container',
        relation='file_retrieval_container_rel',
        column1='file_retrieval_id',
        column2='container_id',
        string='Searched Containers'
    )
    search_attempt_ids = fields.One2many('document.search.attempt', 'file_retrieval_id', string='Search Attempts')
    file_discovered = fields.Boolean(string='File Discovered')
    discovery_date = fields.Datetime(string='Discovery Date')
    discovery_container_id = fields.Many2one('records.container', string='Discovery Container')

    # Status workflow
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

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1')

    # Not found handling
    not_found_reason = fields.Selection([
        ('not_in_container', 'Not in Container'),
        ('container_missing', 'Container Missing'),
        ('destroyed', 'Already Destroyed'),
        ('misfiled', 'Misfiled'),
        ('other', 'Other Reason')
    ], string='Not Found Reason')
    not_found_notes = fields.Text(string='Not Found Notes')

    # Quality and condition
    condition_before = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    ], string='Condition Before')
    condition_after = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    ], string='Condition After')

    # Computed fields
    containers_accessed_count = fields.Integer(string='Containers Accessed', compute='_compute_containers_accessed_count')
    total_search_attempts = fields.Integer(string='Total Search Attempts', compute='_compute_total_search_attempts')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    @api.depends('searched_container_ids')
    def _compute_containers_accessed_count(self):
        for record in self:
            record.containers_accessed_count = len(record.searched_container_ids)

    @api.depends('search_attempt_ids')
    def _compute_total_search_attempts(self):
        for record in self:
            record.total_search_attempts = len(record.search_attempt_ids)

    @api.depends('name', 'requested_file_name')
    def _compute_display_name(self):
        for record in self:
            if record.requested_file_name:
                record.display_name = f"{record.name} - {record.requested_file_name}"
            else:
                record.display_name = record.name or "New File Retrieval"

    def action_start_search(self):
        """Start the file search process"""
        self.ensure_one()
        if self.status != 'pending':
            raise UserError(_("Only pending files can start search process."))
        self.write({'status': 'searching'})
        self.message_post(body=_("Search started for file: %s", self.requested_file_name))
        return True

    def action_record_search(self, container_id, found=False, notes=""):
        """Record a search attempt in a container"""
        self.ensure_one()
        if container_id not in self.searched_container_ids.ids:
            self.searched_container_ids = [(4, container_id)]

        self.env['document.search.attempt'].create({
            'file_retrieval_id': self.id,
            'container_id': container_id,
            'searched_by_id': self.env.user.id,
            'search_date': fields.Datetime.now(),
            'found': found,
            'search_notes': notes,
            'requested_file_name': self.requested_file_name,
        })

        if found:
            self.write({
                'status': 'located',
                'file_discovered': True,
                'discovery_date': fields.Datetime.now(),
                'discovery_container_id': container_id,
                'container_id': container_id,
            })
